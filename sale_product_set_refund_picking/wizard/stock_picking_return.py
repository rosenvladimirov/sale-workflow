# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
from odoo.addons.stock.wizard import stock_picking_return as stockpickingreturn

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
                res_move_id = set([])
                quantity_new = {}
                for move_line in res['product_return_moves']:
                    # _logger.info("product return moves %s" % (move_line,))
                    cmd, arg, value = move_line
                    res_move_id.update([value['move_id']])
                    quantity_new[value['move_id']] = value['quantity']
                move_lines = self.env['stock.move'].browse(list(res_move_id))
                for move in move_lines:
                    if move.state == 'cancel':
                        continue
                    if move.scrapped:
                        continue
                    moves = move.move_line_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
                    quantity_save = quantity_new[move.id]
                    for product_set, lines in groupby(moves.sorted(lambda r: r.product_set_id, reverse=True), lambda l: l.product_set_id):
                        lines_lot = []
                        for line in lines:
                            lines_lot.append(line)
                        for lot_id, line_lot in groupby(sorted(lines_lot, key=lambda k: k.lot_id, reverse=True), lambda r: r.lot_id):
                            quantity = sum([r.qty_done for r in line_lot])
                            quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                            # _logger.info("QTY %s(%s)==>%s=%s" % (product_set, [r.qty_done for r in moves.filtered(lambda r: r.product_set_id == product_set)], quantity, quantity_save))
                            quantity_save -= quantity
                            product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity,
                                                                'move_id': move.id, 'uom_id': move.product_id.uom_id.id,
                                                                'lot_id': lot_id and lot_id.id or False,
                                                                'product_set_id': product_set.id}))
                if product_return_moves:
                    res['product_return_moves'] = product_return_moves
        return res


    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        force_product_set = any([r.product_set_id for r in self.product_return_moves])
        if force_product_set:
            for move_id, lines in groupby(self.product_return_moves.sorted(lambda r: r.move_id),
                                              lambda l: l.move_id):
                return_line_move = []
                for return_line in lines:
                    return_line_move.append(return_line)
                _logger.info("LINES %s" % return_line_move)
                if any([r.quantity != 0 for r in return_line_move]):
                    returned_lines += 1
                    vals = self._prepare_move_default_values(return_line_move[0], new_picking)
                    r = move_id.copy(vals)
                    move_id_id = r.id
                    vals = {}
                    move_line_ids = []
                    # make all operations rows
                    for return_line in return_line_move:
                        stock_move_line = self.env['stock.move.line'].new({
                            'picking_id': new_picking.id,
                            'product_id': return_line.product_id.id,
                            'product_uom_qty': return_line.quantity,
                            'ordered_qty': return_line.quantity,
                            'product_uom_id': return_line.product_id.uom_id.id,
                            'lot_id': return_line.lot_id and return_line.lot_id.id or False,
                            'location_id': return_line.move_id.location_dest_id.id,
                            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
                            'date': fields.datetime.now(),
                            'product_set_id': return_line.product_set_id and return_line.product_set_id.id or False,
                            'move_id': move_id_id,
                        })
                        move_line_ids.append((0, 0, stock_move_line._convert_to_write(stock_move_line._cache)))
                    r.write({'move_line_ids': move_line_ids})

                    # +--------------------------------------------------------------------------------------------------------+
                    # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                    # |              | returned_move_ids              ↑                                  | returned_move_ids
                    # |              ↓                                | return_line.move_id              ↓
                    # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                    # +--------------------------------------------------------------------------------------------------------+
                    move_orig_to_link = move_id.move_dest_ids.mapped('returned_move_ids')
                    move_dest_to_link = move_id.move_orig_ids.mapped('returned_move_ids')
                    vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | move_id]
                    vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                    r.write(vals)
        else:
            for return_line in self.product_return_moves:
                if not return_line.move_id:
                    raise UserError(_("You have manually created product lines, please delete them to proceed"))
                # TODO sle: float_is_zero?
                if return_line.quantity:
                    returned_lines += 1
                    vals = self._prepare_move_default_values(return_line, new_picking)
                    r = return_line.move_id.copy(vals)
                    vals = {}

                    # +--------------------------------------------------------------------------------------------------------+
                    # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                    # |              | returned_move_ids              ↑                                  | returned_move_ids
                    # |              ↓                                | return_line.move_id              ↓
                    # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                    # +--------------------------------------------------------------------------------------------------------+
                    move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                    move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                    vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                    vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                    r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

stockpickingreturn._create_returns = ReturnPicking._create_returns


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete='restrict')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    # lot_name = fields.Char('Lot/Serial Number')
