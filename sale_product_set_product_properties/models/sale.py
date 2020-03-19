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

    @api.multi
    def set_all_print_properties(self):
        super(SaleOrder, self).set_all_print_properties()
        print_ids = False
        for record in self:
            for r in record.mapped('product_set_id'):
                print_ids = r.product_properties_ids
            if print_ids:
                record.print_properties = [(0, False, {'name': x.name.id, 'order_id': self.id, 'print': True, 'sequence': x.sequence}) for x in print_ids]
