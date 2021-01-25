# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, models, fields, _
from odoo.http import request
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
            amount_untaxed = set.amount_untaxed
            set_old = self.sets_line.search([('order_id', '=', self.id), ('product_set_id', '=', set.id)])
            if set_old:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write(self.prepare_sale_order_set_data(self.id, set, quantity+sum(ss.quantity for ss in set_old), sum(ss.amount_total for ss in set_old)+self.pricelist_id.currency_id.round(amount_untaxed)))
                res_id = set_old.id
            else:
                res = SetLinesSets.create(self.prepare_sale_order_set_data(self.id, set, quantity, self.pricelist_id.currency_id.round(amount_untaxed)))
                res_id = res.id
            for set_line in set.set_lines:
                line = self.sudo().order_line.search([('order_id', '=', self.id), ('product_id', '=', set_line.product_id.id), ('product_set_id', '=', set.id)], limit=1)
                if line:
                    line.write(self.prepare_sale_order_line_set_data(self.id, set, set_line, quantity, set_old.id, max_sequence=max_sequence, old_qty=line.product_uom_qty, old_pset_qty=line.pset_quantity))
                else:
                    line = SaleOrderLineSudo.create(self.prepare_sale_order_line_set_data(self.id, set, set_line, quantity, set_old.id, max_sequence=max_sequence))
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                amount_untaxed += line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)['total_excluded']
            set_old.write({'price_unit': amount_untaxed/self.quantity,
                           'amount_total': amount_untaxed})
        return {"set_line_id": res_id, "quantity": quantity}
