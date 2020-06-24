# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    product_set_code = fields.Char(string='Product Set code', related="product_set_id.code")

    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)
        for rec in self:
            if not rec.product_set_id and rec.move_id.product_set_id:
                rec.product_set_id = rec.move_id.product_set_id
        return res