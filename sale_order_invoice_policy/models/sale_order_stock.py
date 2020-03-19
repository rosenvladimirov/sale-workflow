# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('order_id.state')
    def _compute_invoice_status(self):
        super(SaleOrderLine, self)._compute_invoice_status()
        for line in self:
            # We handle the following specific situation: a physical product is partially delivered,
            # but we would like to set its invoice status to 'Fully Invoiced'. The use case is for
            # products sold by weight, where the delivered quantity rarely matches exactly the
            # quantity ordered.
            if line.order_id.state == 'done'\
                    and line.invoice_status == 'no'\
                    and line.product_id.type in ['consu', 'product']\
                    and line.product_id.invoice_policy == 'delivery'\
                    and line.move_ids \
                    and all(move.state in ['done', 'cancel'] for move in line.move_ids):
                line.invoice_status = 'invoiced'
