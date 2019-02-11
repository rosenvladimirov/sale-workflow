# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockPackageAdd(models.TransientModel):
    _name = 'stock.package.add'
    _rec_name = 'package_id'
    _description = "Wizard model to add package into a quotation"

    package_id = fields.Many2one('stock.quant.package', 'Package', help='The package containing this quant')

    @api.multi
    def add_package(self):
        """ Add package, multiplied by quantity in piking line """
        packing_id = self._context['active_id']
        if not packing_id:
            return
        order_obj = self.env['stock.picking']
        picking = order_obj.browse(packing_id)
        max_sequence = 0
        if picking.move_line_ids:
            max_sequence = max([line.sequence for line in picking.move_line_ids])
        stock_move_line = self.env['stock.move.line']
        for package in self.package_id:
            for quant in package.quant_ids:
                line = stock_move_line.create(order_obj.prepare_stock_move_line_package_data(packing_id, package, quant, max_sequence=max_sequence))

    def prepare_stock_move_line_package_data(self, packing_id, package, quant, max_sequence=0):
        stock_move_line = self.env['stock.move.line'].new({
            'picking_id': packing_id,
            'product_id': quant.product_id.id,
            'ordered_qty': quant.quantity,
            'product_uom_id': quant.product_uom_id.id,
            'sequence': max_sequence + set_line.sequence,
        })
        stock_move_line.product_id_change()
        line_values = stock_move_line._convert_to_write(stock_move_line._cache)
        return line_values
