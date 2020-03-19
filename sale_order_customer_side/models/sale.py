# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order"

    customer_po_ids = fields.One2many('sale.order.customer', compute="_compute_customer_po_ids", inverse="_set_customer_po_ids", string='Customer PO ref.')

    api.multi
    def _compute_customer_po_ids(self):
        for record in self:
            for line in record.order_line:
                record.customer_po_ids |= line.customer_po_ids

    api.multi
    def _set_customer_po_ids(self):
        for record in self:
            if not record.customer_po_ids: continue
            lines = record.order_line.filtedred(lambda r: not r.customer_po_ids)
            for line in lines:
                line.update({'customer_po_ids': (6, False, record.customer_po_ids.ids)})

    #@api.multi
    #def _prepare_invoice(self):
    #    invoice_vals = super(SaleOrder, self)._prepare_invoice()
    #    self.ensure_one()
    #    invoice_vals.update({
    #        'customer_po_ids': self.customer_po_ids.ids,
    #    })
    #    return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    customer_po_ids = fields.Many2many('sale.order.customer', 'sale_order_line_cust_po_rel',
                                        'so_line_id', 'customer_so_line_id', string='Customer PO ref.')

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({'customer_po_ids': self.customer_po_ids.ids})
        return values


class SaleOrderCustomer(models.Model):
    _name = "sale.order.customer"
    _description = "PO reference from customer"

    sale_order_line_ids = fields.Many2many('sale.order.customer', 'sale_order_line_cust_po_rel',
                                            'customer_so_line_id', 'so_line_id', string='Customer PO ref.')
    date_po = fields.Date('Date PO')
    name = fields.Char('Name PO')
    description = fields.Text('Description')
    partner_id = fields.Many2one('res.partner', 'Customer')

    @api.depends('requested_date', 'name')
    def name_get(self):
        res = []
        for ref in self:
            res.append((ref.id, "[%s] %s" % (ref.date_po, ref.name)))
        return res