# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sets_line = fields.One2many('sale.order.sets', 'order_id', string='Order Sets Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Ungroup by sets")
    product_set_id = fields.Many2one('product.set', related='sets_line.product_set_id', string='Product Set')

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len(record.sets_line) > 0

    @api.multi
    def order_lines_layouted(self):
        return self.order_lines_sets_layouted()

    @api.multi
    def order_lines_sets_layouted(self):
        self.ensure_one()
        if self.has_sets:
            report_pages_sets = [[]]
            for category, lines in groupby(self.order_line.sorted(lambda r: r.product_set_id, reverse=True), lambda l: l.product_set_id):
                #_logger.info("LINES %s" % list(lines))
                # If last added category induced a pagebreak, this one will be on a new page
                if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    report_pages_sets.append([])
                qty = sum(x.quantity for x in self.sets_line if x.product_set_id and category and x.product_set_id.id == category.id)
                unit_price = qty > 0.0 and category.subtotal/qty or category.subtotal
                split_sets = self.sets_line.filtered(lambda r: r.product_set_id == category)
                if split_sets:
                    split_sets = split_sets[0].split_sets
                else:
                    split_sets = False
                # Append category to current report page
                report_pages_sets[-1].append({
                        'name': category and category.print_name or _('Uncategorized'),
                        'quantity': qty,
                        'price_unit': unit_price,
                        'subtotal': category and category.subtotal,
                        'pagebreak': category and category.pagebreak,
                        'lines': list(lines),
                        'vat':  ', '.join(map(lambda x: (x.description or x.name), [l.tax_id for l in list(lines)])),
                        'pset': category,
                        'split_sets': split_sets,
                    })
            #_logger.info("LINES %s" % report_pages_sets)
            return report_pages_sets
        else:
            report_pages_sets = [[]]
            for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
                # If last added category induced a pagebreak, this one will be on a new page
                if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    report_pages_sets.append([])
                #_logger.info("CATEGORY %s:%s" % (category, lines))
                qty = sum(x.product_uom_qty for x in self.order_line if category and (x.layout_category_id and x.layout_category_id.id or False) == category.id)
                subtotal = sum(x.price_subtotal for x in self.order_line if category and (x.layout_category_id and x.layout_category_id.id or False) == category.id)
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

    def prepare_sale_order_set_data(self, sale_order_id, set, qty, total, split_sets=False):
        set_lines = self.env['sale.order.sets'].new({
            'order_id': sale_order_id,
            'product_set_id': set.id,
            'quantity': qty,
            'price_unit': total/qty,
            'amount_total': total,
            'split_sets': split_sets,
        })
        line_sets_values = set_lines._convert_to_write(set_lines._cache)
        return line_sets_values

    def prepare_sale_order_line_set_data(self, sale_order_id, set, set_line, qty, set_id,
                                     max_sequence=0, old_qty=0, old_pset_qty=0, split_sets=False):
        sale_line = self.env['sale.order.line'].new({
            'order_id': sale_order_id,
            'product_id': set_line.product_id.id,
            'product_uom_qty': (set_line.quantity * qty)+old_qty,
            'product_uom': set_line.product_id.uom_id.id,
            'sequence': max_sequence + set_line.sequence,
            'product_set_id': set.id,
            'set_id': set_id,
            'split_sets': split_sets,
            'pset_quantity': qty+old_pset_qty,
        })
        sale_line.product_id_change()
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        invoice_vals.update({
            'print_sets': self.print_sets,
        })
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id, layout_category_id, product_set_id, sequence, id'


    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    set_id = fields.Many2one('sale.order.sets', string='Product Sets', change_default=True, copy=True)
    split_sets = fields.Boolean("Splited set")
    pset_quantity = fields.Float(string='PSET Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id, product_set_id=self.product_set_id.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id, product_set_id=self.product_set_id.id)
        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        for record in res:
            if 'product_set_id' in vals and not self._context.get('block_pset', False):
                update = record.order_id.order_line.filtered(lambda r: r.product_set_id.id == vals['product_set_id'] and not r.set_id)
                #_logger.info("PSET NEW %s:%s" % (update, vals))
                if update:
                    pset = {}
                    for line in record.order_id.order_line:
                        if line.product_set_id:
                            qty = sum([x.quantity for x in
                                       line.product_set_id.set_lines.filtered(lambda r: r.product_id == line.product_id)])
                            qty = qty < 1 and 1.0 or line.product_uom_qty/qty
                            if not pset.get(line.product_set_id):
                                pset[line.product_set_id] = {'amount_total': 0.0, 'quantity': qty < 1 and 1.0 or qty}
                            pset[line.product_set_id]['amount_total'] += line.price_subtotal
                    if pset:
                        for k, line in pset.items():
                            set_line = record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)
                            if not set_line:
                                record.order_id.sets_line = [(0, False, {'order_id': record.order_id.id,
                                                                       'product_set_id': k.id,
                                                                       'amount_total': line['amount_total'],
                                                                       'quantity': line['quantity'],
                                                                       'price_unit': line['amount_total'] / line['quantity']})]
                                record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id).write(
                                    {'set_id': record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)[0].id,
                                     'pset_quantity': line['quantity']})
                            else:
                                set_line.write({'amount_total': line['amount_total'], 'quantity': line['quantity'],
                                                 'price_unit': line['amount_total'] / line['quantity']})
                                if update:
                                    record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id).write(
                                        {'set_id': record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)[0].id,
                                         'pset_quantity': line['quantity']})
        return res

    @api.multi
    def write(self, values):
        result = super(SaleOrderLine, self).write(values)
        #_logger.info("PSET %s" % values)
        updated = True
        if 'product_set_id' in values and not self._context.get('block_pset', False):
            for record in self:
                pset = {}
                for line in record.order_id.order_line:
                    if line.product_set_id:
                        qty = sum([x.quantity for x in
                                   line.product_set_id.set_lines.filtered(lambda r: r.product_id == line.product_id)])
                        qty = qty < 1 and 1.0 or line.product_uom_qty/qty
                        if not pset.get(line.product_set_id):
                            pset[line.product_set_id] = {'amount_total': 0.0, 'quantity': qty < 1 and 1.0 or qty}
                        pset[line.product_set_id]['amount_total'] += line.price_subtotal
                if pset:
                    updated = False
                    for k, line in pset.items():
                        set_line = record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)
                        if not set_line:
                            record.order_id.sets_line = [(0, False, {'order_id': record.order_id.id,
                                                                   'product_set_id': k.id,
                                                                   'amount_total': line['amount_total'],
                                                                   'quantity': line['quantity'],
                                                                   'price_unit': line['amount_total'] / line['quantity']})]
                            record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id).write(
                                {'set_id': record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)[0].id})
                        else:
                            set_line.write({'amount_total': line['amount_total'], 'quantity': line['quantity'],
                                             'price_unit': line['amount_total'] / line['quantity']})

        if 'price_unit' in values and not self._context.get('block_pset', False) and updated:
            for record in self:
                pset = {}
                for line in record.order_id.order_line:
                    if line.product_set_id:
                        qty = sum([x.quantity for x in
                                   line.product_set_id.set_lines.filtered(lambda r: r.product_id == line.product_id)])
                        qty = qty < 1 and 1.0 or line.product_uom_qty/qty
                        if not pset.get(line.product_set_id):
                            pset[line.product_set_id] = {'amount_total': 0.0, 'quantity': qty < 1 and 1.0 or qty}
                        pset[line.product_set_id]['amount_total'] += line.price_subtotal
                        #_logger.info("SUM %s" % pset[line.product_set_id])
                #_logger.info("PSET %s" % pset)
                if pset:
                    for k, line in pset.items():
                        set_lines = record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)
                        if not set_lines:
                            record.order_id.sets_line = [(0, False, {'order_id': record.order_id.id,
                                                                   'product_set_id': k.id,
                                                                   'amount_total': line['amount_total'],
                                                                   'quantity': line['quantity'],
                                                                   'price_unit': line['amount_total'] / line['quantity']})]
                            record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id).write(
                                {'set_id': record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)[
                                    0].id})
                        else:
                            for set_line in set_lines:
                                qty = set_line.quantity > 0 and set_line.quantity or 1.0
                                set_line.write({'amount_total': line['amount_total'],
                                                'price_unit': line['amount_total'] / qty})
                            if record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id and not r.set_id):
                                record.order_id.order_line.filtered(lambda r: r.product_set_id.id == k.id).write(
                                    {'set_id': record.order_id.sets_line.filtered(lambda r: r.product_set_id.id == k.id)[0].id})
        return result

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({'product_set_id': self.product_set_id.id})
        return values


