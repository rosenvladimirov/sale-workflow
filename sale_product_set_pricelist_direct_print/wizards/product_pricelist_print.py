# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistPrint(models.TransientModel):
    _inherit = 'product.pricelist.print'

    product_set_ids = fields.Many2many(
        comodel_name='product.set',
        string='Product sets',
        )
    show_set_detals = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(ProductPricelistPrint, self).default_get(fields)
        if self.env.context.get('from_pricelist_id'):
            active_ids = self.env.context.get('from_pricelist_id') or self.env.context.get('active_ids', [])
            items = self.env['product.pricelist.item'].browse(active_ids)
            product_set_items = items.filtered(
                lambda r: r.product_set_id)
            if product_set_items:
                res['product_set_ids'] = [
                    (6, 0, list(set(product_set_items.mapped('product_set_id').ids)))]
            _logger.info("SETS %s" % res)
        return res

    @api.onchange('product_from_pricelist', 'pricelist_id')
    def _onchange_product_from_pricelist(self):
        if self.pricelist_id and self.product_from_pricelist:
            res = self.with_context(from_pricelist_id=self.pricelist_id.item_ids.ids).default_get([])
            if res.get('product_ids'):
                self.product_ids = res['product_ids']
                self.show_variants = True
                if self.order_field == 'name':
                    self.product_ids = self.product_ids.sorted(lambda x: x.name)
                elif self.order_field == 'default_code':
                    self.product_ids = self.product_ids.sorted(lambda x: x.default_code)
                else:
                    self.product_ids = self.product_ids.sorted(lambda x: x.product_tmpl_id.name)
            if res.get('product_tmpl_ids'):
                self.product_tmpl_ids = res['product_tmpl_ids']
            if res.get('categ_ids'):
                self.categ_ids = res['categ_ids']
            if res.get('product_set_ids'):
                self.product_set_ids = res['product_set_ids']
        if not self.product_from_pricelist:
            self.partner_id = False

    @api.multi
    def product_set_layouted(self, products, pricelist, date):
        self.ensure_one()
        product_set_obj = self.env['product.set']
        pages = {product_set_obj: []}
        qty_set_products = {}
        all_set_products = self.env['product.product']
        for seto in self.product_set_ids:
            for set_line in seto.set_lines:
                #if set_line.product_id in products:
                if not qty_set_products.get(seto):
                    qty_set_products[seto] = {}
                if not pages.get(seto):
                    pages[seto] = []
                if not qty_set_products[seto].get(set_line.product_id):
                    qty_set_products[seto][set_line.product_id] = 0
                qty_set_products[seto][set_line.product_id] += set_line.quantity
            pages[seto] = seto.set_lines.mapped('product_id')
            all_set_products |= pages[seto]
        pages[product_set_obj] = products-all_set_products
        #_logger.info("SETS %s" % pages)
        report_pages = [[]]
        for k, v in pages.items():
            price_tax = 0.0
            price_total = 0.0
            price_subtotal = 0.0
            if (k != product_set_obj):
                fpos = self.partner_id and self.partner_id.property_account_position_id or self.env.user.company_id.partner_id.property_account_position_id
                line_company_id = self.env.user.company_id
                for x in v:
                    taxes = x.taxes_id.filtered(lambda r: not line_company_id or r.company_id == line_company_id)
                    tax_id = fpos.map_tax(taxes, x, self.partner_id) if fpos else taxes
                    price = self.env['account.tax']._fix_tax_included_price_company(
                                                x.with_context(pricelist=pricelist.id,
                                                date=date,
                                                quantity=qty_set_products[k][x],
                                                product_set_id=k.id,
                                                partner_id=self.partner_id and self.partner_id.id).price, x.taxes_id,
                                                tax_id, line_company_id)
                    taxes = tax_id.compute_all(price, pricelist.currency_id, qty_set_products[k][x])
                    price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    price_total += taxes['total_included']
                    price_subtotal += taxes['total_excluded']
                values = {
                'name': k.display_name,
                'lines': v,
                'qty': qty_set_products[k],
                'price': price_total,
                'tax': price_tax,
                'price_subtotal': price_subtotal,
                }
                report_pages[-1].append(values)
            else:
                #_logger.info("SETS %s" % values)
                values = {
                'name': _('Uncategorized'),
                'lines': v,
                'qty': False,
                'price': False,
                'tax': False,
                'price_subtotal': False,
                }
                report_pages[-1].append(values)
        #_logger.info("SETS %s" % report_pages[-1])
        return report_pages
