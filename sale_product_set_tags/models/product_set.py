# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductSet(models.Model):
    _inherit = 'product.set'

    tag_ids = fields.Many2many(
        comodel_name='product.template.tag', string="Product Set Tags",
        relation='product_set_product_tag_rel',
        column1='product_set_id', column2='tag_id')
