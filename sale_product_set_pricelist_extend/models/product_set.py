# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _


import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'product_set_id', string='Pricelist Items', compute_sudo=True)
    has_pricelist = fields.Boolean(string="Has pricelist", compute="_compute_has_pricelist")

    @api.multi
    def _compute_has_pricelist(self):
        for record in self:
            record.has_pricelist = len(record.pricelist_item_ids.ids) > 0
