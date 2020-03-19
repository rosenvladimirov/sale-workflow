# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    fleet_ids = fields.Many2many(comodel_name="fleet.vehicle.model", relation="fleet_vehicle_model_product_set_rel", column1="product_set_id", column2="model_id", string="Fleet model")

