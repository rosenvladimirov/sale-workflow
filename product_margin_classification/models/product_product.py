# -*- coding: utf-8 -*-
# Copyright (C) 2018-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    margin_classification_id = fields.Many2one(
        comodel_name='product.margin.classification',
        string='Margin Classification')

    @api.multi
    def get_margin_classification(self):
        for category in self:
            while category.parent_id:
                if category.margin_classification_id:
                    return category.margin_classification_id
                category = category.parent_id
            if category.margin_classification_id:
                return category.margin_classification_id
        return False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Define a variant function to allow inherited modules to call
    # use_theoritical_price for product variants
    @api.multi
    def use_theoretical_price_variant(self):
        self.mapped('product_tmpl_id').use_theoretical_price()
