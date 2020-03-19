# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.set'

    competitor_ids = fields.One2many('product.set.competitorinfo', 'product_set_id', 'Competitors')

    def _get_competitorinfo_pricelist_price(
            self, rule, date=None, quantity=None):
        return self.product_tmpl_id._get_competitorinfo_pricelist_price(
            rule, date=date, quantity=quantity, product_id=self.id)

    def price_compute(self, price_type, uom=False, currency=False,
                      company=False):
        """Return dummy not falsy prices when computation is done from supplier
        info for avoiding error on super method. We will later fill these with
        correct values.
        """
        if price_type == 'competitorinfo':
            return dict.fromkeys(self.ids, 1.0)
        return super().price_compute(
            price_type, uom=uom, currency=currency, company=company)


class CompetitorInfo(models.Model):
    _name = "product.set.competitorinfo"
    _description = "Information about a product set competitor"
    _order = 'sequence, min_qty desc, price'

    name = fields.Many2one(
        'res.partner', 'Competitor',
        domain=[('competitor', '=', True)], ondelete='cascade', required=True,
        help="Competitor of this product")
    product_name = fields.Char(
        'Competitor Product Name',
        help="This competitor's product name will be used when printing a request for quotation. Keep empty to use the internal one.")
    product_code = fields.Char(
        'Competitor Product Code',
        help="This competitor's product code will be used when printing a request for quotation. Keep empty to use the internal one.")
    sequence = fields.Integer(
        'Sequence', default=1, help="Assigns the priority to the list of product competitor.")
    min_qty = fields.Float(
        'Minimal Quantity', default=0.0, required=True,
        help="The minimal quantity to purchase from this competitor, expressed in the competitor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help="Pricelist for current sales order.")
    partner_id = fields.Many2one('res.partner', string='Customer')
    price_stable = fields.Float(
        'Stable Price', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The stable price to sell a product")
    price = fields.Float(
        'Price', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The price to purchase a product")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.user.company_id.id, index=1)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    date_start = fields.Date('Start Date', help="Start date for this competitor price")
    date_end = fields.Date('End Date', help="End date for this competitor price")
    product_set_id = fields.Many2one('product.set', string='Product Set', help="If not set, the competitor price will apply to all variants of this products.")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')


    @api.multi
    @api.depends('product_name', 'product_code')
    def _compute_display_name(self):
        for this in self:
            this.display_name = '[%s] %s' % (this.product_code, this.product_name)
