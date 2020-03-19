# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    cy_gesy_code = fields.Char('[CY] GESY code')
    cy_registration_code = fields.Char('[CY] Registration Code')
    cy_future_code = fields.Char('[CY] Future Code')
    cy_currency_id = fields.Many2one("res.currency", string="[CY] Currency", required=True, default=lambda self: self.env.ref('base.EUR').id)
    cy_gesy = fields.Monetary('[CY] GESY', currency_field='cy_currency_id')
