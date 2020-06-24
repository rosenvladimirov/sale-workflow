# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    ref_description = fields.Text(string='Ref Description')

    @api.onchange('ref_description')
    def on_change_ref_description(self):
        if self.ref_description:
            self.move_id.ref_description = self.ref_description
