#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class SaleTemplateProductSet(models.Model):
    _name = 'sale.template.product.set'
    _description = 'Sale Product Sets'

    sale_order_template_id = fields.Many2one('sale.order.template', 'Order', required=True)
    product_set_section_id = fields.Many2one('sale.order.template.line', 'Product Set Section')
    product_set_id = fields.Many2one('product.set', 'Product Set')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')

    def _get_sale_template_product_set_value(self, sale_order_template_id, product_set_id, quantity):
        return {
            'sale_order_template_id': sale_order_template_id.id,
            'product_set_id': product_set_id.id,
            'quantity': quantity,
        }
