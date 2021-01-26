# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def calculate_loyalty_points(self, product, qty, price, **kwargs):
        kwargs.update(dict(product_set=self.product_set_id))
        #_logger.info("SALE LOIALTY %s:%s" % (product.name, kwargs))
        return self.order_id.loyalty_program_id.calculate_loyalty_points(product, qty, price, **kwargs)

    @api.onchange('product_set_id')
    def product_set_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        if self.order_id.loyalty_program_id:
            self.set_loyalty_points()
        return result
