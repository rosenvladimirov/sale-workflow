# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def prepare_sale_order_line_set_data(self, sale_order_id, set, set_line, qty, set_id,
                                     max_sequence=0, old_qty=0, old_pset_qty=0, split_sets=False):
        line_values = super(SaleOrder, self).prepare_sale_order_line_set_data(sale_order_id, set, set_line, qty, set_id,
                                     max_sequence=max_sequence, old_qty=old_qty, old_pset_qty=old_pset_qty, split_sets=split_sets)
        #line_values['pricelist_rule_id'] = set_line.pricelist_rule_id.id
        if set_line.product_id:
            so = self.env['sale.order'].browse([sale_order_id])
            line_values['code'] = set_line.product_id.with_context(pricelist=so.pricelist_id.id, product_set_id=line_values['product_set_id']).pricelist_code
        return line_values
