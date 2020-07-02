# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_set_ids = fields.One2many('product.set', compute="_compute_product_set_ids", string='Picking Sets Lines')
    product_set_id = fields.Many2one('product.set', string='Default Product Set', compute="_compute_product_set_id", store=True)

    @api.multi
    def _compute_product_set_ids(self):
        for record in self:
            if record.sale_line_id:
                lines = record.sale_line_id
            else:
                lines = record.move_line_ids
            record.product_set_ids = False
            sets = False
            for line in lines:
                if not sets:
                    sets = line.product_set_id
                else:
                    sets |= line.product_set_id
            if sets:
                record.product_set_ids = sets

    @api.multi
    def _compute_product_set_id(self):
        for record in self:
            if len(record.product_set_ids.ids) > 0:
                record.product_set_id = record.product_set_ids[-1]

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['product_set_id'] = self.sale_line_id.product_set_id.id
        return vals

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        for record in self:
            if record.product_set_id:
                vals['product_set_id'] = record.product_set_id.id
        return vals
