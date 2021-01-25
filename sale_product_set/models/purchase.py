# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sets_line = fields.One2many('purchase.order.sets', 'order_id', string='Order Sets Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    has_sets = fields.Boolean(string="Has sets", compute="_compute_has_sets")
    print_sets = fields.Boolean("Ungroup by sets")
    product_set_id = fields.Many2one('product.set', related='sets_line.product_set_id', string='Product Set')

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.sets_line]) > 0

    @api.multi
    def order_lines_sets_layouted(self):
        self.ensure_one()
        if self.has_sets:
            report_pages_sets = [[]]
            for category, lines in groupby(self.order_line.sorted(lambda r: r.product_set_id, reverse=True), lambda l: l.product_set_id):
                # If last added category induced a pagebreak, this one will be on a new page
                if report_pages_sets[-1] and report_pages_sets[-1][-1]['pagebreak']:
                    report_pages_sets.append([])
                qty = sum(x.quantity for x in self.sets_line if x.product_set_id and category and x.product_set_id.id == category.id)
                unit_price = qty > 0.0 and category.subtotal/qty or category.subtotal
                # Append category to current report page
                report_pages_sets[-1].append({
                    'name': category and category.print_name or _('Uncategorized'),
                    'quantity': qty,
                    'price_unit': unit_price,
                    'subtotal': category and category.subtotal,
                    'pagebreak': category and category.pagebreak,
                    'lines': list(lines),
                    'pset': category,
                })
            return report_pages_sets
        return False

    def prepare_purchase_order_set_data(self, purchase_order_id, set, qty, total, split_sets=False):
        #_logger.info("LINE SET %s" % qty)
        set_lines = self.env['purchase.order.sets'].new({
            'order_id': purchase_order_id,
            'product_set_id': set.id,
            'quantity': qty,
            'price_unit': total/qty,
            'amount_total': total,
            'split_sets': split_sets,
        })
        line_sets_values = set_lines._convert_to_write(set_lines._cache)
        return line_sets_values

    def prepare_purchase_order_line_set_data(self, purchase_order_id, set, set_line, qty, set_id,
                                     max_sequence=0, old_qty=0, old_pset_qty=0, split_sets=False):
        #_logger.info("LINE SET LINE %s" % (set_line.quantity * qty)+old_qty)
        purchase_line = self.env['purchase.order.line'].new({
            'order_id': purchase_order_id,
            'product_id': set_line.product_id.id,
            'product_qty': (set_line.quantity * qty)+old_qty,
            'product_uom': set_line.product_id.uom_id.id,
            'sequence': max_sequence + set_line.sequence,
            'product_set_id': set.id,
            'set_id': set_id,
            'split_sets': split_sets,
            'pset_quantity': qty + old_pset_qty,
        })
        purchase_line.onchange_product_id()
        purchase_line.update({'product_qty': (set_line.quantity * qty)+old_qty})
        line_values = purchase_line._convert_to_write(purchase_line._cache)
        #_logger.info("SET LIENE END %s" % line_values)
        return line_values

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _order = 'order_id, product_set_id, sequence, id'


    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    set_id = fields.Many2one('purchase.order.sets', string='Product Sets', change_default=True, copy=True)
    split_sets = fields.Boolean("Splited set")
    pset_quantity = fields.Float(string='PSET Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)

    @api.model
    def _get_group_keys(self, order, line, picking=False):
        """Define the key that will be used to group. The key should be
        defined as a tuple of dictionaries, with each element containing a
        dictionary element with the field that you want to group by. This
        method is designed for extensibility, so that other modules can add
        additional keys or replace them by others."""
        key = ({'product_set_id': line.product_set_id},)
        return key

    @api.model
    def _first_picking_copy_vals(self, key, lines):
        """The data to be copied to new pickings is updated with data from the
        grouping key.  This method is designed for extensibility, so that
        other modules can store more data based on new keys."""
        vals = {'move_lines': []}
        for key_element in key:
            if 'product_set_id' in key_element.keys():
                vals['product_set_id'] = key_element['product_set_id'].id
        return vals

    @api.multi
    def _create_stock_moves(self, picking):
        """Group the receptions in one picking per group key"""
        moves = self.env['stock.move']
        # Group the order lines by group key
        order_lines = sorted(self, key=lambda l: l.product_set_id)
        product_set_groups = groupby(order_lines, lambda l: self._get_group_keys(l.order_id, l, picking=picking))

        first_picking = False
        # If a picking is provided, use it for the first group only
        if picking:
            first_picking = picking
            key, lines = next(product_set_groups)
            po_lines = self.env['purchase.order.line']
            for line in list(lines):
                po_lines += line
            moves += super(PurchaseOrderLine, po_lines)._create_stock_moves(first_picking)

        for key, lines in product_set_groups:
            # If a picking is provided, clone it for each key for modularity
            if picking:
                copy_vals = self._first_picking_copy_vals(key, lines)
                picking = first_picking.copy(copy_vals)
            po_lines = self.env['purchase.order.line']
            for line in list(lines):
                po_lines += line
            moves += super(PurchaseOrderLine, po_lines)._create_stock_moves(picking)
        return moves

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for re in res:
            re['product_set_id'] = self.product_set_id.id
        return res

    @api.multi
    def write(self, values):
        if 'name' in values and self.product_set_id and _('set-code:') not in values['name']:
            values['name'] = _("%s (set-code: %s)" % (values['name'], self.product_set_id.code))
        return super(PurchaseOrderLine, self).write(values)


class PurchaseOrderSets(models.Model):
    _name = 'purchase.order.sets'
    _description = 'Purchase Order Sets'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('purchase.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')

    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', required=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Sets Qty'), required=True, default=1.0)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    amount_total = fields.Monetary(string='Total')

    split_sets = fields.Boolean("Splited set")
    set_lines = fields.One2many('purchase.order.line', 'set_id', string='Purchase order lines', ondelete="cascade")

    @api.multi
    def unlink(self):
        purchase = self.env['purchase.order'].browse([self.order_id.id])
        purchase_lines = self.env['purchase.order.line'].browse(self.set_lines.ids)
        purchase_lines.unlink()
        purchase.order_line.invalidate_cache()
        return super(PurchaseOrderSets, self).unlink()
