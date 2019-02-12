# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.move_lines]) > 0

    def prepare_stock_move_line_package_data(self, picking_id, package):
        res = []
        for quant in package.quant_ids:
            qty = sum(x.quantity for x in quant)
            stock_move_line = self.env['stock.move.line'].new({
                'picking_id': picking_id,
                'product_id': quant.product_id.id,
                'product_uom_qty': quant.quantity,
                'ordered_qty': quant.quantity,
                'product_uom_id': quant.product_uom_id.id,
                'lot_id': quant.lot_id,
                'package_id': quant.package_id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
            stock_move_line.onchange_product_id()
            move = self.prepare_stock_move_pset_data(picking_id, quant, qty, package)
            move.update({
                'move_line_ids': [(0, 0, stock_move_line._convert_to_write(stock_move_line._cache))],
                })
            _logger.info("Move %s" % move)
            res.append((0, 0, move))
        return res

    def prepare_stock_move_pset_data(self, picking_id, set_line, qty, package, old_qty=0):
        stock_move = self.env['stock.move'].new({
            'picking_id': picking_id,
            'origin': _('PSET/%s' % package.name),
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': set_line.product_id.id,
            'ordered_qty': qty+old_qty,
            'product_uom_id': set_line.product_uom_id.id,
        })
        stock_move.onchange_product_id()
        line_values = stock_move._convert_to_write(stock_move._cache)
        return line_values
