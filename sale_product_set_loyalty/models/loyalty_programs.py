# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class LoyaltyRule(models.Model):
    _inherit = 'loyalty.rule'


    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete='restrict')


    @api.multi
    def _check_match(self, product, qty, price, **kwargs):
        return super(LoyaltyRule, self)._check_match(product, qty, price, **kwargs) and (not self.product_set_id or self.product_set_id == kwargs['product_set'])
