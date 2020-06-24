# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderImportPurchaseOrder(models.TransientModel):
    _name = 'sale.order.import.purchase.order'
    _rec_name = 'import_po_id'
    _description = 'Import from purchase order in sale order'
    _inherit = ['barcodes.barcode_events_mixin']

    import_po_name = fields.Char('From purchase order', required=True)
    import_po_id = fields.Many2one('stock.picking', 'From purchase order', ondelete='restrict', compute_sudo=True)
    sale_order_id = fields.Many2one('sale.order', 'Sale order', compute_sudo=True)

    def on_barcode_scanned(self, barcode):
        self.import_po_name = barcode

    @api.multi
    def import_purchase_order(self):
        """ Add package, multiplied by quantity in piking line """
        so_id = self._context['active_id']
        import_po = self.sudo().env['purchase.order'].search([('name', '=', self.import_po_name)])
        if not so_id:
            so = self.sale_order_id
        else:
            so = self.env['sale.order'].browse(so_id)
        if import_po:
            if so.state == 'draft':
                res = so.prepare_sale_order_line_data(so, import_po)
                _logger.info("IMPORT %s:%s:%s" % (so, import_po, res))
                if res:
                 so.order_line = res
        return {'type': 'ir.actions.act_window_close'}
