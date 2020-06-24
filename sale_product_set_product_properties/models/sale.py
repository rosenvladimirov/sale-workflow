# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    products_set_properties = fields.Html('Products properties', compute="_get_products_set_properties")

    def _get_set_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        rcontext['doc'] = self
        result['html'] = self.env.ref(
            'sale_product_set_product_properties.report_saleorder_set_html').with_context(context).render(
                rcontext)
        return result

    @api.multi
    def _get_products_set_properties(self):
        for rec in self:
            if len(rec.order_line.ids) > 0:
                rec.products_set_properties = rec._get_set_html()['html']
