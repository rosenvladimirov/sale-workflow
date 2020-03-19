# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    product_set_ids = fields.Many2many(comodel_name="product.set", relation="fleet_vehicle_model_product_set_rel", column1="model_id", column2="product_set_id", string="Product sets")
