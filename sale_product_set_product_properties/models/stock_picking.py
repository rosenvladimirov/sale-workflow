# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    print_sets_line = fields.Many2many('product.set', related="product_prop_static_id.sets_line")

    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        if 'print_sets_line' in vals:
            res.product_prop_static_id.print_sets_line = res.print_sets_line
        return res

    @api.multi
    def write(self, vals):
        res = super(Picking, self).write(vals)
        if 'print_sets_line' in vals:
            # use mapped to call write one time good for performance
            for record in self:
                if not record.product_prop_static_id:
                    vals = self.env['product.properties.static'].static_property_data(record, vals, property_data={'print_sets_line': vals['print_sets_line']})
                if not record.print_sets_line and record.product_prop_static_id:
                    for line in record.product_prop_static_id:
                        line.print_sets_line = vals['print_sets_line']
        # for record in self:
        #     _logger.info("VALS %s:%s:%s" % (record.product_prop_static_id, record.print_sets_line, vals.get('print_sets_line')))
        return res
