# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby

from odoo import _, api, fields, models
from functools import reduce

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
                product_items = items.filtered(
                    lambda x: x.applied_on == '0_product_variant' and not x.product_set_id)
                template_items = items.filtered(
                    lambda x: x.applied_on == '1_product' and not x.product_set_id)
                category_items = items.filtered(
                    lambda x: x.applied_on == '2_product_category')
                # Convert al pricelist items to their affected variants
                if product_items:
                    res['show_variants'] = True
                    product_ids = product_items.mapped('product_id')
                    product_ids |= template_items.mapped(
                        'product_tmpl_id.product_variant_ids')
                    product_ids |= product_ids.search([
                        ('sale_ok', '=', True),
                        ('categ_id', 'in', category_items.mapped('categ_id').ids)
                    ])
                    res['product_ids'] = [(6, 0, product_ids.ids)]
                # Convert al pricelist items to their affected templates
                if template_items and not product_items:
                    product_tmpl_ids = template_items.mapped('product_tmpl_id')
                    product_tmpl_ids |= product_tmpl_ids.search([
                        ('sale_ok', '=', True),
                        ('categ_id', 'in', category_items.mapped('categ_id').ids)
                    ])
                    res['product_tmpl_ids'] = [
                        (6, 0, product_tmpl_ids.ids)]
                # Only category items, we just set the categories
                if category_items and not product_items and not template_items:
                    res['categ_ids'] = [
                        (6, 0, category_items.mapped('categ_id').ids)]
            #_logger.info("SETS %s" % res)
        return res

    @api.onchange('product_from_pricelist', 'pricelist_id')
    def _onchange_product_from_pricelist(self):
        if self.pricelist_id and self.product_from_pricelist:
            res = self.with_context(from_pricelist_id=self.pricelist_id.item_ids.ids).default_get([])
            if res.get('product_ids'):
                self.product_ids = res['product_ids']
                self.show_variants = True
                self.product_ids = self.product_ids.sorted(lambda x: x.product_tmpl_id.id)
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
        pages = {product_set_obj: products.sorted(lambda r: r.product_tmpl_id.id)}
        #pages[product_set_obj] = products.sorted(lambda r: r.product_tmpl_id.id)
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
        #pages[product_set_obj] = products-all_set_products
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
                'pset': k,
                'group': "-".join([k.mdgp_device and k.mdgp_device.code or "unknown", k.mdgp_anatomy and k.mdgp_anatomy.code or "unknown", k.mdgp_type and k.mdgp_type.name or 'unknown']),
                'group_name': ", ".join([x for x in [k.mdgp_device and k.mdgp_device.name or 'unknown', k.mdgp_anatomy and k.mdgp_anatomy.name or 'unknown', k.mdgp_type and k.mdgp_type.name or 'unknown'] if x != 'unknown']),
                'group_color': k.mdgp_anatomy.color,
                'group_sort': "-".join([k.mdgp_device and k.mdgp_device.code or "unknown", k.mdgp_anatomy and k.mdgp_anatomy.code or "unknown", k.mdgp_type and k.mdgp_type.name or 'unknown', k.code and k.code or "", "unknown"]),
                'codes': False,
                }
                report_pages[-1].append(values)
            else:
                for category, lines in groupby(v, lambda l: l.product_tmpl_id):
                    report_pages[-1].append({
                        'name': category and category.display_name or _('Uncategorized'),
                        'lines': list(lines),
                        'qty': False,
                        'price': False,
                        'tax': False,
                        'price_subtotal': False,
                        'pset': False,
                        'group': "-".join([category.vmdgp_device and category.vmdgp_device.code or "unknown", category.vmdgp_anatomy and category.vmdgp_anatomy.code or "unknown", category.mdgp_type and category.mdgp_type.name or 'unknown']),
                        'group_name': ", ".join([x for x in [category.vmdgp_device and category.vmdgp_device.name or "unknown", category.vmdgp_anatomy and category.vmdgp_anatomy.name or "unknown", category.mdgp_type and category.mdgp_type.name or 'unknown'] if x != 'unknown']),
                        'group_color': category.mdgp_anatomy.color,
                        'group_sort': "-".join([category.vmdgp_device and category.vmdgp_device.code or "unknown", category.vmdgp_anatomy and category.vmdgp_anatomy.code or "unknown", category.mdgp_type and category.mdgp_type.name or 'unknown', "unknown", category.default_code and category.default_code or 'unknown']),
                        'has_variant_with_price': category.product_variant_count > 1 and category.check_for_price(
                            pricelist, date),
                        'single_product': category.product_variant_count == 1,
                        'codes': False,
                    })

        if len(report_pages[-1]) > 0:
            for val in report_pages[-1]:
                codes = {}
                if val.get('pset'):
                    pset = val['pset']
                    if not codes.get(pset):
                        codes[pset] = set([])
                    val["codes"] = False
                    for line in val['lines']:
                        ctx = dict(self._context, pricelist=pricelist.id, product_set_id=pset.id)
                        #_logger.info("CTX %s:%s" % (ctx, line.with_context(ctx).pricelist_code))
                        if line.with_context(ctx).pricelist_code:
                            codes[pset].update([line.with_context(ctx).pricelist_code])
                    if codes:
                        val["codes"] = list(set(reduce(lambda x, y: list(x)+list(y), list(codes.values()))))
            #page = sorted(page, key=lambda x: x.get('pset') and str(x['pset'].code) or str(False), reverse=True)
        report_pages[-1] = sorted(report_pages[-1], key=lambda x: x['group']+"-".join(map(str, [x['group_sort']])))
        #_logger.info("SETS %s:%s" % (pricelist, report_pages[-1]))
        return report_pages

    def _get_field_value(self, product, partner, pricelist, page):
        res = super(ProductPricelistPrint, self)._get_field_value(product, partner, pricelist, page)
        if res and page.get('pset'):
            res['product_set_id'] = page['pset'].id
        return res

    def _get_key_value(self, partner_id, pricelist_id, product_tmpl_id, product_id, page):
        key = super(ProductPricelistPrint, self)._get_key_value(partner_id, pricelist_id, product_tmpl_id, product_id, page)
        if page.get('pset'):
            key += "-%s" % page['pset'].id
        else:
            key += "-False"
        return key

    def _get_product_layouted(self, products, pricelist, date):
        return self.product_set_layouted(products, pricelist, date)


class ProductPricelistPrintLine(models.TransientModel):
    _inherit = 'product.pricelist.print.line'

    product_set_id = fields.Many2one('product.set', string='Product Set')
