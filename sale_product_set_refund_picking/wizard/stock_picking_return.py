# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from itertools import groupby
from odoo.tools.float_utils import float_round

import logging
_logger = logging.getLogger(__name__)


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        if return_line.product_set_id:
            vals.update({
                'product_set_id': return_line.product_set_id.id,
            })
        return vals

    @api.model
    def default_get(self, fields):
        res = super(ReturnPicking, self).default_get(fields)
        if res.get('picking_id') and res.get('product_return_moves'):
            product_return_moves = []
            picking = self.env['stock.picking'].browse(res['picking_id'])
            if picking:
                for move in picking.move_lines:
                    moves = move.move_line_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
                    moves_old_refunds = move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids')
                    moves |= moves_old_refunds
                    for product_set, lines in groupby(moves.sorted(lambda r: r.product_set_id, reverse=True),
                                                    lambda l: l.product_set_id):
                        quantity = move.product_qty - sum([r.product_qty for r in lines])
                        quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                        product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity,
                                                            'move_id': move.id, 'uom_id': move.product_id.uom_id.id,
                                                            'product_set_id': product_set.id}))
                if product_return_moves:
                    res['product_return_moves'] = product_return_moves
        return res


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete='restrict')


