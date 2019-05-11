# -*- coding: utf-8 -*-

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json

import logging
_logger = logging.getLogger(__name__)

PPG = 10  # Product sets Per Page

class WebsiteSaleSets(WebsiteSale):


    @http.route(['/shop/sets/add'], type='json', auth="public", website=True)
    def add_to_sets(self, product_id, product_set_id=False, price=False, **kw):
        if not price:
            compute_currency, pricelist_context, pl = self._get_compute_currency_and_context()
            p = request.env['product.product'].with_context(pricelist_context, display_default_code=False).browse(product_id)
            price = p.website_price

        partner_id = session = False
        if not request.website.is_public_user():
            partner_id = request.env.user.partner_id.id
        else:
            session = request.session.sid
        return request.env['product.set'].sudo()._add_to_set(
            pl.id,
            pl.currency_id.id,
            request.website.id,
            price,
            product_id,
            product_set_id,
            partner_id,
            session
        )

    @http.route([
                '/shop/sets',
                '/shop/sets/page/<int:page>'
    ], type='http', auth="public", website=True)
    def get_sets(self, count=False, page=0, search='', ppg=False, **post):
        product_set = request.env['product.set']
        if count:
            return request.make_response(json.dumps(product_set.with_context(display_default_code=False).current().mapped("id")))


        product_set_count = product_set.product_set_count(search=search)

        if not product_set_count:
            return request.redirect("/shop")

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if search:
            post["search"] = search
        keep = QueryURL('/shop/sets', search=search)

        pager = request.website.pager(url='/shop/sets', total=product_set_count, page=page, step=ppg, scope=7, url_args=post)
        values = product_set.with_context(display_default_code=False).current(limit=ppg, offset=pager['offset'], search=search)
        return request.render("sale_product_set.product_set", dict(
                                product_sets=values,
                                pager=pager,
                                pset_count=product_set_count,
                                opened=values.filtered(lambda r: r.state == 'draft'),
                                keep=keep,
                                count=None,
                                search=search))

    @http.route([
                '/shop/sets/opened',
    ], type='json', auth="public", website=True)
    def get_opened(self, opened=True, **kw):
        ctx = dict(kw['kwargs']['context'])
        _logger.info("Context %s:%s:%s" % (ctx, request.context, kw))
        if ctx.get('display_product_set_product', False):
            res = request.env['product.set'].with_context(display_product_set_opened=True).current_set_products()
            return res and [res.mapped('id')[0], [x.id for x in res.mapped('set_lines').mapped('product_id')]] or False
        else:
            res = request.env['product.set'].with_context(display_product_set_opened=True).current()
            return res and res.mapped("id") or False

    @http.route(['/shop/sets/remove/<model("product.set"):sets>'], type='json', auth="public", website=True)
    def rm_sets(self, sets, **kw):
        if sets and sets.state == 'draft':
            sets.active = False
            sets.state = 'freeze'
            res = request.env['product.set'].with_context(display_product_set_opened=True).current()
            return res and res.mapped("id") or False
        return sets and sets.id or False

    @http.route(['/shop/sets/product/remove/<model("product.set"):sets>/<model("product.product"):product>'], type='json', auth="public", website=True)
    def rm_from_sets(self, sets, product=False, **kw):
        _logger.info("Remove %s:%s" % (sets, product and product.id or product))
        if sets:
            sets._rm_from_set(sets, product)
        return sets and sets.id or False

    @http.route(['/shop/sets/state/<model("product.set"):sets>'], type='json', auth="public", website=True)
    def sets_state(self, sets, state, **kw):
        sets.state = state
        return sets.state

    @http.route(['/shop/sets/dublicate/<model("product.set"):sets>'], type='json', auth="public", website=True)
    def sets_copy(self, sets, **kw):
        res = False
        if sets and sets.state == 'draft':
            sequence_code = request.env['ir.sequence'].sudo().next_by_code('product.set')
            res = sets.copy({'code': sequence_code, 'name': sets.name.replace(sets.code, sequence_code)})
            for row in sets.set_lines:
                row.copy({'product_set_id': res.id})
            sets.state = 'freeze'
        return res and res.id or False

    @http.route(['/shop/sets/get/<model("product.set"):sets>'], type='json', auth="public", website=True)
    def get_from_sets(self, sets, **kw):
        values = sets.mapped('set_lines')
        return [(x.product_id.id, x.quantity) for x in values]

    @http.route(['/shop/sets/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def sets_update_json(self, product_set_id, add_qty=None, set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        value = order._set_cart_update(product_set_id=product_set_id, add_qty=add_qty, set_qty=set_qty)

        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity
        from_currency = order.company_id.currency_id
        to_currency = order.pricelist_id.currency_id

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'compute_currency': lambda price: from_currency.compute(price, to_currency),
            'suggested_products': order._cart_accessories()
        })
        return value

    @http.route(['/shop/sets/modal/<model("product.set"):product_sets>'], type='json', auth="public", methods=['POST'], website=True)
    def prodset_modal(self, product_sets=None, **post):
        if not product_sets:
            return False

        error = dict()
        error_message = []
        if not product_sets:
            error['product_sets'] = None
            error_message.append(_('Invalid Product Set ID. Please ask Administrator to check!'))

        return request.env['ir.ui.view'].render_template("sale_product_set.prodset_modal", {
            'name': product_sets and product_sets.name or None,
            'code': product_sets and product_sets.code or None,
            'cars': request.env['fleet.vehicle.model'].sudo(),
            'error': error,
            'error_message': error_message,
            'kw': post,
        })

    @http.route(['/shop/sets/update_desc/<model("product.set"):product_sets>'], type='json', auth="public", methods=['POST'], website=True, multilang=False)
    def sets_description_update_json(self, product_sets, name=None, code=None, fleet_ids=None, lang=None, **kw):
        #_logger.info("post %s:%s:%s:%s:%s" % (product_sets, name, code, fleet_ids, kw))
        if lang:
            request.website = request.website.with_context(lang=lang)
        #product_set = request.env['product.set'].browse(product_set_id)
        if product_sets and name and code:
            res = product_sets.write({'name': name, 'code': code})
            return res and product_sets.id or False
        return product_sets and product_sets.id or False
