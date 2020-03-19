# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    bg_bda_code = fields.Char('[BG] BDA Code')
    bg_future_code = fields.Char('[BG] Future code')
    bg_currency_id = fields.Many2one("res.currency", string="[BG] Currency", required=True, default=lambda self: self.env.ref('base.BGN').id)
    bg_reimbursement = fields.Monetary('Reimbursement', currency_field='bg_currency_id')
    bg_nhif = fields.Char('[BG] NHIF Code')
