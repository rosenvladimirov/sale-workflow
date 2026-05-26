# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    stock_int_picking_ids = fields.Many2many(
        'stock.picking',
        compute="_compute_stock_int_picking_ids",
        string='Internal Transfers ref.'
    )

    def _compute_stock_int_picking_ids(self):
        for record in self:
            for order_line in record.sale_line_ids:
                record.stock_int_picking_ids |= order_line.stock_int_picking_ids
