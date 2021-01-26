# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sets_line = fields.One2many('account.invoice.sets', 'invoice_id', string='Invoice Sets Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Ungroup by sets")

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = [x.id for x in record.sets_line]

    @api.multi
    def is_order_lines_sets_layouted(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda l: l.product_set_id != False)

    @api.multi
    def order_lines_sets_layouted(self):
        #self.ensure_one()
        report_pages_sets = [[]]
        for inv in self:
            if inv.has_sets:
                for category, lines in groupby(inv.invoice_line_ids.sorted(lambda r: r.product_set_id.id, reverse=True), lambda l: l.product_set_id):
                    # If last added category induced a pagebreak, this one will be on a new page
                    if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                        report_pages_sets.append([])
                    qty = sum(x.quantity for x in inv.sets_line if x.product_set_id.id == category.id)
                    unit_price = qty > 0.0 and category.subtotal/qty or category.subtotal
                    split_sets = False
                    for sale in self.sets_line.filtered(lambda r: r.product_set_id == category).mapped('sale_order_ids'):
                        split_sets = sale.sets_line.filtered(lambda r: r.product_set_id == category)
                        if split_sets:
                            split_sets = split_sets[0].split_sets
                        else:
                            split_sets = False
                        if split_sets:
                            break
                    # Append category to current report page
                    report_pages_sets[-1].append({
                        'name': category and category.display_name or _('Uncategorized'),
                        'quantity': qty,
                        'price_unit': unit_price,
                        'subtotal': category and category.subtotal,
                        'pagebreak': category and category.pagebreak,
                        'lines': list(lines),
                        'pset': category,
                        'split_sets': split_sets,
                    })
                    #_logger.info("Category %s" % report_pages_sets)
                return report_pages_sets
            else:
                for category, lines in groupby(inv.invoice_line_ids, lambda l: l.layout_category_id):
                    # If last added category induced a pagebreak, this one will be on a new page
                    if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                        report_pages_sets.append([])
                    qty = sum(x.quantity for x in inv.invoice_line_ids if category and (x.layout_category_id and x.layout_category_id.id or False) == category.id)
                    subtotal = sum(x.price_subtotal for x in inv.invoice_line_ids if category and (x.layout_category_id and x.layout_category_id.id or False) == category.id)
                    unit_price = category and qty > 0.0 and subtotal/qty or 0.0
                    # Append category to current report page
                    report_pages_sets[-1].append({
                        'name': category and category.name or _('Uncategorized'),
                        'quantity': qty,
                        'price_unit': unit_price,
                        'subtotal': category and category.subtotal,
                        'pagebreak': category and category.pagebreak,
                        'lines': list(lines),
                        'pset': False,
                    })
        return report_pages_sets


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    _order = 'invoice_id, layout_category_id, product_set_id, sequence, id'

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)

    def _set_additional_fields(self, invoice):
        for sale_order_line in self.sale_line_ids:
            self.product_set_id = sale_order_line.product_set_id
            for order in sale_order_line.order_id:
                sets = order.sets_line
                for line in sets:
                    pset = invoice.sets_line.search([('invoice_id', '=', invoice.id), ('product_set_id', '=', line.product_set_id.id)])
                    #_logger.info("Sets %s:%s" % (line, pset))
                    if pset:
                        if order.id not in [x.id for x in pset.sale_order_ids]:
                            pset.write({'invoice_id': invoice.id, 'amount_total': line.amount_total, 'quantity': line.quantity, 'sale_order_ids': [(6, False, [x.id for x in pset.sale_order_ids] + [order.id])]})
                        else:
                            pset.write({'invoice_id': invoice.id, 'amount_total': line.amount_total, 'quantity': line.quantity})
                    else:
                        invoice.sets_line.create({'invoice_id': invoice.id, 'product_set_id': line.product_set_id.id, 'sale_order_ids': [(6, False, [order.id])], 'quantity': line.quantity, 'amount_total': line.amount_total})
        super(AccountInvoiceLine, self)._set_additional_fields(invoice)


class AccountInvoiceSets(models.Model):
    _name = 'account.invoice.sets'
    _description = 'Invoice Sets Lines'
    _order = 'invoice_id, sequence, id'

    @api.one
    @api.depends('amount_total', 'invoice_id.tax_line_ids',
        'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.amount_total
        taxes = False
        if self.invoice_id.tax_line_ids:
            for tax in self.invoice_id.tax_line_ids:
                taxes = tax.tax_id.compute_all(price, currency, 1, product=False, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
            sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            self.price_subtotal_signed = price_subtotal_signed * sign

    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one(related='invoice_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='invoice_id.company_id', string='Company', store=True, readonly=True)
    invoice_partner_id = fields.Many2one(related='invoice_id.partner_id', store=True, string='Customer')
    sale_order_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', string='Sales Order', readonly=True, copy=False)
    company_currency_id = fields.Many2one('res.currency', related='invoice_id.company_currency_id', readonly=True, related_sudo=False)

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', required=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Sets Qty'), required=True, default=1.0)
    amount_total = fields.Monetary(string='Total')

    price_subtotal = fields.Monetary(string='Amount',
        store=True, readonly=True, compute='_compute_price', help="Total amount without taxes")
    price_total = fields.Monetary(string='Amount',
        store=True, readonly=True, compute='_compute_price', help="Total amount with taxes")
    price_subtotal_signed = fields.Monetary(string='Amount Signed', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_price',
        help="Total amount in the currency of the company, negative for credit note.")
