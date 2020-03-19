# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    ref_description = fields.Text(string='Ref Description')

    @api.onchange('ref_description')
    def on_change_ref_description(self):
        if self.ref_description:
            self.move_id.ref_description = self.ref_description


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('ref_description', False):
            result['ref_description'] = values['ref_description']
        return result
