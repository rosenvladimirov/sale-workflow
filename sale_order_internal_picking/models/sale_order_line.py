# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_int_picking_ids = fields.Many2many(
        'stock.picking',
        'sale_order_line_int_picking_rel',
        'so_line_id',
        'picking_line_id',
        string='Internal Transfers ref.'
    )
    order_partner_shipping_id = fields.Many2one(related='order_id.partner_shipping_id', store=True, string='Customer')
