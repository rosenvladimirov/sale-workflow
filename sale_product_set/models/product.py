# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from lxml import etree


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_set_ids = fields.One2many(
        comodel_name='product.set.line',
        inverse_name='product_tmpl_id',
        string="Product set lines",
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_set_ids = fields.One2many(
        comodel_name='product.set.line',
        inverse_name='product_id',
        string="Product set lines",
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
            pset_path = "//field[@name='product_set_ids']"
            pset_fields = product_xml.xpath(pset_path)
            if pset_fields:
                pset_field = pset_fields[0]
                pset_field.attrib['readonly'] = "0"
                pset_field.attrib['context'] = \
                    "{'default_product_tmpl_id': product_tmpl_id," \
                    "'default_product_product_id': active_id}"
                res['arch'] = etree.tostring(product_xml)

        return res
