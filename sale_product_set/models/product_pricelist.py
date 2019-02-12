# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons import decimal_precision as dp

from odoo.tools import pycompat

class Pricelist(models.Model):
    _inherit = "product.pricelist"


    def _filter(self, product, qty, partner, rule):
        res = super(Pricelist, self)._filter(product, qty, partner, rule)
        return res and (rule.product_set_id.id in [set.id for set in x.product_set_id for x in product])

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_set_id = fields.Many2one('product.set', string='Product Set')

