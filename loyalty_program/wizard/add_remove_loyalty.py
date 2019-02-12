# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSetAdd(models.TransientModel):
    _name = 'loyalty.sale.add'
    _rec_name = 'partner_id'
    _description = "Wizard model to add sele order into a loyalty"

    partner_id = fields.Many2one('res.partner', string='Partner')
    split_loyalty = fields.Boolean("Split sales")


    @api.multi
    def sale_add_loyalty(self):
        so_id = self._context['active_id']
        so_ids = so_id and [so_id] or self._context['active_ids']

        if not so_ids:
            return
        order_obj = self.env['sale.order']
        so = order_obj.browse(so_ids)
        for sale in so:
            if self.partner_id and sale.partner_id == self.partner_id:
                
