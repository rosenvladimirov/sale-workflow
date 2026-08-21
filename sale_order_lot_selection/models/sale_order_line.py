from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one(
        "stock.lot",
        "Lot",
        copy=False,
        compute="_compute_lot_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    def _prepare_procurement_values(self):
        # 🚨 19.0 махна `group_id` от подписа
        # (sale_stock/models/sale_order_line.py:278) — `procurement.group` вече
        # не се подава оттук. Старият override щеше да гръмне с TypeError при
        # ПОТВЪРЖДАВАНЕ на поръчка, не при инсталация.
        vals = super()._prepare_procurement_values()
        if self.lot_id:
            vals["restrict_lot_id"] = self.lot_id.id
        return vals

    @api.depends("product_id")
    def _compute_lot_id(self):
        for sol in self:
            if sol.product_id != sol.lot_id.product_id:
                sol.lot_id = False
