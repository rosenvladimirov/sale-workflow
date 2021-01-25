# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import copy
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_sale_order_line_picking_data(self, line, picking):
        res = super(SaleOrder, self)._prepare_sale_order_line_picking_data(line, picking)
        product_set_id = False
        for move_line in line.move_line_ids:
            if not product_set_id:
                product_set_id = move_line.product_set_id
            else:
                product_set_id |= move_line.product_set_id
        if len(product_set_id.ids) > 0:
            res.update({'product_set_id': product_set_id[0].id})
            _logger.info("PSET LINE FOR PUT %s" % res)
        return res

    def prepare_sale_order_line_picking_data(self, pickings):
        order, order_line = super(SaleOrder,self).prepare_sale_order_line_picking_data(pickings)
        pset = {}
        sets_line = []
        if not order:
            order = {}
        for line in pickings.move_line_ids:
            qty = sum([x.quantity for x in
                       line.product_set_id.set_lines.filtered(lambda r: r.product_id == line.product_id)])
            qty = qty == 0.0 and 1.0 or qty
            if line.product_set_id:
                pset[line.product_set_id] = line.move_id.ordered_qty / qty
            continue
        for k,v in pset.items():
            sets_line.append((0, False, {'order_id': self.id, 'product_set_id': k.id, 'quantity': v}))
        if sets_line:
            order.update({'sets_line': sets_line})
        return order, order_line

