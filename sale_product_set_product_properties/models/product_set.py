# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    product_properties_ids = fields.One2many("product.properties", "product_set_id", string='Product sets properties')
    has_product_properties = fields.Boolean(compute="_compute_has_product_properties", string="Sets Product properties")

    categ_ids = fields.Many2many('product.properties.category', relation="product_set_prop", string='Global Category properties')

    massedit = fields.Boolean()

    @api.onchange('product_prop_static_id')
    def _onchange_product_prop_static_id(self):
        for prod in self:
            if prod.product_prop_static_id:
                prod.categ_ids = False
                prod.categ_ids = (6, False, [x.id for x in self.env['product.properties.category'].search([('applicability', '=', 'set')])])
                prod._onchange_categ_ids()

    @api.onchange('categ_ids')
    def _onchange_categ_ids(self):
        for prod in self:
            ret = []
            for categ in prod.categ_ids:
                ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)

    def _get_default_product_properties_ids(self, properties, categ_id=False, product=False, default={}):
        system = False
        if not product:
            product = self
        if not properties:
            system = True
            properties = self.env['product.properties.type'].search([])
        res = []
        sequence = 0
        name_ids = [x.name.id for x in self.product_properties_ids]
        for rec in properties.sorted(key=lambda r: r.sequence):
            if default and default.get(rec.name.name):
                if rec.type_fields == 'int':
                    if default[rec.name.name]['value'] and default[rec.name.name]['value'].find(".") == -1:
                        type_int = int(default[rec.name.name]['value'])
                    elif default[rec.name.name]['value']:
                        type_float = float(default[rec.name.name]['value'])
                        type_fields = 'float'
                    else:
                        type_int = default[rec.name.name]['value']
                elif rec.type_fields == 'float':
                    type_float = float(default[rec.name.name]['value'])
                elif rec.type_fields == 'char':
                    type_char = default[rec.name.name]['value']
                elif rec.type_fields == 'range':
                    type_int = default[rec.name.name]['min']
                    type_int_second = default[rec.name.name]['max']
                elif rec.type_fields == 'package':
                    package = self.env['product.properties.package'].search([('name', '=', default[rec.name.name]['value'])])
                    if package:
                        type_package_id = package.id
                        type_char = rec.type_char
                    else:
                        type_package_id = rec.type_package_id.id
                        type_char = rec.type_char
                uom = self.env['product.properties.uom'].search([('name', '=', default[rec.name.name]['unit'])])
                if uom:
                    type_uom_id = uom.id
                else:
                    type_uom_id = rec.type_uom_id.id
            sequence += 1
            if rec.name.id not in name_ids:
                #_logger.info("LINE %s" % categ_id.id)
                #'product_id': product.product_variant_id.id,
                value = {'product_set_id': product.id,
                          'sequence': sequence,
                          'name': system and rec.id or rec.name.id,
                          'categ_id': categ_id.id,
                          'type_fields': rec.type_fields,
                          'type_char': rec.type_char,
                          'type_int': rec.type_int,
                          'type_int_second': rec.type_int_second,
                          'type_float': rec.type_float,
                          'type_boolean': rec.type_boolean,
                          'type_package_id': rec.type_package_id and rec.type_package_id.id or False,
                          'type_field_model_id': rec.type_field_model_id and rec.type_field_model_id.id or False,
                          'type_field_target': rec.type_field_target and rec.type_field_target.id or False,
                          'dimensions_x': rec.dimensions_x,
                          'dimensions_y': rec.dimensions_y,
                          'dimensions_z': rec.dimensions_z,
                          'type_uom_id': rec.type_uom_id and rec.type_uom_id.id or False,
                          }
                line = self.env["product.properties"].new(value)
                res.append((0, False, line._convert_to_write(line._cache)))
        return res


    @api.one
    @api.depends('product_properties_ids')
    def _compute_has_product_properties(self):
        self.has_product_properties = len(self.product_properties_ids.ids) > 0

    def get_product_properties_print(self, product, properties_print=False, lot_ids=False, description=False):
        if not product:
            return False
        res = {}
        ret = []
        print_ids = [x.name.id for x in properties_print if x.print]
        for prop_line in product.product_properties_ids:
            if properties_print and prop_line.name.id in print_ids:
                if lot_ids and prop_line.name.type_fields == 'lot':
                    res[prop_line.name.name] = {'value': lot_ids and '-'.join([x.name for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and prop_line.name.type_fields == 'use_date':
                    res[prop_line.name.name] = {'value': lot_ids and '-'.join(['%s:%s' % (x.name, x.use_date) for x in lot_ids]) or '', 'attrs': False, 'image': False}
                elif lot_ids and prop_line.name.type_fields == 'gs1':
                    res[prop_line.name.name] = {'value': lot_ids and '-'.join([x.gs1 for x in lot_ids]) or '', 'attrs': False, 'image': False}
                else:
                    res[prop_line.name.name] = {'value': prop_line.type_display, 'attrs': prop_line.type_display_attrs, 'image': prop_line.image_small}
        for k, v in res.items():
            if v['value']:
                ret.append({'label': k, 'value': v})
        #_logger.info("RETURN %s" % ret)
        return ret

    @api.model
    def create(self, vals):
        res = super(ProductSet, self).create(vals)
        if "product_properties_ids" not in vals:
            category = self.env['product.properties.category'].search([('applicability', '=', 'set')])
            for prod in res.with_context(block=True):
                ret = []
                for categ in category:
                    ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)
                if ret:
                    res.product_properties_ids = ret
        return res

    @api.multi
    def write(self, vals):
        if vals.get('massedit') and vals.get('categ_ids'):
            category = self.env['product.properties.category'].search([('id', 'in', [x[1] for x in vals.get('categ_ids')])])
            for prod in self:
                ret = []
                for categ in category:
                    ret += prod._get_default_product_properties_ids(categ.lines_ids, categ_id=categ, product=prod)
                if ret:
                    vals['product_properties_ids'] = ret
        return super(ProductSet, self).write(vals)
