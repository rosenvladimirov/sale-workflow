# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, Command

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stock_int_picking_ids = fields.One2many(
        'stock.picking',
        compute="_compute_stock_int_picking_ids",
        inverse="_set_stock_int_picking_ids",
        search='_search_stock_int_picking_ids',
        string='Internal Transfers ref.'
    )
    location_int_display_name = fields.Char(
        "Int. source Picking Info",
        compute="_compute_location_int_display_name"
    )
    location_dest_int_display_name = fields.Char(
        "Int. dest Picking Info",
        compute="_compute_location_int_display_name"
    )
    int_delivery_count = fields.Integer(string='Internal delivery Orders', compute='_get_int_delivery_count')

    @api.depends('stock_int_picking_ids')
    def _get_int_delivery_count(self):
        for order in self:
            order.int_delivery_count = len(order.stock_int_picking_ids)

    def _compute_stock_int_picking_ids(self):
        for record in self:
            for line in record.order_line:
                record.stock_int_picking_ids |= line.stock_int_picking_ids

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

    def _compute_location_int_display_name(self):
        for record in self:
            for line in record.order_line:
                record.location_int_display_name = "-".join(x.name for x in line.stock_int_picking_ids.mapped('location_id'))
                record.location_dest_int_display_name = "-".join(x.name for x in line.stock_int_picking_ids.mapped('location_dest_id'))

    @staticmethod
    def _search_stock_int_picking_ids(operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('stock_int_picking_ids', operator, value)]

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
                sale_order_line = self.env['sale.order.line'].default_get()
                sale_order_line.update(self._prepare_sale_order_line_picking_data(line, picking))
                order_line.append(Command.create(sale_order_line))
        return False, order_line

    def action_view_int_delivery(self):
        return self._get_action_int_view_picking(self.stock_int_picking_ids)

    def _get_action_int_view_picking(self, pickings):
        '''
        This function returns an action that displays existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        else:
            return True
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'internal')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        # View context from sale_renting `rental_schedule_view_form`
        cleaned_context = {k: v for k, v in self._context.items() if k != 'form_view_ref'}
        action['context'] = dict(cleaned_context, default_partner_id=self.partner_id.id, default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name, default_group_id=picking_id.group_id.id)
        return action


