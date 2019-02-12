# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from lxml import etree


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_loyalty_ids = fields.One2many(
        comodel_name='loyalty.rule',
        inverse_name='product_tmpl_id',
        string="Loyalty rule lines",
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_loyalty_ids = fields.One2many(
        comodel_name='loyalty.rule',
        inverse_name='product_id',
        string="Loyalty rule lines",
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Custom redefinition of fields_view_get to adapt the context
            to product variants.
        """
        res = super().fields_view_get(view_id=view_id,
                                      view_type=view_type,
                                      toolbar=toolbar,
                                      submenu=submenu)
        if view_type == 'form':
            product_xml = etree.XML(res['arch'])
            ployalty_path = "//field[@name='product_putaway_ids']"
            ployalty_fields = product_xml.xpath(ployalty_path)
            if ployalty_fields:
                ployalty_field = ployalty_fields[0]
                ployalty_field.attrib['readonly'] = "0"
                ployalty_field.attrib['context'] = \
                    "{'default_product_tmpl_id': product_tmpl_id," \
                    "'default_product_product_id': active_id}"
                res['arch'] = etree.tostring(product_xml)

        return res
