#  Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.addons.microsoft_calendar.models.microsoft_sync import after_commit

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'product.set.mixin']

    product_set_section_id = fields.Many2one('sale.order.line', string='Sale Product Set Section')

    def _get_values_product_set_mixin(self, total_quantity):
        return self._get_update_product_set_section_values(total_quantity)

    @api.model_create_multi
    def create(self, vals_list):
        if not self._context.get('create_new_set'):
            inx = None

            for sequence_inx, vals in enumerate(vals_list):
                order_id = self.env['sale.order'].search([('id', '=', vals['order_id'])], limit=1)
                if order_id.order_line:
                    last_section_id = order_id.order_line[-1]
                    sequence = last_section_id.sequence
                    vals.update({'sequence': sequence + 2 + sequence_inx})
                    product_set_id = last_section_id.product_set_id
                    if product_set_id:
                        set_line_ids = product_set_id.set_line_ids
                        if vals.get('product_id') in set_line_ids.mapped('product_id').ids:
                            product_set_line_id = set_line_ids. \
                                filtered(lambda p: p.product_id.id == vals.get('product_id'))
                            if len(product_set_line_id) > 1:
                                product_set_line_id = product_set_line_id[0]
                            vals.update({
                                'product_set_id': product_set_id.id,
                                'product_set_line_id': len(product_set_line_id) > 1 and product_set_line_id[0].id or product_set_line_id.id,
                                'product_set_section_id': last_section_id.id,
                            })
                        elif vals.get('product_id') and inx is None:
                            inx = sequence_inx
            # _logger.info(f"vals_list: {vals_list}")
        return super().create(vals_list)

    def write(self, values):
        if not self._context.get('create_new_set') and values.get('product_set_id'):
            for record in self:
                order_id = record.order_id
                sequences = {}
                line_section = {}
                sequence_inx_insert = 0
                for sequence_inx, line in enumerate(order_id.order_line.\
                                                        sorted(lambda r: f"{r.product_set_id or 0}-{r.sequence}", reverse=True)):
                    product_set_id = line.product_set_id
                    sequences.update({line: sequence_inx + sequence_inx_insert})
                    if line.product_set_id and not line.product_set_line_id:
                        set_line_ids = product_set_id.set_line_ids
                        if line.product_id.id in set_line_ids.mapped('product_id').ids:
                            product_set_line_id = set_line_ids. \
                                filtered(lambda p: p.product_id.id == line.product_id.id)
                            if len(product_set_line_id) > 1:
                                product_set_line_id = product_set_line_id[0]
                            line.with_context(**dict(self._context, create_new_set=True)).write({
                                'product_set_line_id': product_set_line_id.id
                            })
                    if product_set_id and line.product_set_id != product_set_id:
                        sequence_inx_insert += 1
                        line_section.update({line: sequence_inx + sequence_inx_insert})
                for line, sequence_inx in sequences.items():
                    line.with_context(**dict(self._context, create_new_set=True)).write({
                        'sequence': sequence_inx
                    })
                for line, sequence_inx in line_section.items():
                    self.env['sale.order.line'].create({
                    'display_type': 'line_section',
                    'name': _('Uncategorized'),
                    'order_id': order_id.id,
                    'sequence': sequence_inx,
                })
        return super().write(values)

    def unlink(self):
        for record in self:
            if self._context.get('create_new_set') or not record.display_type == 'line_section':
                continue
            product_set_section_id = record
            for order_id in record.mapped('order_id'):
                order_lines = order_id.order_line. \
                               filtered(lambda r: r.product_set_section_id.id == product_set_section_id.id)
                for line in order_lines:
                    line.unlink()
        return super().unlink()
