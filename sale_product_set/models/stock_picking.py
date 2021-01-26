# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from itertools import groupby
import math

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Ungroup by sets")
    print_lots = fields.Boolean("Print Lots")
    sets_line = fields.One2many('product.set', compute="_compute_sets_line", string='Picking Sets Lines')

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.move_line_ids if x.product_set_id]) > 0

    @api.multi
    def _compute_sets_line(self):
        for record in self:
            record.sets_line = False
            sets_line = False
            for line in record.move_line_ids:
                if not sets_line:
                    sets_line = line.product_set_id
                else:
                    sets_line |= line.product_set_id
            if sets_line:
                record.sets_line = sets_line

    def prepare_stock_move_line_pset_data(self, picking_id, set_lines, quantity, set):
        res = []
        res_stock_move_line = {}
        if not self._context.get('force_validate'):
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            for line in set_lines:
                #move = self.prepare_stock_move_pset_data(picking_id, line, line.quantity*quantity)
                stock_move_line = self.env['stock.move.line'].new({
                    'picking_id': picking_id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity*quantity,
                    'ordered_qty': line.quantity*quantity,
                    'product_uom_id': line.product_id.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'date': fields.datetime.now(),
                    'product_set_id': set.id,
                })
                if not res_stock_move_line.get(line.product_id):
                    res_stock_move_line[line.product_id] = []
                res_stock_move_line[line.product_id].append((0, 0, stock_move_line._convert_to_write(stock_move_line._cache)))
                #move['move_line_ids'] = (0, 0, stock_move_line._convert_to_write(stock_move_line._cache)),
                #res.append((0, 0, move._convert_to_write(move._cache)))
                #_logger.info("TEST BEFORE %s" % move['move_line_ids'])
        for key, psets in groupby(set_lines, lambda l: l.product_set_id):
            #_logger.info("LINES %s:%s:%s:%s" % (lines, qty, set_lines, product))
            for product, lines in groupby(psets, lambda l: l.product_id):
                qty = sum([x.quantity for x in lines])
                move = self.prepare_stock_move_pset_data(picking_id, product, qty*quantity, set)
                if res_stock_move_line.get(product, False):
                    move['move_line_ids'] = res_stock_move_line[product]
                res.append((0, 0, move._convert_to_write(move._cache)))
        return res

    def prepare_stock_move_pset_data(self, picking_id, product, qty, set, old_qty=0):
        #oring = _('PSET/%s' % product_set_id.name)
        name = '%s/%s>%s' % (
                #oring,
                product.code and '/%s: ' % product.code or '/',
                self.location_id.name, self.location_dest_id.name)
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'name': name,
            'product_set_id': set.id,
            #'origin': oring,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': product.id,
            'ordered_qty': qty+old_qty,
            'product_uom_qty': qty + old_qty,
            'product_uom': product.uom_id.id,
            'product_set_id': set.id,
            'company_id': self.company_id.id,
        })
        #line_values = stock_move._convert_to_write(stock_move._cache)
        #_logger.info("Stock move %s" % stock_move)
        return stock_move

    def action_split_pset_row(self):
        #_logger.info("INVOKE SPLIT")
        update = False
        res_ids = self.env['stock.move.line']
        to_delete_ids = self.env['stock.move.line']
        for line in self.move_lines:
            #_logger.info("START %s::%s" % (line, line.move_line_ids.ids))
            if line.sale_line_id and len(line.move_line_ids.ids) > 0:
                order_line = line.sale_line_id
                if order_line.product_set_id and line.product_id.tracking != 'serial':
                    line.move_line_ids[0].package_qty = order_line.pset_quantity
                    line.move_line_ids[0].qty_done = order_line.product_uom_qty/order_line.pset_quantity
                    line.move_line_ids[0].product_set_id = order_line.product_set_id.id
                    res, to_delete = line._split_move_line()
                    res_ids |= res
                    to_delete_ids |= to_delete
                    update = True

                elif order_line.product_set_id and line.product_id.tracking == 'serial':
                    sequence = 0
                    for move_line in line.move_line_ids:
                        sequence += 1
                        move_line.product_set_id = order_line.product_set_id.id
                        move_line.sequence = sequence

        # try direct from stock move lines
        if not update:
            sequence = 0
            keep_qty_done = {}
            keep_ids = self.env['stock.move.line']
            for move_line in self.move_line_ids.filtered(lambda r: not r.result_package_id).sorted(
                    lambda r: r.product_set_id):
                line.product_set_id = move_line.product_set_id
                pset_quantity = sum([x.quantity for x in
                                     move_line.product_set_id.set_lines.filtered(
                                         lambda r: r.product_id == move_line.product_id)])
                pset_quantity = pset_quantity < 1 and 1.0 or pset_quantity

                if move_line.move_id:
                    line = move_line.move_id
                else:
                    line = self.move_lines.filtered(lambda x: x.product_id == move_line.product_id)[0]

                if not keep_qty_done.get(move_line.product_id):
                    keep_qty_done[move_line.product_id] = {'keep_pqty': pset_quantity * (line.product_uom_qty / pset_quantity), 'keep_qty': 0.0, 'keep_qty_start': 0}

                #_logger.info("SPLIT %s=>%s:%s:%s->%s::%s::%s" % (
                #    move_line.product_id.name, move_line.product_uom_qty, move_line.package_qty, move_line.qty_done,
                #    pset_quantity, move_line.split_line, line))

                if move_line.product_set_id and line.product_id.tracking != 'serial':
                    product_uom_qty = move_line.product_uom_qty
                    move_line.package_qty = line.product_uom_qty / pset_quantity
                    move_line.qty_done = int(move_line.product_uom_qty/move_line.package_qty)
                    move_line.split_lot_id = move_line.lot_id
                    package_qty = move_line.package_qty
                    lot_id = move_line.lot_id
                    qty_done = move_line.qty_done
                    qty_done_calc = move_line.product_uom_qty / move_line.package_qty

                    res, to_delete = line._split_move_line()
                    res_ids |= res
                    to_delete_ids |= to_delete
                    update = True

                    if qty_done != qty_done_calc:
                        keep_ids |= move_line
                        #_logger.info("QTY %s::%s:%s" % (lot_id, product_uom_qty, package_qty*qty_done))
                        keep_qty_done[move_line.product_id].update({'keep_qty': keep_qty_done[move_line.product_id]['keep_qty']+qty_done*package_qty, 'package': pset_quantity, lot_id: product_uom_qty - package_qty*qty_done})
                        move_line.split_lot_id = lot_id

                elif move_line.product_set_id and line.product_id.tracking == 'serial':
                    sequence += 1
                    move_line.sequence = sequence

            # calculate keep qty's
            keep_qty = 0.0
            for move_line in keep_ids:
                #_logger.info("STATE PSET %s:%s::%s:%s" % (move_line.product_id.name, move_line.split_lot_id, move_line, keep_qty_done[move_line.product_id]))
                if move_line.move_id:
                    line = move_line.move_id
                else:
                    line = self.move_lines.filtered(lambda x: x.product_id == move_line.product_id)[0]

                if keep_qty_done.get(move_line.product_id) and keep_qty_done[move_line.product_id]['keep_pqty'] - keep_qty_done[move_line.product_id]['keep_qty'] > 0.0:
                    #keep_qty = keep_qty_done[move_line.product_id]['keep_pqty'] - keep_qty_done[move_line.product_id]['keep_qty']
                    keep_qty += keep_qty_done[move_line.product_id][move_line.split_lot_id]
                    if keep_qty_done[move_line.product_id][move_line.split_lot_id]/keep_qty_done[move_line.product_id]['package'] <= 1:
                        move_line.package_qty = keep_qty_done[move_line.product_id][move_line.split_lot_id]
                        move_line.qty_done = 1.0
                    elif keep_qty_done[move_line.product_id][move_line.split_lot_id]/keep_qty_done[move_line.product_id]['package'] > 1:
                        move_line.package_qty = keep_qty_done[move_line.product_id]['package']
                        move_line.qty_done = 1.0
                        keep_qty = keep_qty_done[move_line.product_id]['package']

                    keep_qty_done[move_line.product_id]['keep_qty'] += move_line.qty_done*move_line.package_qty
                    res, to_delete = line._split_move_line(start=keep_qty_done[move_line.product_id]['keep_qty_start'])
                    keep_qty_done[move_line.product_id]['keep_qty_start'] = int(keep_qty)

                    res_ids |= res
                    to_delete_ids |= to_delete

        if update:
            # Check for package
            to_delete_ids.unlink()
            move_lines = self.move_line_ids.filtered(lambda r: r.product_set_id and r.product_id.product_tmpl_id.auto_packing)
            for line in move_lines.sorted(key=lambda r: r.sequence):
                if line.product_set_id and not line.result_package_id:
                    package = self.env['stock.quant.package'].create(self.env['stock.move']._get_data_stock_quant_package(line))
                else:
                    package = line.result_package_id
                self.move_line_ids.filtered(lambda r: r.product_set_id and r.product_set_id.id == line.product_set_id.id and r.sequence == line.sequence).write({'result_package_id': package.id})
            ## sord by sequence
            #move_lines = self.move_line_ids.filtered(lambda r: r.product_set_id)
            #if move_lines:
            #    top = max(move_lines.sorted(key=lambda r: r.sequence).mapped('product_id.id'))
            #    for line in move_lines.sorted(key=lambda r: r.product_id.id):
            #        line.write({'sequence': (top//10*10+10*line.sequence)+line.product_id.id})

        return {
                "type": "ir.actions.do_nothing",
                }

    @api.multi
    def order_lines_sets_layouted(self):
        #self.ensure_one()
        report_pages_sets = [[]]
        for picking in self:
            moves = picking.move_line_ids.sorted(lambda r: r.product_set_id.id, reverse=True)
            _logger.info("MOVE %s" % [r.product_set_id for r in moves])
            if picking.has_sets:
                pset = {}
                for line in picking.move_lines:
                    if line.sale_line_id and len(line.move_line_ids.ids) > 0:
                        order_line = line.sale_line_id
                        if order_line.product_set_id and not pset.get(order_line.product_set_id):
                            pset[order_line.product_set_id] = order_line.pset_quantity
                if not pset:
                    for p_set, lines in groupby(moves, lambda l: l.product_set_id):
                        lines_copy = list(lines)
                        p_set = p_set.sudo()
                        if p_set and p_set.set_lines and not pset.get(p_set):
                            # calculate for one product
                            # get first product
                            # first_product_id = p_set.set_lines[0]
                            for first_product_id in p_set.set_lines:
                                # _logger.info("P-SET 1 %s" % lines_copy)
                                sum_arr = [line.ordered_qty for line in lines_copy if line.product_id == first_product_id.product_id]
                                picking_pset_qty = sum(sum_arr)
                                pset_qty = first_product_id.quantity
                                pset_qty = pset_qty <= 0 and 1 or pset_qty
                                pset[p_set] = math.ceil(picking_pset_qty/pset_qty)
                                _logger.info("P-SET %s(%s):%s=%s=%s" % (first_product_id.product_id.display_name, sum_arr, pset_qty, picking_pset_qty, pset[p_set]))
                                if pset[p_set] > 0:
                                    break
                            #_logger.info("PSET %s:%s:%s:%s:%s:%s" % (p_set, pset[p_set], p_set.set_lines[0], picking_pset_qty/pset_qty, picking_pset_qty, pset_qty))

                for category, lines in groupby(moves, lambda l: l.product_set_id):
                    # Append category to current report page
                    report_pages_sets[-1].append({
                        'name': category and category.display_name or _('Uncategorized'),
                        'quantity': category and pset.get(category) and pset[category] or False or False,
                        'lines': list(lines),
                        'pset': category and category or False,
                        'codes': False,
                    })
                _logger.info("Category %s" % report_pages_sets)
                return report_pages_sets
            else:
                for category, lines in groupby(moves, lambda l: l.product_id):
                    # If last added category induced a pagebreak, this one will be on a new page
                    #if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    #    report_pages_sets.append([])
                    qty = sum(x.qty_done for x in moves if category and (x.product_id and x.product_id.id or False) == category.id)
                    # Append category to current report page
                    report_pages_sets[-1].append({
                        'name': category and category.name or _('Uncategorized'),
                        'quantity': qty,
                        'lines': list(lines),
                        'pset': False,
                        'codes': False,
                    })
        return report_pages_sets
