# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float('Quantity On Hand', compute="_compute_qty_available")

    @api.multi
    def _compute_qty_available(self):
        for record in self:
            if record.product_id and record.product_uom:
                record.qty_available = record.product_id.uom_id._compute_quantity(record.product_id.qty_available,
                                                                                  record.product_uom)

    def _check_routing(self):
        is_available = super(SaleOrderLine, self)._check_routing()
        if is_available:
            is_available = True
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            message = _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                      (self.product_uom_qty, self.product_uom.name, product.virtual_available, product.uom_id.name,
                       self.order_id.warehouse_id.name)
            # We check if some products are available in other warehouses.
            if float_compare(product.virtual_available, self.product_id.virtual_available,
                             precision_digits=precision) == -1:
                message += _('\nThere are %s %s available accross all warehouses.') % \
                           (self.product_id.virtual_available, product.uom_id.name)

            self.env.user.notify_info(message)
        return is_available

