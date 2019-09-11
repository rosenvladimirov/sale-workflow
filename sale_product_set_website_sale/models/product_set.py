# Copyright 2019 dXFactory Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.osv import expression
from odoo import fields, models, api, tools, _

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSet(models.Model):
    _inherit = 'product.set'

    session = fields.Char(help="Website session identifier where this product was setsed.")
    website_id = fields.Many2one('website', required=False, default=lambda self: self.env['res.config.settings'].website_id.id)

    @api.model
    def _rm_from_set(self, product_set, product=False):
        if product_set and product and self.state == 'draft':
            pset = product_set.set_lines.search([('product_set_id', '=', product_set.id), ('product_id', '=', product.id)])
            if pset:
                pset.unlink()
                if not product_set.set_lines.mapped('id'):
                    product_set.state = 'draft'
                    product_set.unlink()
        elif product_set and not product:
            product_set.state = 'draft'
            product_set.unlink()
        return product_set and product_set.id or False

    @api.model
    def _add_to_set(self, pricelist_id, currency_id, website_id, price, product_id, product_set_id=False, partner_id=False, session=False):
        sets = False
        if not session:
            sequence_code = self.env['ir.sequence'].sudo().next_by_code('product.set')
        else:
            sequence_code = session
        partner = self.env['res.partner'].browse(partner_id)
        if partner.parent_id:
            partner = partner.parent_id
        product = self.env['product.product'].browse(product_id)
        #_logger.info("Data to save %s:%s:%s:%s:%s" % (partner, product, product_set_id, sequence_code, session))
        if partner and product:
            product_set = self.env['product.set'].browse(product_set_id)
            if not product_set:
                product_set = self.env['product.set'].search([("partner_id", "=", partner.id), ('state', '=', 'draft')], limit=1)
            if product_set and product_set.state == 'draft':
                new_products = product_set.set_lines.search([('product_set_id', '=', product_set.id), ('product_id', '=', product.id)], limit=1)
                #_logger.info("product new _____________ %s:%s" % (new_products and new_products.product_id.name or new_products, product_set and product_set.name or product_set))
                if new_products:
                    for new_product in new_products:
                        new_product.quantity = new_product.quantity + 1.0
                    sets = True
                else:
                    sets = product_set.write({
                        'set_lines': [(0, False, {'product_id': product.id, 'product_uom': self.env.context.get('uom') or product.uom_id.id, 'quantity': 1.0})],
                    })
                if sets:
                    sets = product_set
            else:
                sets = product_set.create({
                    'name': "car-%s" % sequence_code[-4],
                    'code': sequence_code,
                    'partner_id': partner.id,
                    'session': session,
                    'set_lines': [(0, False, {'product_id': product.id, 'product_uom': self.env.context.get('uom') or product.uom_id.id, 'quantity': 1.0})],
                    'currency_id': currency_id,
                    'pricelist_id': pricelist_id and pricelist_id or (partner.property_product_pricelist and partner.property_product_pricelist.id or False),
                    'fiscal_position_id': self.env['account.fiscal.position'].get_fiscal_position(partner.id, partner.address_get(['delivery', 'invoice'])['delivery']) or self.env['account.fiscal.position'].get_fiscal_position(partner.id, partner.id),
                    'website_id': website_id,
                })
        #_logger.info("Sets ___ %s" % sets)
        return sets and sets.id or None

    @api.model
    def current(self, limit=100, offset=False, search=''):
        """Get all sets items that belong to current user or session,
        filter products that are unpublished."""
        if self._context.get("display_product_set_opened", False):
            return self.sudo().search([
                    ("partner_id", "=", self.env.user.partner_id.parent_id and self.env.user.partner_id.parent_id.id or self.env.user.partner_id.id),
                    ("state", "=", "draft"),
                    ], limit=limit, offset=offset, order="state asc").filtered("active")
        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|', ('code', 'ilike', srch), ('name', 'ilike', srch)]
        return self.sudo().search([
            ("partner_id", "=", self.env.user.partner_id.parent_id and self.env.user.partner_id.parent_id.id or self.env.user.partner_id.id)
            ]+domain, limit=limit, offset=offset).filtered("active").sorted(key=lambda r: (r.name, r.code))

    @api.model
    def product_set_count(self, search=''):
        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|', ('code', 'ilike', srch), ('name', 'ilike', srch)]
        return self.sudo().search_count([
            ("partner_id", "=", self.env.user.partner_id.parent_id and self.env.user.partner_id.parent_id.id or self.env.user.partner_id.id)
            ]+domain)

    @api.model
    def current_set_products(self):
        return self.sudo().search([
            ('active', '=', True),
            ("state", "=", "draft"),
            ("partner_id", "=", self.env.user.partner_id.parent_id and self.env.user.partner_id.parent_id.id or self.env.user.partner_id.id)
            ])

    @api.model
    def _join_current_user_and_session(self):
        """Assign all dangling session wishlisted products to user."""
        session_wishes = self.search([
            ("session", "=", self.env.user.current_session),
            ("partner_id", "=", False),
        ])
        partner_wishes = self.search([
            ("partner_id", "=", self.env.user.partner_id.id),
        ])
        partner_products = partner_wishes.mapped("product_id")
        # Remove session products already present for the user
        duplicated_wishes = session_wishes.filtered(lambda wish: wish.product_id <= partner_products)
        session_wishes -= duplicated_wishes
        duplicated_wishes.unlink()
        # Assign the rest to the user
        session_wishes.write({
            "partner_id": self.env.user.partner_id.id,
            "session": False,
        })

    @api.model
    def _garbage_collector(self, *args, **kwargs):
        """Remove wishlists for unexisting sessions."""
        self.search([
            ("create_date", "<", fields.Datetime.to_string(datetime.now() - timedelta(weeks=kwargs.get('wishlist_week', 5)))),
            ("partner_id", "=", False),
        ]).unlink()
