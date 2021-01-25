# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    move_line_ids = fields.One2many('stock.move.line', compute="_compute_move_line_ids", inverse="_set_move_line_ids", string='Stock Moves')
    has_move_line_ids = fields.Boolean(compute="_compute_has_move_line_ids")
    picking_id = fields.One2many('stock.picking', compute="_compute_picking_id", string="Last opened picking")
    location_id = fields.Many2one('stock.location', "Source Location", compute="_compute_picking")
    location_dest_id = fields.Many2one('stock.location', "Destination Location", compute="_compute_picking")
    picking_state = fields.Selection([
                                ('draft', 'Draft'),
                                ('waiting', 'Waiting Another Operation'),
                                ('confirmed', 'Waiting'),
                                ('assigned', 'Ready'),
                                ('done', 'Done'),
                                ('cancel', 'Cancelled'),
                                ('no', 'No Active picking'),
                            ], string='Picking Status', compute='_compute_picking')
    picking_is_locked = fields.Boolean('Picking is locked', compute='_compute_picking')
    picking_type_entire_packs = fields.Boolean(compute='_compute_picking')
    picking_show_validate = fields.Boolean(compute='_compute_picking')
    show_lots_text = fields.Boolean(compute='_compute_picking')
    entire_package_detail_ids = fields.One2many('stock.quant.package', compute='_compute_picking',
                                                help='Those are the entire packages of a picking shown in the view of detailed operations')

    @api.multi
    def _compute_move_line_ids(self):
        for record in self:
            record.move_line_ids = False
            for order_line in record.order_line:
                if order_line.move_ids:
                    for move_line in order_line.move_ids:
                        for line in move_line.move_line_ids:
                            record.move_line_ids |= line

    @api.multi
    def _set_move_line_ids(self):
        for record in self:
            for line in record.move_line_ids:
                line = line if line else False
                #_logger.info("LINE %s:%s" % (line, self._context))
                if isinstance(line.id, models.NewId):
                    new_line = line._convert_to_write(line._cache)
                    #_logger.info("LINE %s:%s:%s:%s" % (record, record.move_line_ids, line._convert_to_write(line._cache), new_line))
                    move = record.picking_id.mapped('move_lines').filtered(lambda r: r.product_id == line.product_id)
                    if move:
                        new_line.update({'move_id': move[0].id, 'picking_id': record.picking_id.id})
                        _logger.info("NEW %s" % new_line)
                        line.create(new_line)
                #if updated_line:
                #    line.write(updated_line)

    @api.multi
    @api.depends('move_line_ids')
    def _compute_has_move_line_ids(self):
        for record in self:
            record.has_move_line_ids = len(record.move_line_ids.ids) > 0

    @api.multi
    @api.depends('picking_ids')
    def _compute_picking_id(self):
        for record in self:
            if record.picking_ids:
                picking_ids = record.picking_ids.sorted(lambda r: r.id).filtered(lambda r: r.state not in ['done', 'cancel'])
                if len(picking_ids.ids) == 1:
                    record.picking_id = picking_ids[-1]
                else:
                    record.picking_id = False
            else:
                record.picking_id = False

    @api.multi
    @api.depends('picking_ids')
    def _compute_picking(self):
        for record in self:
            if record.picking_ids:
                picking_ids = record.picking_ids.sorted(lambda r: r.id).filtered(lambda r: r.state not in ['done', 'cancel'])
                if len(picking_ids.ids) == 1:
                    record.location_id = picking_ids[-1].location_id
                    record.location_dest_id = picking_ids[-1].location_dest_id
                    record.picking_state = picking_ids[-1].state
                    record.picking_is_locked = picking_ids[-1].is_locked
                    record.picking_type_entire_packs = picking_ids[-1].picking_type_entire_packs
                    record.entire_package_detail_ids = picking_ids[-1].entire_package_detail_ids
                    record.show_lots_text = picking_ids[-1].show_lots_text
                    record.picking_show_validate = picking_ids[-1].show_validate
                else:
                    record.location_id = False
                    record.location_dest_id = False
                    record.picking_state = 'no'
                    record.picking_is_locked = True
                    record.picking_type_entire_packs = False
                    record.entire_package_detail_ids = False
                    record.show_lots_text = False
                    record.picking_show_validate = False
            else:
                record.location_id = False
                record.location_dest_id = False
                record.picking_state = 'no'
                record.picking_is_locked = True
                record.picking_type_entire_packs = False
                record.entire_package_detail_ids = False
                record.show_lots_text = False
                record.picking_show_validate = False

    @api.multi
    def button_picking_validate(self):
        for record in self:
            if record.picking_id:
                return record.picking_id.button_validate()
            else:
                raise UserError(_('At moment is not Picking for validations'))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    #move_line_ids = fields.One2many('stock.move.line', compute="_compute_move_line_ids", inverse="_set_move_line_ids", string='Stock Moves')
    move_id = fields.Many2one("stock.move", compute="_compute_move_id")
    lot_ids = fields.One2many('stock.production.lot', compute="_compute_lot_ids")
    picking_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')], compute="_compute_picking")
    move_state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], compute="_compute_picking")

    @api.multi
    def _compute_move_id(self):
        for record in self:
            if len(record.move_ids.ids) > 0 and len(record.order_id.picking_ids.ids) > 0:
                move_id = record.move_ids.filtered(lambda r: r.picking_id == record.order_id.picking_id)
                if len(move_id.ids) > 0:
                    record.move_id = move_id[-1]
                else:
                    record.move_id = False
            else:
                record.move_id = False

    #@api.multi
    #def _compute_move_line_ids(self):
    #    for record in self:
    #        record.move_line_ids = False
    #        if record.move_ids:
    #            for line in record.move_ids.move_line_ids:
    #                record.move_line_ids |= line

    #@api.multi
    #def _set_move_line_ids(self):
    #    for record in self:
    #        record.move_line_ids[record.move_line_ids.id] = record.move_line_ids if record.move_line_ids else False

    @api.multi
    def _compute_lot_ids(self):
        for record in self:
            record.lot_ids = False
            for move in record.move_ids:
                for line in move.move_line_ids:
                    if line and line.lot_id:
                        record.lot_ids |= line.lot_id

    @api.multi
    @api.depends('move_ids')
    def _compute_picking(self):
        for record in self:
            if len(record.move_ids.ids) > 0:
                record.picking_code = record.move_ids[0].picking_code
                record.move_state = record.move_ids[0].state
