# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    gr_ekapty_code = fields.Char('[GR] EKAPTY code')
    gr_eof_code = fields.Char('[GR] EOF Code')
    gr_observer_code = fields.Char('[GR] Observer code')
    gr_future_code = fields.Char('[GR] Future Code')
    gr_currency_id = fields.Many2one("res.currency", string="[GR] Currency", required=True, default=lambda self: self.env.ref('base.EUR').id)
    gr_observer = fields.Monetary('[GR] Observer', currency_field='gr_currency_id')
