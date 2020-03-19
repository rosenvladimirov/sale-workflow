# -*- coding: utf-8 -*-

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json

import logging
_logger = logging.getLogger(__name__)

PPG = 8  # Product address Per Page

class WebsiteSaleSets(WebsiteSale):

    def _checkout_pager_values(self, checkout, search='', limit=100, offset=False):
        partner_related = []
        partner_related_delivery = []
        domain = []
        lang = request.env.user.sudo().lang

        if checkout['order'].partner_id != request.website.user_id.sudo().partner_id:
            if search:
                lang_name = 'display_name_%s' % lang.split("_")[0]
                for srch in search.split(" "):
                    if lang_name in request.env['res.partner']._fields and len(srch.encode('ascii', 'ignore')) != len(srch):
                        domain += ['|', "|", ('display_name_en', 'like', srch.upper()+"%"), (lang_name, 'like', srch.upper()+"%"), ('ref', 'ilike', srch)]
                    else:
                        domain += ['|', ('display_name_en', 'like', srch.upper()+"%"), ('ref', 'ilike', srch)]

            relations = request.env['res.partner'].with_context(active_test=True).sudo().search([
                                ('search_relation_partner_id', '=', checkout['order'].partner_id.id),
                                ]+domain)
            for x in relations:
                partner_related += x.commercial_partner_id.ids
                partner_related_delivery.append(x.commercial_partner_id.id)
            if relations:
                return partner_related, partner_related_delivery
        return False, False

    def checkout_pager_values(self, checkout, search='', limit=100, offset=False):
        #_logger.info("Arguments %s:%s:%s:%s" % (checkout, limit, offset, search))
        res = {}
        shippings = []
        partner_related, partner_related_delivery = self._checkout_pager_values(checkout, search=search, limit=limit, offset=offset)
        if partner_related and partner_related_delivery:
            Partner = request.env['res.partner'].with_context(show_address=1).sudo()
            shippings = Partner.search([
                    ("id", "child_of", partner_related),
                    '|', ("type", "in", ["delivery", "other"]), ("id", "in", partner_related_delivery)
                ], limit=limit, offset=offset, order='id desc')
            if shippings:
                res['shippings'] = shippings
        return res

    def count_address(self, checkout, search=''):
        address_count = len(checkout.get('shippings') and checkout.get('shippings').mapped("id") or [])
        partner_related, partner_related_delivery = self._checkout_pager_values(checkout, search=search)
        if partner_related and partner_related_delivery:
            Partner = request.env['res.partner'].with_context(show_address=1).sudo()
            address_count = Partner.search_count([
                    ("id", "child_of", partner_related),
                    '|', ("type", "in", ["delivery", "other"]), ("id", "in", partner_related_delivery)
                ])
        return address_count

    def checkout_values(self, **kw):
        order = request.website.sale_get_order(force_create=1)
        shippings = []
        partner_related = []
        partner_related_delivery = []
        if order.partner_id != request.website.user_id.sudo().partner_id:
            Partner = order.partner_id.with_context(show_address=1).sudo()
            relations = request.env['res.partner'].with_context(active_test=True).sudo().search([
                                ('search_relation_partner_id', '=', order.partner_id.id),
                                ])
            for x in relations:
                partner_related += x.commercial_partner_id.ids
                partner_related_delivery.append(x.commercial_partner_id.id)
            if relations:
                shippings = Partner.search([
                        ("id", "child_of", partner_related),
                        '|', ("type", "in", ["delivery", "other"]), ("id", "in", partner_related_delivery)
                    ], order='id desc')
            else:
                shippings = False
            if shippings:
                if kw.get('partner_id') or 'use_billing' in kw:
                    if 'use_billing' in kw:
                        partner_id = order.partner_id.id
                    else:
                        partner_id = int(kw.get('partner_id'))
                    if partner_id in shippings.mapped('id'):
                        order.partner_shipping_id = partner_id
                elif not order.partner_shipping_id:
                    last_order = request.env['sale.order'].sudo().search([("partner_id", "=", order.partner_id.id)], order='id desc', limit=1)
                    order.partner_shipping_id.id = last_order and last_order.id

        values = {
            'order': order,
            'shippings': shippings,
            'only_services': order and order.only_services or False
        }
        return values

    @http.route([
                '/shop/checkout',
                '/shop/checkout/page/<int:page>'
                ], type='http', auth="public", website=True)
    def checkout(self, page=0, search='', ppg=False, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            return request.redirect('/shop/address')

        for f in self._get_mandatory_billing_fields():
            if not order.partner_id[f]:
                return request.redirect('/shop/address?partner_id=%d' % order.partner_id.id)
        values = self.checkout_values(**post)
        address_count = self.count_address(values, search=search)

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
        keep = QueryURL('/shop/checkout', search=search)
        pager = request.website.pager(url='/shop/checkout', total=address_count, page=page, step=ppg, scope=7, url_args=post)
        #_logger.info("Search %s:%s:%s:%s:%s" % (values, ppg, pager['offset'], search, post))
        values.update(self.checkout_pager_values(values, search=search, limit=ppg, offset=pager['offset']))
        values.update({
                    'pager': pager,
                    'keep': keep,
                    'count': None,
                    'search': search
                    })
        _logger.info("POST %s:%s" % (post, order.partner_shipping_id))
        # Avoid useless rendering if called in ajax
        if post.get('xhr'):
            return 'ok'
        return request.render("website_sale.checkout", values)
