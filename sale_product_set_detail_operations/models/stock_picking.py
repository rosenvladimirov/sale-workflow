# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_get_stock_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('sale_product_set_detail_operations.stock_move_line_inherit_action')
        if not action_ref:
            return False
        sets = False
        for line in self.move_line_ids:
            if not sets:
                sets = line.product_set_id
            else:
                sets |= line.product_set_id

        action_data = action_ref.read()[0]
        action_data['domain'] = [('picking_id', '=', self.id)]
        action_data['context'] = {'default_picking_id': self.id,
                                  'default_location_id': self.location_id.id,
                                  'default_location_dest_id': self.location_dest_id.id,
                                  'default_product_set_id': sets and sets[-1].id or False,
                                  'parent': self}
        return action_data


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    show_lots_text = fields.Boolean(compute='_compute_show_lots_text')
    picking_location_id = fields.Many2one('stock.location', related="picking_id.location_id")
    picking_location_dest_id = fields.Many2one('stock.location', related="picking_id.location_dest_id")

    @api.depends('picking_id')
    def _compute_show_lots_text(self):
        group_production_lot_enabled = self.user_has_groups('stock.group_production_lot')
        for record in self:
            for picking in record.picking_id:
                if not picking.move_line_ids:
                    picking.show_lots_text = False
                elif group_production_lot_enabled and picking.picking_type_id.use_create_lots \
                        and not picking.picking_type_id.use_existing_lots and picking.state != 'done':
                    picking.show_lots_text = True
                else:
                    picking.show_lots_text = False
