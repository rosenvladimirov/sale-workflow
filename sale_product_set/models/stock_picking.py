# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.move_lines]) > 0

    def prepare_stock_move_line_pset_data(self, picking_id, set_line, quantity):
        res = []
        for line in set_line:
            move = self.prepare_stock_move_pset_data(picking_id, line, line.quantity*quantity)
            stock_move_line = self.env['stock.move.line'].new({
                'picking_id': picking_id,
                'product_id': line.product_id.id,
                #'product_uom_qty': quant.quantity,
                'ordered_qty': line.quantity*quantity,
                'product_uom_id': line.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
            move['move_line_ids'] = (0, 0, stock_move_line._convert_to_write(stock_move_line._cache)),
            res.append((0, 0, move._convert_to_write(move._cache)))
            _logger.info("TEST BEFORE %s" % move['move_line_ids'])
        _logger.info("Lines %s" % (res))
        return res

    def prepare_stock_move_pset_data(self, picking_id, set_line, qty, old_qty=0):
        oring = _('PSET/%s' % set_line.product_set_id.name)
        name = '%s%s/%s>%s' % (
                oring,
                set_line.product_id.code and '/%s: ' % set_line.product_id.code or '/',
                self.location_id.name, self.location_dest_id.name)
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'name': name,
            'origin': oring,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': set_line.product_id.id,
            #'ordered_qty': qty+old_qty,
            'product_uom_qty': qty + old_qty,
            'product_uom': set_line.product_id.uom_id.id,
        })
        #line_values = stock_move._convert_to_write(stock_move._cache)
        _logger.info("Stock move %s" % stock_move)
        return stock_move

    def prepare_stock_move_line_package_data(self, picking_id, package):
        res = []
        qty = sum([x.quantity for x in package.quant_ids])
        for quant in package.quant_ids:
            _logger.info("Lines %s:%s:%s" % (quant, quant.quantity, quant.product_uom_id))
            move = self.prepare_stock_move_package_data(picking_id, quant, qty, package)
            stock_move_line = self.env['stock.move.line'].new({
                'picking_id': picking_id,
                'product_id': quant.product_id.id,
                #'product_uom_qty': quant.quantity,
                'ordered_qty': quant.quantity,
                'product_uom_id': quant.product_uom_id.id,
                'lot_id': quant.lot_id,
                'package_id': quant.package_id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
            move['move_line_ids'] = (0, 0, stock_move_line._convert_to_write(stock_move_line._cache)),
            _logger.info("TEST BEFORE %s" % move['move_line_ids'])
            res.append((0, 0, move._convert_to_write(move._cache)))
        _logger.info("Lines %s" % (res))
        return res

    def prepare_stock_move_package_data(self, picking_id, set_line, qty, package, old_qty=0):
        oring = _('PKG/%s' % package.name)
        name = '%s%s/%s>%s' % (
                oring,
                set_line.product_id.code and '/%s: ' % set_line.product_id.code or '/',
                self.location_id.name, self.location_dest_id.name)
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'name': name,
            'origin': oring,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': set_line.product_id.id,
            #'ordered_qty': qty+old_qty,
            'product_uom_qty': qty+old_qty,
            'product_uom': set_line.product_uom_id.id,
        })
        #line_values = stock_move._convert_to_write(stock_move._cache)
        _logger.info("Stock move %s" % stock_move)
        return stock_move

    def action_split_pset_row(self):
        for line in self.move_lines:
            if line.sale_line_id and len(line.move_line_ids.ids) > 0:
                order_line = line.sale_line_id
                if order_line.product_set_id:
                    #for x in range(1, int(order_line.pset_quantity)+1):
                    line.move_line_ids[0].package_qty = order_line.pset_quantity
                    line.move_line_ids[0].qty_done = order_line.product_uom_qty/order_line.pset_quantity
                    line.move_line_ids[0].product_set_id = order_line.product_set_id.id
                    #if float_compare(line.move_line_ids[0].qty_done, line.move_line_ids[0].product_uom_qty,
                    #              precision_rounding=line.move_line_ids[0].product_uom_id.rounding) < 0:
                    res = line._split_move_line()
                    #    line.move_line_ids[0].product_set_id = False
        # Check for package
        move_lines = self.move_line_ids.filtered(lambda r: r.product_set_id and r.result_package_id)
        for line in move_lines:
            self.move_line_ids.filtered(lambda r: r.product_set_id == line.product_set_id and r.sequence == line.sequence and not r.result_package_id).write({'result_package_id': line.result_package_id.id})
        return {
                "type": "ir.actions.do_nothing",
                }