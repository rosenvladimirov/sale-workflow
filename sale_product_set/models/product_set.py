# Copyright 2019 dXFactory Ltd.
# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _name = 'product.set'
    _description = 'Product set'

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


    name = fields.Char(string='Name', help='Product set name', required=True, readonly=True, translate=True, states={'draft': [('readonly', False), ('required', False)]})
    code = fields.Char(string='Code', help='Product set code', required=True, readonly=True, translate=True, states={'draft': [('readonly', False), ('required', False)]})
    sale_ok = fields.Boolean('Can be Sold', default=True, help="Specify if the product can be selected in a sales order line.")
    purchase_ok = fields.Boolean('Can be Purchased')
    set_lines = fields.One2many('product.set.line', 'product_set_id', string="Products", readonly=True, copy=True, states={'draft': [('readonly', False)]})

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, default=lambda self: self._context.get('default_partner_id', False) or self.env['res.company']._company_default_get('product.set').partner_id)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True, help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', required=True, help="Delivery address for current sales order.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)]}, compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', readonly=True, string='Fiscal Position')
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env['res.company']._company_default_get('product.set'))

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')

    active = fields.Boolean(default=True, required=True)
    state = fields.Selection([
            ('draft','Draft'),
            ('progress', 'Progress'),
            ('freeze', 'Freeze'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Product set.\n"
             " * The 'Progress' status is used when user use the product set.\n"
             " * The 'Freeze' status is used when user freeze the product set.")
    state_next = fields.Selection([
                                ('draft','Draft'),
                                ('progress', 'Progress'),
                                ('freeze', 'Freeze'),
                                ], compute="_move_next_status", readonly=True, default='draft',
                                track_visibility='onchange', copy=False)

    type = fields.Selection([
                            ('boot', 'Purchase and Sale'),
                            ('sale', 'Sales'),
                            ('purchase', 'Purchase'),
                            ],
                            track_visibility='onchange', default='boot', copy=False)
    pricelist_item_ids = fields.One2many('product.pricelist.item', 'product_set_id', string='Pricelist Items', compute_sudo=True)
    has_pricelist = fields.Boolean(string="Has pricelist", compute="_compute_has_pricelist")

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    display_name = fields.Char(compute='_compute_display_name')
    print_name = fields.Char(compute='_compute_print_name')

    subtotal = fields.Boolean('Add subtotal', default=True)
    pagebreak = fields.Boolean('Add pagebreak')


    @api.depends('display_name')
    def _compute_print_name(self):
        for pset in self:
            pset.print_name = pset.display_name

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for pset in self:
            pset.display_name = "[%s] %s" % (pset.code, pset.name)

    @api.multi
    def _compute_has_pricelist(self):
        for record in self:
            record.has_pricelist = len(record.pricelist_item_ids.ids) > 0

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed on the SO.
        """
        for order in self:
            order.set_lines._compute_tax_id()


    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """
        self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, self.partner_shipping_id.id)
        return {}

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Invoice address
        - Delivery address
        """
        self.ensure_one()
        if not self.partner_id:
            self.update({
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        #_logger.info("Change partner info %s" % addr)
        values = {
            'fiscal_position_id': self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, addr['delivery']),
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        self.update(values)

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        self.ensure_one()
        #_logger.info("PRICELIST CHANGE %s:%s" % (self, self.pricelist_id))
        if self.pricelist_id:
            self.update({'currency_id': self.pricelist_id.currency_id.id})
            self.set_lines.update({'pricelist_id': self.pricelist_id.id, 'currency_id': self.currency_id.id})
            self.set_lines._compute_price_unit()

    @api.onchange('state')
    def onchange_state(self):
        if self.state and self.state == 'draft':
            product_set_unstate = self.search([('state', '=', 'draft')])
            product_set_unstate.write({'state': 'progress'})

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            if partner.parent_id:
                partner = partner.parent_id
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(ProductSet, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if ('name' and 'code') in vals:
            vals['state'] = 'progress'
        return super(ProductSet, self).write(vals)

    @api.multi
    def _move_next_status(self):
        for set in self:
            if set.state == 'draft':
                set.state_next = 'progress'
            elif set.state == 'progress':
                set.state_next = 'freeze'
            elif set.state == 'freeze':
                set.state_next = 'progress'

    @api.multi
    def action_use_product_kit(self):
        for set in self:
            if set.state in ['draft', 'freeze']:
                set.state = 'progress'
            elif set.state == 'progress':
                set.state = 'freeze'

    @api.multi
    def action_cancel_product_kit(self):
        for set in self:
            if set.state in ['progress', 'freeze']:
                set.state = 'draft'


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            domain = ['|', ('code', '=ilike', name + "%"), ('name', operator, search_name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        product_set = self.search(domain + args, limit=limit)
        return product_set.name_get()


    def name_get(self):
        res = []
        for set in self:
            res.append((set.id, "[%s] %s" % (set.code, set.name)))
        return res


class ProductSetLine(models.Model):
    _name = 'product.set.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'


    @api.depends('quantity', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.product_set_id.currency_id, line.quantity, product=line.product_id, partner=line.product_set_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.product_set_id.fiscal_position_id or line.product_set_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.product_set_id.partner_shipping_id) if fpos else taxes

    @api.depends('product_set_id', 'tax_id', 'company_id', 'product_id')
    def _compute_price_unit(self):
        for line in self:
            if line.product_id and line.pricelist_id and line.product_set_id.partner_id:
                line.update({'price_unit': 
                              self.env['account.tax']._fix_tax_included_price_company(line._get_display_price(line.product_id), line.product_id.taxes_id, line.tax_id, line.company_id)})
            else:
                line.update({'price_unit': 0.0})

    def _get_domain(self):
        if self.type == 'sale':
            return [('sale_ok', '=', True)]
        elif self.type == 'purchase':
            return [('purchase_ok', '=', True)]
        else:
            return ["|", ('sale_ok', '=', True), ('purchase_ok', '=', True)]


    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    product_set_id = fields.Many2one('product.set', string='Set', ondelete='cascade', copy=False)
    #partner_id = fields.Many2one(string='Partner', related="product_set_id.partner_id", store=True)
    company_id = fields.Many2one(related='product_set_id.company_id', string='Company')

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, compute_sudo=True, help="Pricelist for current sales order.")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Currency', store=True)

    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', domain=_get_domain)
    #product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Product template', readonly=True)

    # name = fields.Text(string='Description', required=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Monetary(compute='_compute_price_unit', string='Unit price', readonly=True, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)


    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        for rec in self:
            vals = {}
            if rec.product_tmpl_id:
                vals['product_id'] = rec.product_tmpl_id.product_variant_id.id
                self.update(vals)
                return {'domain': {'product_id': [('product_tmpl_id', '=', rec.product_tmpl_id.id)]}}
            else:
                return {'domain': {'product_id': []}}

    @api.multi
    def _get_display_price(self, product):
        PricelistItem = self.env['product.pricelist.item'].sudo()
        product_context = dict(self.env.context, partner_id=self.product_set_id.partner_id.id, date=fields.Date.context_today(self),
                                uom=self.product_uom.id, product_set_id=self.product_set_id.id, company_id=self.pricelist_id.company_id.id)
        final_price, rule_id = self.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.quantity or 1.0, self.product_set_id.partner_id)
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
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id, product_set_id=self.product_set_id).get_product_price_rule(product, qty, self.product_set_id.partner_id)
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
    @api.onchange('product_id')
    def product_id_change(self):
        self.ensure_one()
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['quantity'] = 1.0

        product = self.product_id.with_context(
            lang=self.product_set_id.partner_id.lang,
            partner=self.product_set_id.partner_id.id,
            quantity=vals.get('quantity') or self.quantity,
            date=fields.Date.context_today(self), ###
            pricelist=self.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        #name = product.name_get()[0][1]
        #if product.description_sale:
        #    name += '\n' + product.description_sale
        #vals['name'] = name

        self._compute_tax_id()
        self.update(vals)
        return result

#class ProductSetPricelist(models.Model):
#    _name = 'product.set.pricelist'
#    _description = 'Product set pricelists'

