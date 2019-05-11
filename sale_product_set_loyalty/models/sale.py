# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _calculate_loyalty_points(self, product, qty, price, **kwargs):
        kwargs.update(dict(product_set=self.product_set_id))
        return self.order_id.loyalty_program_id.calculate_loyalty_points(product, qty, price, **kwargs)