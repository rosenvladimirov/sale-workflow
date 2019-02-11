# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSetAdd(models.TransientModel):
    _name = 'product.set.add'
    _rec_name = 'product_set_id'
    _description = "Wizard model to add product set into a quotation"

    product_set_id = fields.Many2one('product.set', 'Product set', required=True, domain="[('state', '=', 'progress'), ('active', '=', True)]")
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('product.set').partner_id)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    amount_total = fields.Monetary(string='Total', related="product_set_id.amount_total", store=True)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    @api.multi
    def sale_add_set(self):
        """ Add product set, multiplied by quantity in sale order line """
        so_id = self._context['active_id']
        if not so_id:
            return
        order_obj = self.env['sale.order']
        so = order_obj.browse(so_id)
        max_sequence = 0
        if so.order_line:
            max_sequence = max([line.sequence for line in so.order_line])
        sale_order_line = self.env['sale.order.line']
        set_lines = self.env['sale.order.sets']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = sale_order_line.create(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity, max_sequence=max_sequence))
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                amount_untaxed += line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)['total_excluded']
            set_old = set_lines.search([('order_id', '=', so_id), ('product_set_id', '=', set.id)])
            if set_old:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write({
                        'order_id': so_id,
                        'product_set_id': set.id,
                        'quantity': self.quantity+set_old.quantity,
                        'amount_total': set_old.amount_total+self.pricelist_id.currency_id.round(amount_untaxed),
                        })
            else:
                set_lines.create(order_obj.prepare_sale_order_set_data(so_id, set, self.quantity, self.pricelist_id.currency_id.round(amount_untaxed)))

    @api.multi
    def purchase_add_set(self):
        """ Add product set, multiplied by quantity in purchase order line """
        po_id = self._context['active_id']
        if not po_id:
            return
        order_obj = self.env['purchase.order']
        po = order_obj.browse(po_id)
        max_sequence = 0
        if po.order_line:
            max_sequence = max([line.sequence for line in po.order_line])
        purchase_order_line = self.env['purchase.order.line']
        set_lines = self.env['purchase.order.sets']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = purchase_order_line.create(order_obj.prepare_purchase_order_line_set_data(po_id, set, set_line, self.quantity, max_sequence=max_sequence))
                price = line.price_unit
                amount_untaxed += line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)['total_excluded']
            set_old = set_lines.search([('order_id', '=', po_id), ('product_set_id', '=', set.id)])
            if set_old:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write({
                        'order_id': po_id,
                        'product_set_id': set.id,
                        'quantity': self.quantity+set_old.quantity,
                        'amount_total': set_old.amount_total+self.pricelist_id.currency_id.round(amount_untaxed),
                        })
            else:
                set_lines.create(order_obj.prepare_purchase_order_set_data(po_id, set, self.quantity, self.pricelist_id.currency_id.round(amount_untaxed)))
