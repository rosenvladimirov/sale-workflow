# Copyright 2026 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_int_picking_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_stock_int_picking_ids",
        string="Internal Transfers ref.",
    )

    @api.depends("invoice_line_ids.sale_line_ids.stock_int_picking_ids")
    def _compute_stock_int_picking_ids(self):
        # 🚨 Същият заварен дефект като на поръчката: полето не се присвояваше
        # преди `|=`, а тук е още по-често — фактура без нито един ред със
        # свързана поръчка изобщо не влиза в цикъла.
        for record in self:
            pickings = record.invoice_line_ids.sale_line_ids.stock_int_picking_ids
            record.stock_int_picking_ids = [Command.set(pickings.ids)]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    stock_int_picking_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_stock_int_picking_ids",
        string="Internal Transfers ref.",
    )

    @api.depends("sale_line_ids.stock_int_picking_ids")
    def _compute_stock_int_picking_ids(self):
        # 🚨 Тук е коренът на падането в продукция: ВСЕКИ ред от статия —
        # данъчният, контрапартидният, всеки ред на покупна фактура — има празен
        # `sale_line_ids`, значи цикълът не се изпълнява и полето остава
        # неприсвоено. Затова четенето на всички полета на `account.move.line`
        # гърмеше с „Compute method failed to assign".
        for record in self:
            record.stock_int_picking_ids = [
                Command.set(record.sale_line_ids.stock_int_picking_ids.ids)]
