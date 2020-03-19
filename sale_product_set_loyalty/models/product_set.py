# Copyright 2019 dXFactory Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    loyalty_item_ids = fields.One2many('loyalty.rule', 'product_set_id', string='Pricelist Items', compute_sudo=True)
