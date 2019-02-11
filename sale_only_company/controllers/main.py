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

    def checkout_pager_values(self, checkout, limit=100, offset=False, search=''):
        _logger.info("Arguments %s:%s:%s:%s" % (checkout, limit, offset, search))
        res = {}
        shippings = []
        partner_related = []
        partner_related_delivery = []
        domain = []
        if checkout['order'].partner_id != request.website.user_id.sudo().partner_id:
            if search:
                for srch in search.split(" "):
                    domain += ['|', ('display_name', 'like', srch), ('ref', 'ilike', srch)]

            Partner = request.env['res.partner'].with_context(show_address=1).sudo()
            relations = request.env['res.partner'].with_context(active_test=True).sudo().search([
                                ('search_relation_partner_id', '=', checkout['order'].partner_id.id),
                                ]+domain)
            for x in relations:
                partner_related += x.commercial_partner_id.ids
                partner_related_delivery.append(x.commercial_partner_id.id)
            shippings = Partner.search([
                ("id", "child_of", partner_related),
                '|', ("type", "in", ["delivery", "other"]), ("id", "in", partner_related_delivery)
            ], limit=limit, offset=offset, order='id desc')
            if shippings:
                res['shippings'] = shippings
        return res

    def count_address(self, checkout, search=''):
        shippings = []
        partner_related = []
        partner_related_delivery = []
        domain = []
        address_count = len(checkout.get('shippings') and checkout.get('shippings').mapped("id") or [])
        if checkout['order'].partner_id != request.website.user_id.sudo().partner_id:
            Partner = request.env['res.partner'].with_context(show_address=1).sudo()
            if search:
                for srch in search.split(" "):
                    domain += ['|', ('display_name', 'like', srch), ('ref', 'ilike', srch)]
            relations = request.env['res.partner'].with_context(active_test=True).sudo().search([('search_relation_partner_id', '=', checkout['order'].partner_id.id)]+domain)
            for x in relations:
                partner_related += x.commercial_partner_id.ids
                partner_related_delivery.append(x.commercial_partner_id.id)
            address_count = Partner.search_count([
                ("id", "child_of", partner_related),
                '|', ("type", "in", ["delivery", "other"]), ("id", "in", partner_related_delivery)
            ])
        return address_count

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
        address_count = self.count_address(values)

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
        _logger.info("Search %s:%s:%s:%s:%s" % (values, ppg, pager['offset'], search, post))
        values.update(self.checkout_pager_values(values, limit=ppg, offset=pager['offset'], search=search))
        values.update({
                    'pager': pager,
                    'keep': keep,
                    'count': None,
                    'search': search
                    })
        # Avoid useless rendering if called in ajax
        if post.get('xhr'):
            return 'ok'
        return request.render("website_sale.checkout", values)
