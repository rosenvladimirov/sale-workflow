# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare

class MrpProductProduce(models.TransientModel):
    _name = "mrp.bom.import"
    _description = "Transform BOM to product set"

    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        help="Bill of Materials allow you to define the list of required raw materials to make a finished product.")
    product_set_id = fields.Many2one('product.set', 'Product set', required=True, domain="[('state', '=', 'draft'), ('active', '=', True)]")
    product_qty = fields.Float(
        'Quantity To Produce',
        default=1.0, digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)

    @api.multi
    def import_bom(self):
        for bom in self:
            if bom.bom_id:
                for product in bom.bom_id.bom_line_ids:
                    self.env['product.set.line'].new({
                                                    'product_id': product.product_id.id,
                                                    'quantity': product.product_qty,
                                                    'product_uom': product.product_uom_id.id,
                                                    })
