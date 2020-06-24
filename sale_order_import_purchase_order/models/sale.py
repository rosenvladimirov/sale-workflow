# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def prepare_sale_order_line_data(self, so, import_po):
        order_line = []
        for line in import_po.order_line:
            sale_order_line = self.env['sale.order.line'].new({
                'order_id': so.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_qty,
                'purchase_price_unit': line.price_unit,
                'purchase_currency_id': line.order_id.currency_id.id,
            })
            order_line.append((0, 0, sale_order_line._convert_to_write(sale_order_line._cache)))
        return order_line


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_price_unit = fields.Monetary("Purchase unit price", )
    purchase_currency_id = fields.Many2one(related='order_id.pricelist_id.currency_id', store=True, string='Purchase Currency', readonly=True)
