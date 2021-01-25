# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stock_int_picking_ids = fields.One2many('stock.picking', compute="_compute_stock_int_picking_ids", inverse="_set_stock_int_picking_ids", search='_search_stock_int_picking_ids', string='Internal Transfers ref.')
    location_int_display_name = fields.Char("Int. source Picking Info", compute="_compute_location_int_display_name")
    location_dest_int_display_name = fields.Char("Int. dest Picking Info", compute="_compute_location_int_display_name")
    has_int_pick = fields.Boolean(compute="_compute_has_int_pick")

    api.multi
    def _compute_stock_int_picking_ids(self):
        for record in self:
            for line in record.order_line:
                record.stock_int_picking_ids |= line.stock_int_picking_ids

    api.multi
    def _set_stock_int_picking_ids(self):
        for record in self:
            #_logger.info("INFO %s" % record.stock_int_picking_ids.ids)
            if not record.stock_int_picking_ids:
                for line in record.order_line.filtered(lambda r: r.stock_int_picking_ids):
                    line.stock_int_picking_ids = False
            else:
                lines = record.order_line.filtered(lambda r: not r.stock_int_picking_ids)
                for line in lines:
                    line.update({'stock_int_picking_ids': record.stock_int_picking_ids.ids})

    api.multi
    def _compute_location_int_display_name(self):
        for record in self:
            for line in record.order_line:
                record.location_int_display_name = "-".join(x.name for x in line.stock_int_picking_ids.mapped('location_id'))
                record.location_dest_int_display_name = "-".join(x.name for x in line.stock_int_picking_ids.mapped('location_dest_id'))

    @api.multi
    def _compute_has_int_pick(self):
        for record in self:
            record.has_int_pick = len(record.stock_int_picking_ids.ids) > 0

    def _search_stock_int_picking_ids(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('stock_int_picking_ids', operator, value)]

    #@api.multi
    #def _prepare_invoice(self):
    #    invoice_vals = super(SaleOrder, self)._prepare_invoice()
    #    self.ensure_one()
    #    invoice_vals.update({
    #        'stock_int_picking_ids': self.stock_int_picking_ids.ids,
    #    })
    #    return invoice_vals

    def _prepare_sale_order_line_picking_data(self, line, picking):
        return {
            'order_id': self.id,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom.id,
            'product_uom_qty': line.product_qty,
            'stock_int_picking_ids': [picking.id],
        }

    def prepare_sale_order_line_picking_data(self, pickings):
        order_line = []
        for picking in pickings:
            for line in picking.move_lines:
                sale_order_line = self.env['sale.order.line'].new(self._prepare_sale_order_line_picking_data(line, picking))
                sale_order_line = sale_order_line._convert_to_write(sale_order_line._cache)
                order_line.append((0, 0, sale_order_line))
            #_logger.info("LINE FOR PUT %s" % order_line)
            return False, order_line

    @api.multi
    def action_import_picking(self):
        for record in self:
            if record.stock_int_picking_ids:
                record.order_line.update(record.prepare_sale_order_line_picking_data())


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_int_picking_ids = fields.Many2many('stock.picking', 'sale_order_line_int_picking_rel',
                                        'so_line_id', 'picking_line_id', string='Internal Transfers ref.')
    order_partner_shipping_id = fields.Many2one(related='order_id.partner_shipping_id', store=True, string='Customer')

    @api.multi
    def get_formview_id(self, access_uid=None):
        if self._context.get('force_tree'):
            return self.env.ref('sale_order_internal_picking.view_order_line_form').id
        else:
            return super(SaleOrderLine, self).get_formview_id(access_uid=access_uid)
