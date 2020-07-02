# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    int_picking_so_ids = fields.Many2many('sale.order.line', 'sale_order_line_int_picking_rel',
                                          'picking_line_id', 'so_line_id', string='Linked SO ref.')
    stock_int_picking_ids = fields.Many2many('stock.picking', compute="_compute_stock_int_picking_ids", string='Internal Transfers ref.')
    has_int_pick = fields.Boolean(compute="_compute_has_int_pick")

    @api.multi
    def _compute_has_int_pick(self):
        for record in self:
            record.has_int_pick = len(record.stock_int_picking_ids.ids) > 0

    @api.multi
    def _compute_stock_int_picking_ids(self):
        for record in self:
            record.customer_po_ids = False
            for line in record.move_lines:
                for order_line in line.sale_line_id:
                    record.stock_int_picking_ids |= order_line.stock_int_picking_ids
