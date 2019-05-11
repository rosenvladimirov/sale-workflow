# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['product_set_id'] = self.sale_line_id.product_set_id.id
        return vals

