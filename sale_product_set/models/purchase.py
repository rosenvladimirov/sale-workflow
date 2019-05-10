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

    @api.multi
    def _compute_has_sets(self):
        for record in self:
            record.has_sets = len([x.id for x in record.sets_line]) > 0

    def prepare_purchase_order_set_data(self, purchase_order_id, set, qty, total, split_sets=False):
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
        purchase_line = self.env['purchase.order.line'].new({
            'order_id': purchase_order_id,
            'product_id': set_line.product_id.id,
            'product_uom_qty': (set_line.quantity * qty)+old_qty,
            'product_uom': set_line.product_id.uom_id.id,
            'sequence': max_sequence + set_line.sequence,
            'product_set_id': set.id,
            'set_id': set_id,
            'split_sets': split_sets,
            'pset_quantity': qty + old_pset_qty,
        })
        purchase_line.onchange_product_id()
        line_values = purchase_line._convert_to_write(purchase_line._cache)
        return line_values


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _order = 'order_id, product_set_id, sequence, id'


    product_set_id = fields.Many2one('product.set', string='Product Set', change_default=True, ondelete='restrict', copy=True)
    set_id = fields.Many2one('purchase.order.sets', string='Product Sets', change_default=True, copy=True)
    split_sets = fields.Boolean("Splited set")
    pset_quantity = fields.Float(string='PSET Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)


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

