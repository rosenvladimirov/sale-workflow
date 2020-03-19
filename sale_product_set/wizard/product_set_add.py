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
                    'pricelist_id': line.order_id.pricelist_id.id,
                    'quantity': line.product_uom_qty,
                    'product_set_id': line.product_set_id.id,
                    'sequence': line.sequence,
                    'split_sets': line.split_sets,
                    'set_lines': line.id,
                }))
        #_logger.info("Import lines %s:%s" % (self._context.get('set_line_ids'), values))
        return values if len(values) > 0 else False

    @api.depends('set_lines.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for productset in self:
            amount_untaxed = amount_tax = 0.0
            for line in productset.set_lines:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            productset.update({
                'amount_untaxed': productset.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': productset.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    product_set_id = fields.Many2one('product.set', 'Product set', required=True, domain="[('state', '=', 'progress'), ('active', '=', True)]")
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', help="Delivery address for current sales order.")
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')

    company_id = fields.Many2one('res.company', 'Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency")

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    #amount_total = fields.Monetary(string='Total', related="product_set_id.amount_total")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')

    split_sets = fields.Boolean("Split set")
    edit_sets = fields.Boolean("Edit set")
    set_lines = fields.One2many('product.set.add.line', 'set_id', string="Products", copy=True, default=_get_default)


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self._context.get('default_pricelist_id', False):
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
                        'pricelist_id': self.pricelist_id,
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
                    #_logger.info("Sale line %s:%s" % (so_id, set_line.set_lines))
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
            amount_untaxed = set.amount_untaxed
            set_old = set_lines.search(
                [('order_id', '=', po_id), ('product_set_id', '=', set.id), ('split_sets', '=', self.split_sets)])
            if set_old and not self.split_sets:
                if self.edit_sets:
                    quantity = 0.0
                    amount_untaxed_old = 0.0
                else:
                    quantity = sum(ss.quantity for ss in set_old)
                    amount_untaxed_old = sum(ss.amount_total for ss in set_old)
                set_old.write(order_obj.prepare_purchase_order_set_data(po_id, set, self.quantity + quantity,
                                                                    amount_untaxed_old + self.pricelist_id.currency_id.round(amount_untaxed),
                                                                    split_sets=self.split_sets))
            else:
                set_old = set_lines.create(order_obj.prepare_purchase_order_set_data(po_id, set, self.quantity,
                                                                                 self.pricelist_id.currency_id.round(amount_untaxed),
                                                                                 split_sets=self.split_sets))
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                if self.edit_sets:
                    line = purchase_order_line.search([('product_id', '=', set_line.product_id.id), ('product_set_id', '=', set_line.product_set_id.id), ('id', 'in', [x[1] for x in self._context.get('set_line_ids')])], limit=1)
                    if line:
                        line.write(order_obj.prepare_purchase_order_line_set_data(line.order_id.id, set, set_line, self.quantity, set_old.id,
                                                                              max_sequence=max_sequence,
                                                                              split_sets=self.split_sets))
                    else:
                        line = purchase_order_line.create(order_obj.prepare_purchase_order_line_set_data(po_id, set, set_line, self.quantity, set_old.id,
                                                                              max_sequence=max_sequence,
                                                                              split_sets=self.split_sets))
                else:
                    line = purchase_order_line.create(order_obj.prepare_purchase_order_line_set_data(po_id, set, set_line, self.quantity, set_old.id,
                                                                                     max_sequence=max_sequence,
                                                                                     split_sets=self.split_sets))
                    price = line.price_unit
                    amount_untaxed += \
                        line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                                product=line.product_id,
                                                partner=line.order_id.partner_id)['total_excluded']
                set_old.write({'price_unit': amount_untaxed / self.quantity,
                               'amount_total': amount_untaxed})

    @api.multi
    def picking_add_set(self):
        """ Add product set, multiplied by quantity in picking move line """
        picking_id = self._context['active_id']
        if not picking_id:
            return
        picking = self.env['stock.picking'].browse(picking_id)
        #for set in self.product_set_id:
            #for set_line in self.set_lines:
        picking.move_lines = picking.with_context(dict(self._context, force_validate=True)).prepare_stock_move_line_pset_data(picking_id, self.set_lines, self.quantity)
        picking.action_confirm()
        picking.action_assign()

class ProductSetLine(models.TransientModel):
    _name = 'product.set.add.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.set_id.fiscal_position_id or line.set_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.set_id.partner_shipping_id) if fpos else taxes

    set_id = fields.Many2one('product.set.add', string='Product Set', ondelete="cascade")
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product')

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    product_uom = fields.Many2one('product.uom', related="product_id.uom_id", string='Unit of Measure', readonly=True)
    price_unit = fields.Monetary(compute='_compute_price_unit', string='Unit price', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete="restrict")
    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)
    company_id = fields.Many2one(related='set_id.company_id', string='Company')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Currency', store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    split_sets = fields.Boolean("Splited set")
    set_lines = fields.Many2one('sale.order.line', string="Order lines")

    @api.depends('set_id', 'tax_id', 'company_id', 'product_id')
    def _compute_price_unit(self):
        for line in self:
            #_logger.info("COMPUTE PRICE %s:%s:%s" % (line.product_id, line.pricelist_id, line.set_id.partner_id))
            if line.product_id and line.pricelist_id and line.set_id.partner_id:
                line.update({'price_unit':
                              self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(line.product_id), line.product_id.taxes_id, line.tax_id, line.company_id)})
            else:
                line.update({'price_unit': 0.0})

    @api.depends('quantity', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.set_id.currency_id, line.quantity, product=line.product_id, partner=line.set_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _get_display_price(self, product):
        PricelistItem = self.env['product.pricelist.item'].sudo()
        product_context = dict(self.env.context, partner_id=self.set_id.partner_id.id, date=fields.Date.context_today(self),
                                uom=self.product_uom.id, product_set_id=self.product_set_id.id, company_id=self.pricelist_id.company_id.id)
        final_price, rule_id = self.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.quantity or 1.0, self.set_id.partner_id)
        base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.quantity or 1.0, self.product_uom, self.pricelist_id.id)
        if currency_id != self.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price, self.pricelist_id.currency_id)
        if rule_id and PricelistItem.browse(rule_id).compute_price == 'fixed':
            return final_price
        elif rule_id and PricelistItem.browse(rule_id).price_discount >= 0.0:
            return min(base_price, final_price)
        else:
            return max(base_price, final_price)

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        PricelistItem = self.env['product.pricelist.item'].sudo()
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id, product_set_id=self.product_set_id).get_product_price_rule(product, qty, self.set_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0
        #_logger.info("PRICELIST GET CURRENCY RODUCT:%s:CURRENCY:%s:%s:%s:%s" % (product_currency.name, product.company_id.name, currency_id.name, self.env.user.company_id.name, self.env.user.company_id.currency_id.name))
        return product[field_name] * uom_factor * cur_factor, currency_id.id

    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_id = rec.product_tmpl_id.product_variant_id.id
                self._compute_tax_id()
                self._compute_price_unit()
                return {'domain': {'product_id': [('product_tmpl_id', '=', rec.product_tmpl_id.id)]}}
