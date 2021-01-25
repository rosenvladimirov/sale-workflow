# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    customer_po_ids = fields.Many2many('sale.order.customer', compute="_compute_customer_po_ids", string='Customer PO ref.')
    has_customer_po = fields.Boolean(compute="_compute_has_customer_po")

    @api.multi
    def _compute_has_customer_po(self):
        for record in self:
            record.has_customer_po = len([x.id for x in record.customer_po_ids]) > 0

    api.multi
    def _compute_customer_po_ids(self):
        for record in self:
            values = []
            for order_line in self.sale_line_ids:
                values.append(order_line.sale_order_line_ids.ids)
            record.customer_po_ids = (6, False, values)
