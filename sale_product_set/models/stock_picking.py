# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from itertools import groupby

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Ungroup by sets")

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.move_lines]) > 0

    def prepare_stock_move_line_pset_data(self, picking_id, set_lines, quantity):
        res = []
        res_stock_move_line = {}
        if not self._context.get('force_validate'):
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            for line in set_lines:
                #move = self.prepare_stock_move_pset_data(picking_id, line, line.quantity*quantity)
                stock_move_line = self.env['stock.move.line'].new({
                    'picking_id': picking_id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': quant.quantity,
                    'ordered_qty': line.quantity*quantity,
                    'product_uom_id': line.product_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'date': fields.datetime.now(),
                })
                if not res_stock_move_line.get(quant.product_id):
                    res_stock_move_line[quant.product_id] = []
                res_stock_move_line[quant.product_id].append((0, 0, stock_move_line._convert_to_write(stock_move_line._cache)))
                #move['move_line_ids'] = (0, 0, stock_move_line._convert_to_write(stock_move_line._cache)),
                #res.append((0, 0, move._convert_to_write(move._cache)))
                #_logger.info("TEST BEFORE %s" % move['move_line_ids'])
        for product, lines in groupby(set_lines, lambda l: l.product_id):
            qty = sum([x.quantity for x in lines])
            _logger.info("LINES %s:%s:%s:%s" % (lines, qty, set_lines, product))
            move = self.prepare_stock_move_pset_data(picking_id, product, qty*quantity)
            if res_stock_move_line.get(product, False):
                move['move_line_ids'] = res_stock_move_line[product]
            res.append((0, 0, move._convert_to_write(move._cache)))
        return res

    def prepare_stock_move_pset_data(self, picking_id, product, qty, old_qty=0):
        #oring = _('PSET/%s' % product_set_id.name)
        name = '%s/%s>%s' % (
                #oring,
                product.code and '/%s: ' % product.code or '/',
                self.location_id.name, self.location_dest_id.name)
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'name': name,
            #'origin': oring,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': product.id,
            'ordered_qty': qty+old_qty,
            'product_uom_qty': qty + old_qty,
            'product_uom': product.uom_id.id,
        })
        #line_values = stock_move._convert_to_write(stock_move._cache)
        #_logger.info("Stock move %s" % stock_move)
        return stock_move

    def action_split_pset_row(self):
        sequence = 0
        for line in self.move_lines:
            if line.sale_line_id and len(line.move_line_ids.ids) > 0:
                order_line = line.sale_line_id
                if order_line.product_set_id and line.product_id.tracking != 'serial':
                    line.move_line_ids[0].package_qty = order_line.pset_quantity
                    line.move_line_ids[0].qty_done = order_line.product_uom_qty/order_line.pset_quantity
                    line.move_line_ids[0].product_set_id = order_line.product_set_id.id
                    res = line._split_move_line()
                elif order_line.product_set_id and line.product_id.tracking == 'serial':
                    sequence = 0
                    for move_line in line.move_line_ids:
                        sequence += 1
                        move_line.product_set_id = order_line.product_set_id.id
                        move_line.sequence = sequence

        # Check for package
        move_lines = self.move_line_ids.filtered(lambda r: r.product_set_id and r.product_id.product_tmpl_id.auto_packing)
        for line in move_lines.sorted(key=lambda r: r.sequence):
            if line.product_set_id:
                package = self.env['stock.quant.package'].create({})
                self.move_line_ids.filtered(lambda r: r.product_set_id and r.product_set_id.id == line.product_set_id.id and r.sequence == line.sequence).write({'result_package_id': package.id})
        # sord by sequence
        move_lines = self.move_line_ids.filtered(lambda r: r.product_set_id)
        if move_line:
            top = max(move_lines.sorted(key=lambda r: r.sequence).mapped('product_id.id'))
            for line in move_lines.sorted(key=lambda r: r.product_id.id):
                line.write({'sequence': (top//10*10+10*line.sequence)+line.product_id.id})

        return {
                "type": "ir.actions.do_nothing",
                }