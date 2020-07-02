# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    product_set_code = fields.Char(string='Product Set code', related="product_set_id.code")
    mv_product_set_id = fields.Many2one('product.set', string='Default Product Set', related="move_id.product_set_id")

    @api.multi
    @api.onchange('product_set_id')
    def product_set_id_change(self):
        self.ensure_one()
        vals = {}
        if self.product_set_id and self.product_set_id != self.mv_product_set_id:
            self.mv_product_set_id = self.product_set_id

