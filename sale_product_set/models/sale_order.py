#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.tools import groupby

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_set_ids = fields.Many2many('sale.product.set',
                                       compute="_compute_product_set_ids",
                                       string="Product sets",
                                       store=True)

    @api.depends('order_line')
    def _compute_product_set_ids(self):
        compensation_product_id = self.with_company(self.env.company). \
            env.ref('product_set.compensation_product', raise_if_not_found=False).id
        for record in self:
            record.product_set_ids = False
            product_set_ids = {}
            if not record.id:
                continue

            order_lines = record.order_line.filtered(lambda r: r.product_set_id)
            # for ln in order_lines:
            #     _logger.info(f"record: {ln.read(['display_type'])[0]}:{record.exists()}")

            for product_set_section_id, lines in groupby(order_lines.sorted(lambda r: r.product_set_section_id.id),
                                                         key=lambda r: r.product_set_section_id):
                if not product_set_section_id:
                    continue
                product_set_id = product_set_section_id.product_set_id
                quantity = sum([sl.quantity for sl in product_set_id.set_line_ids.
                               filtered(lambda r: r.product_id.id == compensation_product_id)]) or 1.0

                total_quantity = {
                    'amount': 0.0,
                    'quantity': quantity,
                    'section_quantity': 0.0,
                }
                for order_line_id in lines:
                    if order_line_id.qty_delivered != 0.0 and order_line_id.invoice_status == 'invoiced':
                        total_quantity['amount'] += order_line_id.untaxed_amount_invoiced
                    else:
                        total_quantity['amount'] += order_line_id.price_subtotal
                    if order_line_id.product_id.id == compensation_product_id:
                        if order_line_id.qty_delivered != 0.0 and order_line_id.invoice_status == 'invoiced':
                            total_quantity['section_quantity'] += order_line_id.qty_delivered
                        else:
                            total_quantity['section_quantity'] += order_line_id.product_uom_qty
                product_set_section_id.write(product_set_section_id._get_values_product_set_mixin(total_quantity))

                if not product_set_ids.get(product_set_id):
                    product_set_ids[product_set_id] = {
                        'amount': 0.0,
                        'quantity': quantity,
                        'section_quantity': 0.0,
                    }
                product_set_ids[product_set_id].update({
                    'amount': product_set_ids[product_set_id]['amount'] + total_quantity['amount'],
                    'section_quantity': product_set_ids[product_set_id]['section_quantity'] + total_quantity['section_quantity'],
                })

            for product_set_id, total_quantity in product_set_ids.items():
                product_set_ids = self.env['sale.product.set'].search([
                    ('order_id', '=', record.id),
                    ('product_set_id', '=', product_set_id.id)])
                if product_set_ids:
                    record.product_set_ids |= product_set_ids
                    product_set_ids.with_context(**dict(self._context, create_new_set=True)).write(
                        record.product_set_ids._get_sale_product_set_value(
                            record,
                            product_set_id,
                            total_quantity['amount'],
                            total_quantity['section_quantity'] / total_quantity['quantity'],
                        )
                    )
                else:
                    record.product_set_ids |= self.env['sale.product.set'].\
                        with_context(**dict(self._context, create_new_set=True)).create(
                        record.product_set_ids._get_sale_product_set_value(
                            record,
                            product_set_id,
                            total_quantity['amount'],
                            total_quantity['section_quantity'] / total_quantity['quantity'],
                        )
                    )

    def action_set_sections(self):
        compensation_product_id = self.with_company(self.env.company). \
            env.ref('product_set.compensation_product', raise_if_not_found=False).id
        for record in self:
            record.order_line.filtered(lambda r: r.display_type == 'line_section').with_context(**dict(self._context, create_new_set=True)).unlink()
            self.env['sale.product.set'].search([('order_id', '=', record.id)]).with_context(**dict(self._context, create_new_set=True)).unlink()
            values = {}
            total_quantity = {}
            add_sequence = add_no_set_sequence = sequence = 0
            no_set_sequence = 999

            lines = record.order_line.sorted(lambda r: r.product_set_id and r.product_set_id.id or 0)
            product_set_id = False
            for line in lines.\
                with_context(**dict(self._context, lang=record.partner_id.lang)).filtered(lambda r: r.product_set_id):
                sequence += 1
                if not total_quantity.get(line.product_set_id):
                    total_quantity[line.product_set_id] = {
                        'amount': 0.0,
                        'quantity': 1.0,
                        'section_quantity': 0.0,
                    }

                if line.product_set_id != product_set_id:
                    product_set_id = line.product_set_id
                    if product_set_id:
                        values[f'section_{line.id}'] = product_set_id.\
                            prepare_sale_order_values(sequence + add_sequence, order_id=record)
                    else:
                        values[f'section_{line.id}'] = {
                            'display_type': 'line_section',
                            'product_set_id': line.product_set_id.id,
                            'name': line.product_set_id.display_name or _('Uncategorized'),
                            'order_id': record.id,
                            'sequence': sequence + add_sequence,
                        }

                    quantity = sum([sl.quantity for sl in line.product_set_id.set_line_ids.
                                   filtered(lambda r: r.product_id.id == compensation_product_id)]) or 1.0
                    total_quantity[line.product_set_id].update({
                        'quantity': quantity,
                    })
                    add_sequence += 1

                values[f'line_{line.id}'] = {
                    'sequence': sequence + add_sequence,
                }
                if line.product_id.id == compensation_product_id:
                    total_quantity[line.product_set_id]['section_quantity'] += line.product_uom_qty
                if line.product_id.id != compensation_product_id:
                    total_quantity[line.product_set_id]['amount'] += line.price_subtotal

            for line in lines.filtered(lambda r: not r.product_set_id):
                no_set_sequence += 1
                if line.product_set_id != product_set_id:
                    product_set_id = line.product_set_id
                    values[f'section_{line.id}'] = {
                        'display_type': 'line_section',
                        'name': _('Uncategorized'),
                        'order_id': record.id,
                        'sequence': no_set_sequence + add_no_set_sequence
                    }
                    add_no_set_sequence += 1
                values[f'line_{line.id}'] = {
                    'sequence': no_set_sequence + add_no_set_sequence,
                }
            # _logger.info(f"values: {values}\ntotal_quantity: {total_quantity}")
            for line in record.order_line:
                if values.get(f'section_{line.id}') and not values.get(line.product_set_id):
                    if not values.get(line.product_set_id):
                        values[line.product_set_id] = {}
                    if total_quantity.get(line.product_set_id):
                        values[f'section_{line.id}'].update(line._get_values_product_set_mixin(total_quantity[line.product_set_id]))
                    values[line.product_set_id] = {
                        'product_set_section_id': record.\
                            with_context(**dict(self._context, create_new_set=True)).order_line.create(values[f'section_{line.id}']).id
                    }

            for line in record.order_line:
                if values.get(f'line_{line.id}'):
                    # _logger.info(f"values: {f'line_{line.id}'} {values[line.product_set_id]['product_set_section_id']}")
                    if line.product_set_id:
                        values[f'line_{line.id}'].update({'product_set_section_id': values[line.product_set_id]['product_set_section_id']})
                    # _logger.info(f"values: {values[f'line_{line.id}']}")
                    line.with_context(**dict(self._context, create_new_set=True)).write(values[f'line_{line.id}'])

    def unlink(self):
        for record in self:
            self.env['sale.product.set'].search([('order_id', '=', record.id)]).with_context(**dict(self._context, create_new_set=True)).unlink()
        return super().unlink()
