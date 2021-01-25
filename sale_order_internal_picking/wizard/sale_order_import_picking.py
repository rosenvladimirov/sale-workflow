# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderPickingInternalImport(models.TransientModel):
    _name = 'sale.order.picking.internal.import'
    _rec_name = 'import_picking_id'
    _description = 'Put picking in sale order'
    _inherit = ['barcodes.barcode_events_mixin']

    import_picking_name = fields.Char('From picking')
    stock_int_picking_id = fields.Many2one('stock.picking', "Choice Picking", compute_sudo=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address')
    import_picking_id = fields.Many2one('stock.picking', 'From picking', ondelete='restrict', compute_sudo=True)
    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant', compute_sudo=True)

    def on_barcode_scanned(self, barcode):
        self.import_picking_name = barcode

    @api.multi
    def import_picking(self):
        """ Add package, multiplied by quantity in piking line """
        for record in self:
            so_id = self._context['active_id']
            if record.stock_int_picking_id:
                #_logger.info("PICKING %s" % record.stock_int_picking_id)
                import_picking = self.sudo().env['stock.picking'].browse([record.stock_int_picking_id.id])
            else:
                import_picking = self.sudo().env['stock.picking'].search([('name', '=', record.import_picking_name)])
            if not so_id:
                return
            sale_order = self.env['sale.order'].browse(so_id)
            if sale_order:
                    order, order_line = sale_order.prepare_sale_order_line_picking_data(import_picking)
                    if order:
                        sale_order.write(order)
                    if order_line:
                        sale_order.write({'order_line': order_line})
                    _logger.info("UPDATE %s:%s" % (order, order_line))
                    return {'type': 'ir.actions.act_window_close',}
            else:
                return {"type": "ir.actions.do_nothing",}
        return {"type": "ir.actions.do_nothing", }
