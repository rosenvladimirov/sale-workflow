# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')
    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)
    future_loyalty_points = fields.Integer(string='Potential Loyalty Points', compute='_loyalty_points', store=True)
    loyalty_id = fields.Many2one(comodel_name='account.loyalty', string='Loyalty')

    @api.one
    @api.depends('order_line', 'order_line.product_id', 'order_line.product_uom_qty', 'order_line.price_subtotal')
    def _loyalty_points(self):
        self.loyalty_points = sum([l.loyalty_points for l in self.order_line])
        self.future_loyalty_points = sum([l.future_loyalty_points for l in self.order_line])

    @api.onchange('loyalty_program_id')
    def _compute_loyalty_program_id(self):
        self.loyalty_points = 0
        self.future_loyalty_points = 0
        self.order_line.write({'loyalty_points': 0, 'future_loyalty_points': 0})

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.loyalty_program_id:
            self.loyalty_program_id = self.partner_id.loyalty_program_id
        return super(SaleOrder, self).onchange_partner_id()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    loyalty_points = fields.Integer(string='Loyalty Points', compute='_loyalty_points', store=True)
    future_loyalty_points = fields.Integer(string='Potential Loyalty Points', compute='_loyalty_points', store=True)

    @api.model
    def _calculate_loyalty_points(self, product, qty, price, **kwargs):
        return self.order_id.loyalty_program_id.calculate_loyalty_points(product, qty, price, **kwargs)

    @api.one
    @api.depends('product_id', 'product_uom_qty', 'price_subtotal', 'order_id.loyalty_program_id', 'loyalty_points', 'future_loyalty_points')
    def _loyalty_points(self):
        if self.order_id.loyalty_program_id:
            if self.qty_invoiced > 0.0:
                self.loyalty_points = self._calculate_loyalty_points(self.product_id, self.qty_invoiced, self.price_subtotal)
            else:
                self.loyalty_points = 0
            if self.product_uom_qty > 0.0:
                self.future_loyalty_points = self._calculate_loyalty_points(self.product_id, self.product_uom_qty, self.price_subtotal)
            else:
                self.future_loyalty_points = 0
        _logger.info("Loyalty %s:%s" % (self.loyalty_points, self.future_loyalty_points))

