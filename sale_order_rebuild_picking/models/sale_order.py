# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_rebuld_qty(self):
        for record in self:
            for line in record.order_line:
                line._action_launch_procurement_rule()
