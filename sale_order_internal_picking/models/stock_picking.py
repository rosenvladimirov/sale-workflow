# Copyright 2026 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    int_picking_so_ids = fields.Many2many(
        "sale.order.line",
        "sale_order_line_int_picking_rel",
        "picking_line_id",
        "so_line_id",
        string="Linked SO ref.",
    )
    stock_int_picking_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_stock_int_picking_ids",
        string="Internal Transfers ref.",
    )
    color = fields.Integer(compute="_compute_color")

    @api.depends("move_ids.sale_line_id")
    def _compute_stock_int_picking_ids(self):
        for record in self:
            pickings = record.move_ids.sale_line_id.stock_int_picking_ids
            record.stock_int_picking_ids = [Command.set(pickings.ids)]

    # Липсваше `@api.depends` — цветът не се преизчисляваше при промяна на
    # веригата от движения.
    @api.depends("move_ids.move_orig_ids")
    def _compute_color(self):
        for picking in self:
            picking.color = 1 if not picking.move_ids.move_orig_ids else 10
