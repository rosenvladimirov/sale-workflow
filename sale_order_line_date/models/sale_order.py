# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        if not vals.get("requested_date_ids") and vals["date_order"]:
            for line in vals["order_line"]:
                line.update({'requested_date_ids': [(0, False, {"requested_date": vals["date_order"],
                                                      "note": _("Automatic create date"),
                                                      })]})
        return super(SaleOrder, self).create(vals)
