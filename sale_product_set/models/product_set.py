#  Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, tools, api, _, Command, SUPERUSER_ID


class ProductSet(models.Model):
    _inherit = "product.set"

    def prepare_sale_order_values(self, sequence, order_id=False):
        self.ensure_one()
        values = {
            "sequence": sequence,
            "name": self.display_name,
            "product_set_id": self.id,
            "display_type": 'line_section',
        }
        if order_id:
            values["order_id"] = order_id.id
        return values
