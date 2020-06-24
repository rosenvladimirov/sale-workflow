# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductProperties(models.Model):
    _inherit = "product.properties"

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict')

    @api.multi
    def _get_type_field_properties(self):
        for field_name in self:
            if not field_name.type_field_name:
                field_name.type_field_name = field_name.type_field_target.name
            if not field_name.type_field_ttype:
                field_name.type_field_ttype = field_name.type_field_target.ttype
            if not field_name.type_field_model:
                field_name.type_field_model = field_name.type_field_target.model_id.model
            if not field_name.model_obj_id and field_name.type_field_model == 'product.product':
                field_name.model_obj_id = field_name.product_id.id
            elif not field_name.model_obj_id and field_name.type_field_model == 'product.template':
                field_name.model_obj_id = field_name.product_tmpl_id.id
            #elif not field_name.model_obj_id and field_name.type_field_model == 'product.pricelist.item':
             #   field_name.model_obj_id = field_name.pricelist_rule_id.id
            elif not field_name.model_obj_id and field_name.type_field_model == 'product.set':
                field_name.model_obj_id = field_name.product_set_id.id

    def _set_model_obj_id(self):
        for rec in self:
            if not rec.model_obj_id and rec.type_field_model == 'product.product':
                rec.model_obj_id = rec.product_id.id
            elif not rec.model_obj_id and rec.type_field_model == 'product.template':
                rec.model_obj_id = rec.product_tmpl_id.id
            elif not rec.model_obj_id and rec.type_field_model == 'product.set':
                rec.model_obj_id = rec.product_set_id.id

    @api.model
    def set_all_print_properties(self, res, lines, mode='standard'):
        print_properties = super(ProductProperties, self).set_all_print_properties(res, lines, mode=mode)

        def add_set_exluded(x, ids):
            ids.update([x])
            return x

        if res._name == 'stock.picking':
            res_model_id = 'picking_id'
        elif res._name == 'sale.order':
            res_model_id = 'order_id'
        elif res._name == 'account.invoice':
            res_model_id = 'invoice_id'
        elif res._name == 'res.partner':
            res_model_id = 'partner_id'
        else:
            return False

        for record in res:
            print_ids = False
            ids = set([])
            for r in lines.mapped('product_set_id'):
                if print_ids:
                    print_ids |= r.product_properties_ids
                else:
                    print_ids = r.product_properties_ids
            #_logger.info("PROPERTIES %s" % print_ids)
            if print_ids:
                print_properties = [(0, False, {'name': add_set_exluded(x.name.id, ids), res_model_id: record.id, 'print': True, 'sequence': x.sequence}) for x in print_ids if x.name and x.name.id not in list(ids)] + print_properties
        return print_properties


class ProductPropertiesType(models.Model):
    _inherit = "product.properties.type"

    def _get_type_field_model_id(self):
        return [('model', 'in', ['product.product', 'product.template', 'product.pricelist.item', 'sale.order.line',
                                 'account.invoice.line', 'purchase.order.line', 'stock.move.line', 'product.set'])]

    type_field_model_id = fields.Many2one('ir.model', string='Target/Source Odoo model', domain=_get_type_field_model_id)


class ProductPropertiesCategory(models.Model):
    _inherit = "product.properties.category"

    applicability = fields.Selection(selection_add=[
            ('set', 'Product Set')])
