# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

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
            for line in record.invoice_line_ids:
                for order_line in line.sale_line_ids:
                    record.stock_int_picking_ids |= order_line.stock_int_picking_ids


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

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
            for order_line in record.sale_line_ids:
                record.stock_int_picking_ids |= order_line.stock_int_picking_ids