class SaleOrderSets(models.Model):
    _name = 'sale.order.sets'
    _description = 'Sales Order Sets'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', required=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Sets Qty'), required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    amount_total = fields.Monetary(string='Total')

    split_sets = fields.Boolean("Splited set")
    set_lines = fields.One2many('sale.order.line', 'set_id', string='Sele order lines', ondelete="cascade")

    @api.model
    def create(self, vals):
        result = super(SaleOrderSets, self).create(vals)
        if 'amount_total' not in vals:
            order_obj = self.env['sale.order'].sudo()
            sale_order_line = self.env['sale.order.line'].sudo()
            product_set = self.env['product.set'].browse(vals['product_set_id'])
            for set in product_set:
                amount_untaxed = 0.0
                for set_line in product_set.set_lines:
                    line = sale_order_line.with_context(dict(self._context, block_pset=True)).create(order_obj.prepare_sale_order_line_set_data(vals['order_id'], set, set_line, self.quantity, result.id))
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    amount_untaxed += \
                    line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)['total_excluded']
                result.write({'amount_total': amount_untaxed, 'price_unit': amount_untaxed/result.quantity})
        return result

    @api.multi
    def unlink(self):
        sale = self.env['sale.order'].browse([self.order_id.id])
        sale_lines = self.env['sale.order.line'].browse(self.set_lines.ids)
        sale_lines.unlink()
        sale.order_line.invalidate_cache()
        return super(SaleOrderSets, self).unlink()

    @api.depends('product_set_id', 'order_id')
    def name_get(self):
        res = []
        for ref in self:
            res.append((ref.id, "%s/%s" % (ref.order_id.name, ref.product_set_id and ref.product_set_id.display_name or 'not sets')))
        return res

    #@api.onchange('quantity')
    #def onchange_quantity(self):
    #    self.ensure_one()
    #    if self.quantity:
    #        total = 0.0
    #        for line in self.set_lines:
    #            quantity = sum(x.quantity for x in self.product_set_id.mapped('set_lines').filtered(lambda r: r.product_id.id == line.product_id.id))
    #            line.update({'product_uom_qty': self.quantity*quantity})
    #            total += line.price_subtotal
    #        self.update({'amount_total': total, 'price_unit': total/self.quantity})
