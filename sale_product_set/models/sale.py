# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sets_line = fields.One2many('sale.order.sets', 'order_id', string='Order Sets Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Group by sets")

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len(record.sets_line) > 0

    @api.multi
    def order_lines_sets_layouted(self):
        self.ensure_one()
        if self.has_sets:
            report_pages_sets = [[]]
            for category, lines in groupby(self.order_line, lambda l: l.product_set_id):
                # If last added category induced a pagebreak, this one will be on a new page
                if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    report_pages_sets.append([])
                qty = sum(x.quantity for x in self.sets_line if x.product_set_id.id == category.id)
                unit_price = qty > 0.0 and category.subtotal/qty or category.subtotal
                # Append category to current report page
                report_pages_sets[-1].append({
                    'name': category and category.display_name or _('Uncategorized'),
                    'quantity': qty,
                    'price_unit': unit_price,
                    'subtotal': category and category.subtotal,
                    'pagebreak': category and category.pagebreak,
                    'lines': self.print_sets and list(lines) or []
                })
            return report_pages_sets
        else:
            report_pages_sets = [[]]
            for category, lines in groupby(self.order_line, lambda l: l.layout_category_id and not l.product_set_id):
                # If last added category induced a pagebreak, this one will be on a new page
                if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    report_pages_sets.append([])
                qty = sum(x.product_uom_qty for x in self.order_line if (x.layout_category_id and x.layout_category_id.id or False) == category.id)
                subtotal = sum(x.price_subtotal for x in self.order_line if (x.layout_category_id and x.layout_category_id.id or False) == category.id)
                unit_price = category and qty > 0.0 and subtotal/qty or 0.0
                # Append category to current report page
                report_pages_sets[-1].append({
                    'name': category and category.name or _('Uncategorized'),
                    'quantity': qty,
                    'price_unit': unit_price,
                    'subtotal': category and category.subtotal,
                    'pagebreak': category and category.pagebreak,
                    'lines': list(lines)
                })
            return report_pages_sets

    @api.multi
    def _set_cart_update(self, product_set_id=None, add_qty=0, set_qty=0, attributes=None, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        SaleOrderLineSudo = self.env['sale.order.line'].sudo()
        SetLinesSets = self.env['sale.order.sets'].sudo()
        res_id = False
        #_logger.info("Show _____________ %s:%s" % (product_set_id, set_qty))
        try:
            if set_qty:
                quantity = float(set_qty)
        except ValueError:
            quantity = 1

        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status'))

        max_sequence = 0
        if self.order_line:
            max_sequence = max([line.sequence for line in self.order_line])

        for set in self.env['product.set'].browse(product_set_id):
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = SaleOrderLineSudo.create(self.prepare_sale_order_line_set_data(self.id, set, set_line, quantity, max_sequence=max_sequence))
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                amount_untaxed += line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)['total_excluded']
            set_old = self.sets_line.search([('order_id', '=', self.id), ('product_set_id', '=', set.id)])
            if set_old:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write({
                        'order_id': self.id,
                        'product_set_id': set.id,
                        'quantity': quantity+set_old.quantity,
                        'amount_total': set_old.amount_total+self.pricelist_id.currency_id.round(amount_untaxed),
                        })
                res_id = set_old.id
            else:
                res = SetLinesSets.create(self.prepare_sale_order_set_data(self.id, set, quantity, self.pricelist_id.currency_id.round(amount_untaxed)))
                res_id = res.id
        return {"set_line_id": res_id, "quantity": quantity}

    def prepare_sale_order_set_data(self, sale_order_id, set, qty, total):
        set_lines = self.env['sale.order.sets'].new({
            'order_id': sale_order_id,
            'product_set_id': set.id,
            'quantity': qty,
            'price_unit': total/qty,
            'amount_total': total,
        })
        line_sets_values = set_lines._convert_to_write(set_lines._cache)
        return line_sets_values

    def prepare_sale_order_line_set_data(self, sale_order_id, set, set_line, qty,
                                     max_sequence=0):
        sale_line = self.env['sale.order.line'].new({
            'order_id': sale_order_id,
            'product_id': set_line.product_id.id,
            'product_uom_qty': set_line.quantity * qty,
            'product_uom': set_line.product_id.uom_id.id,
            'sequence': max_sequence + set_line.sequence,
            'product_set_id': set.id,
        })
        sale_line.product_id_change()
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        invoice_vals.update({
            'print_sets': self.print_sets,
        })
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id, layout_category_id, product_set_id, sequence, id'


    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)

    @api.multi
    def write(self, values):
        if 'name' in values and self.product_set_id and _('set-code:') not in values['name']:
            values['name'] = _("%s (set-code: %s)" % (values['name'], self.product_set_id.code))
        return super(SaleOrderLine, self).write(values)


class SaleOrderSets(models.Model):
    _name = 'sale.order.sets'
    _description = 'Sales Order Sets'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', required=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Sets Qty'), required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    amount_total = fields.Monetary(string='Total')

    @api.multi
    def unlink(self):
        lines = self.order_id.order_line
        lines.filtered(lambda x: x.product_set_id.id == self.id).unlink()
        return super(SaleOrderSets, self).unlink()


    #@api.multi
    #@api.onchange('product_set_id')
    #def product_set_id_change(self):
