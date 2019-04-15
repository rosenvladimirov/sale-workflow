# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProductSetAdd(models.TransientModel):
    _name = 'product.set.add'
    _rec_name = 'product_set_id'
    _description = "Wizard model to add product set into a quotation"

    def _get_default(self):
        values = []
        if self._context.get('set_line_ids', False):
            for line in self.env['sale.order.line'].browse([x[1] for x in self._context.get('set_line_ids')]):
                values.append((0, False, {
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'product_set_id': line.product_set_id.id,
                    'sequence': line.sequence,
                    'split_sets': line.split_sets,
                    'set_lines': line.id,
                }))
        #_logger.info("Import lines %s:%s" % (self._context.get('set_line_ids'), values))
        return values if len(values) > 0 else False

    product_set_id = fields.Many2one('product.set', 'Product set', required=True, domain="[('state', '=', 'progress'), ('active', '=', True)]")
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', 'Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency")

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    amount_total = fields.Monetary(string='Total', related="product_set_id.amount_total")
    split_sets = fields.Boolean("Split set")
    edit_sets = fields.Boolean("Edit set")
    set_lines = fields.One2many('product.set.add.line', 'set_id', string="Products", copy=True, default=_get_default)


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    @api.multi
    @api.onchange('product_set_id')
    def onchange_product_set_id(self):
        for rec in self:
            if not rec.edit_sets:
                #rec.set_lines.unlink()
                values = []
                for line in rec.product_set_id.set_lines:
                    #_logger.info("Line %s:%s" % (line, rec.set_lines))
                    values.append((0, False, {
                        'product_tmpl_id': line.product_tmpl_id.id,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'product_set_id': line.product_set_id.id,
                        'sequence': line.sequence,
                        }))
                #_logger.info("Values %s:%s" % (values, rec.product_set_id.set_lines))
                rec.update({'set_lines': values})
                self.set_lines.onchange_product_tmpl_id()

    @api.multi
    def sale_add_set(self):
        """ Add product set, multiplied by quantity in sale order line """
        so_id = self._context['active_id']
        if self._context.get('order_id', False):
            so_id = self._context['order_id']
        if not so_id:
            return
        order_obj = self.env['sale.order']
        so = order_obj.browse(so_id)
        max_sequence = 0
        if so.order_line:
            max_sequence = max([line.sequence for line in so.order_line])
        sale_order_line = self.env['sale.order.line']
        set_lines = self.env['sale.order.sets']
        for set in self.product_set_id:
            amount_untaxed = set.amount_untaxed
            set_old = set_lines.search(
                [('order_id', '=', so_id), ('product_set_id', '=', set.id), ('split_sets', '=', self.split_sets)])
            if set_old and not self.split_sets:
                if self.edit_sets:
                    quantity = 0.0
                    amount_untaxed_old = 0.0
                else:
                    quantity = sum(ss.quantity for ss in set_old)
                    amount_untaxed_old = sum(ss.amount_total for ss in set_old)
                set_old.write(order_obj.prepare_sale_order_set_data(so_id, set, self.quantity + quantity,
                                                                    amount_untaxed_old + self.pricelist_id.currency_id.round(amount_untaxed),
                                                                    split_sets=self.split_sets))
            else:
                set_old = set_lines.create(order_obj.prepare_sale_order_set_data(so_id, set, self.quantity,
                                                                                 self.pricelist_id.currency_id.round(
                                                                                     amount_untaxed),
                                                                                 split_sets=self.split_sets))
            amount_untaxed = 0.0
            for set_line in self.set_lines:
                if self.edit_sets:
                    _logger.info("Sale line %s:%s" % (so_id, set_line.set_lines))
                    line = sale_order_line.search([('product_id', '=', set_line.product_id.id), ('product_set_id', '=', set_line.product_set_id.id), ('id', 'in', [x[1] for x in self._context.get('set_line_ids')])], limit=1)
                    if line:
                        line.write(order_obj.prepare_sale_order_line_set_data(line.order_id.id, set, set_line, self.quantity, set_old.id,
                                                                              max_sequence=max_sequence,
                                                                              split_sets=self.split_sets))
                    else:
                        line = sale_order_line.create(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity, set_old.id, 
                                                                              max_sequence=max_sequence, 
                                                                              split_sets=self.split_sets))

                else:
                    line = sale_order_line.create(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity, set_old.id, max_sequence=max_sequence, split_sets=self.split_sets))
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                amount_untaxed += \
                line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id,
                                        partner=line.order_id.partner_shipping_id)['total_excluded']
            set_old.write({'price_unit': amount_untaxed/self.quantity,
                           'amount_total': amount_untaxed})

    @api.multi
    def purchase_add_set(self):
        """ Add product set, multiplied by quantity in purchase order line """
        po_id = self._context['active_id']
        if not po_id:
            return
        order_obj = self.env['purchase.order']
        po = order_obj.browse(po_id)
        max_sequence = 0
        if po.order_line:
            max_sequence = max([line.sequence for line in po.order_line])
        purchase_order_line = self.env['purchase.order.line']
        set_lines = self.env['purchase.order.sets']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = purchase_order_line.create(order_obj.prepare_purchase_order_line_set_data(po_id, set, set_line, self.quantity, max_sequence=max_sequence))
                price = line.price_unit
                amount_untaxed += line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)['total_excluded']
            set_old = set_lines.search([('order_id', '=', po_id), ('product_set_id', '=', set.id)])
            if set_old and not self.split_sets:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write({
                        'order_id': po_id,
                        'product_set_id': set.id,
                        'quantity': self.quantity+set_old.quantity,
                        'amount_total': set_old.amount_total+self.pricelist_id.currency_id.round(amount_untaxed),
                        })
            else:
                set_lines.create(order_obj.prepare_purchase_order_set_data(po_id, set, self.quantity, self.pricelist_id.currency_id.round(amount_untaxed)))

    @api.multi
    def picking_add_set(self):
        """ Add product set, multiplied by quantity in picking move line """
        picking_id = self._context['active_id']
        if not picking_id:
            return
        picking = self.env['stock.picking'].browse(picking_id)
        for set in self.product_set_id:
            for set_line in self.set_lines:
                picking.move_lines = picking.prepare_stock_move_line_pset_data(picking_id, set_line, self.quantity)

class ProductSetLine(models.TransientModel):
    _name = 'product.set.add.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'

    set_id = fields.Many2one('product.set.add', string='Product Set', ondelete="cascade")
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    product_uom = fields.Many2one('product.uom', related="product_id.uom_id", string='Unit of Measure', readonly=True)

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete="restrict")
    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)

    split_sets = fields.Boolean("Splited set")
    set_lines = fields.Many2one('sale.order.line', string="Order lines")


    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_id = rec.product_tmpl_id.product_variant_id.id
                return {'domain': {'product_id': [('product_tmpl_id', '=', rec.product_tmpl_id.id)]}}
