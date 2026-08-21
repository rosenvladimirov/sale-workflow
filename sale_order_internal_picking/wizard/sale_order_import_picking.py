# Copyright 2026 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleOrderPickingInternalImport(models.TransientModel):
    _name = "sale.order.picking.internal.import"
    _description = "Put picking in sale order"
    _inherit = ["barcodes.barcode_events_mixin"]
    _rec_name = "import_picking_id"

    import_picking_name = fields.Char(string="From picking")
    stock_int_picking_id = fields.Many2one("stock.picking", string="Choice Picking")
    partner_id = fields.Many2one("res.partner", string="Customer")
    partner_shipping_id = fields.Many2one("res.partner", string="Delivery Address")
    import_picking_id = fields.Many2one("stock.picking", string="From picking", ondelete="restrict")
    # 🚨 `stock.quant.package` НЕ съществува в 19.0 — моделът е преименуван на
    # `stock.package` (ядро, stock/models/stock_package.py:18), а до него са
    # добавени `stock.package.type` и `stock.package.history`. Липсващият
    # комодел не е тиха грешка: ORM-ът гърми при СГЛОБЯВАНЕ на регистъра с
    # `AssertionError: unknown comodel_name`, тоест модулът не се инсталира.
    # 🚩 Самото поле е мъртво — стои `invisible="1"` в изгледа и не се чете
    # никъде в Python-а. Пренесено е както си беше, за да не се променя обхватът.
    package_id = fields.Many2one(
        "stock.package", string="Package", help="The package containing this quant")

    def on_barcode_scanned(self, barcode):
        self.import_picking_name = barcode

    def import_picking(self):
        """Пренася движенията на избрания пикинг като редове на поръчката."""
        for record in self:
            so_id = self.env.context.get("active_id")
            if not so_id:
                continue
            if record.stock_int_picking_id:
                import_picking = record.stock_int_picking_id
            elif record.import_picking_name:
                import_picking = self.env["stock.picking"].search(
                    [("name", "=", record.import_picking_name)])
            else:
                continue
            if not import_picking:
                continue
            sale_order = self.env["sale.order"].browse(so_id)
            if not sale_order.exists():
                continue
            order, order_line = sale_order.prepare_sale_order_line_picking_data(import_picking)
            if order:
                sale_order.write(order)
            if order_line:
                sale_order.write({"order_line": order_line})
            _logger.info(
                "sale_order_internal_picking: %s ← %d реда от %s",
                sale_order.name, len(order_line), import_picking.mapped("name"))
        return {"type": "ir.actions.act_window_close"}
