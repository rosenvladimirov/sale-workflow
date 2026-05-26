# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import models, fields, api, _, Command

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    int_picking_so_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_int_picking_rel',
        'picking_line_id',
        'so_line_id',
        string='Linked SO ref.'
    )
    stock_int_picking_ids = fields.Many2many(
        'stock.picking',
        compute="_compute_stock_int_picking_ids",
        string='Internal Transfers ref.'
    )
    color = fields.Integer(compute="_compute_color")

    @api.depends('move_ids.sale_line_id')
    def _compute_stock_int_picking_ids(self):
        for record in self:
            stock_int_picking_ids = record.mapped('move_ids').mapped('sale_line_id').mapped('stock_int_picking_ids')
            record.stock_int_picking_ids = [Command.set(stock_int_picking_ids.ids)]

    def _compute_color(self):
        for picking in self:
            picking.color = len(picking.mapped('move_ids.move_orig_ids').ids) == 0 and 1 or 10
