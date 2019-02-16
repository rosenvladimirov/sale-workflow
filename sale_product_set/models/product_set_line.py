# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductSetLine(models.Model):
    _name = 'product.set.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'

    def _get_domain(self):
        if self.type == 'sale':
            return [('sale_ok', '=', True)]
        elif self.type == 'purchase':
            return [('purchase_ok', '=', True)]
        else:
            return ["|", ('sale_ok', '=', True), ('purchase_ok', '=', True)]

    product_id = fields.Many2one(comodel_name='product.product', domain=_get_domain, string='Product', required=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    product_set_id = fields.Many2one('product.set', string='Set', ondelete='cascade',)
    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)
