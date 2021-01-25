# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons import decimal_precision as dp

from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    @api.one
    def _count_items(self):
        self.count_items = len(self.item_ids.ids)

    count_items = fields.Integer(compute=_count_items, string="Items")

    def filter(self, product, qty, partner, rule):
        res = super(Pricelist, self).filter(product, qty, partner, rule)
        if rule.product_set_id:
            return rule.product_set_id.id != self._context.get("product_set_id", False)
        if res != None:
            return res
        return None

    def check_pricelist(self):
        for pricelist in self.item_ids:
            if pricelist.applied_on == "3_global":
                pricelist.sequence = 4000
            if pricelist.applied_on == "2_product_category":
                pricelist.sequence = 3000
            if pricelist.applied_on == "0_product_variant":
                pricelist.sequence = 1000
            if pricelist.product_set_id:
                pricelist.sequence = 0

            if pricelist.categ_id and pricelist.applied_on != "2_product_category":
                pricelist.applied_on = '2_product_category'
                pricelist.product_id = False
                pricelist.product_tmpl_id = False
            if pricelist.product_tmpl_id and pricelist.applied_on != '1_product':
                pricelist.applied_on = '1_product'
                pricelist.categ_id = False
                pricelist.product_id = False
            if pricelist.product_id and pricelist.applied_on != '0_product_variant':
                pricelist.applied_on = '0_product_variant'
                pricelist.categ_id = False
                pricelist.product_tmpl_id = False


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_set_id = fields.Many2one('product.set', string='Product Set')

