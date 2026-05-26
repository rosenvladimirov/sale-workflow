#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, tools, api, _, Command, SUPERUSER_ID


class ProductSet(models.Model):
    _inherit = "product.set"

    def prepare_sale_order_template_values(self, sequence, sale_order_template_id=False):
        self.ensure_one()
        values = {
            "sequence": sequence,
            "name": self.display_name,
            "product_set_id": self.id,
            "display_type": 'line_section',
        }
        if sale_order_template_id:
            values["sale_order_template_id"] = sale_order_template_id.id
        return values
