# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class SaleOrderLineDate(models.Model):
    _name = "sale.order.line.dates"
    _description = "Requested dates plan"
    _order = "requested_date"

    requested_date = fields.Date(required=True)
    date_confirmed = fields.Date(string='Confirmed Date', required=True, index=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    note = fields.Text("Note", translate=True)
    name = fields.Char('Customer reference')

    @api.depends('requested_date', 'name')
    def name_get(self):
        res = []
        for ref in self:
            res.append((ref.id, "%s/%s" % (ref.requested_date, ref.name or ref.product_uom_qty)))
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    requested_date_ids = fields.Many2many("sale.order.line.dates", string="Requested dates plan")

