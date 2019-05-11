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
        picking = self.env['stock.picking'].browse(packing_id)
        if picking:
            picking.move_lines = picking.prepare_stock_move_line_package_data(picking.id, self.package_id)
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.package.add',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self._context['active_id'],
                'target': 'new',
                }