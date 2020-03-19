# Copyright 2019 dxFactory - Rosen Vladimirov
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SaleOrderLinePriceWarn(models.TransientModel):
    _name = "sale.order.line.price.warn"
    _description = "Sale order line price history Warning"

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        compute_sudo=True,
        readonly=True,
        help="Pricelist for current sales order."
    )
    item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        string='Pricelist Items',
        compute_sudo=True,
        readonly=True,
    )
    price_unit = fields.Float(
        related="sale_order_line_id.price_unit",
        readonly=True,
    )
