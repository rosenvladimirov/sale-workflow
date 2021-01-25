# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLinePriceHistory(models.TransientModel):
    _name = "sale.order.line.price.history"
    _description = "Sale order line price history"

    @api.model
    def _default_partner_id(self):
        line_id = self.env.context.get("active_id")
        return self.env['sale.order.line'].browse(line_id).order_partner_id.id

    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
        default=lambda self: self.env.context.get("active_id"),
    )
    product_id = fields.Many2one(
        related="sale_order_line_id.product_id",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        default=_default_partner_id,
    )
    line_ids = fields.One2many(
        comodel_name="sale.order.line.price.history.line",
        inverse_name="sale_history_id",
        string="History line",
        readonly=True,
    )
    include_quotations = fields.Boolean(
        string="Include quotations",
        help="Include quotations lines in the sale history",
    )
    include_commercial_partner = fields.Boolean(
        string="Include commercial entity",
        default=True,
        help="Include commercial entity and its contacts in the sale history"
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        compute_sudo=True,
        help="Pricelist for current sales order.",
        default=lambda self: self.env.context.get('default_pricelist_id'),
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Ordered qty from SO",
        default=lambda self: self.env.context.get('default_product_uom_qty'),
    )
    custom_price_unit = fields.Float('For update')

    @api.onchange("partner_id", "include_quotations",
                  "include_commercial_partner")
    def _onchange_partner_id(self):
        self.line_ids = False
        states = ["sale", "done"]
        if self.include_quotations:
            states += ["draft", "sent"]
        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "in", states),
        ]
        if self.partner_id and not self._context.get('force_remove_partner'):
            if self.include_commercial_partner:
                domain += [("order_partner_id", "child_of",
                            self.partner_id.commercial_partner_id.ids)]
            else:
                domain += [
                    ("order_partner_id", "child_of", self.partner_id.ids)]

        vals = []
        order_lines = self.env['sale.order.line'].search(domain, limit=20)
        order_lines -= self.sale_order_line_id
        for order_line in order_lines:
            vals.append((0, False, {
                'sale_order_line_id': order_line.id,
                'history_sale_order_line_id': self.sale_order_line_id,
            }))
        self.line_ids = vals

    @api.multi
    def action_set_price(self):
        self.ensure_one()
        self.history_sale_order_line_id.price_unit = self.custom_price_unit


class SaleOrderLinePriceHistoryline(models.TransientModel):
    _name = "sale.order.line.price.history.line"
    _description = "Sale order line price history line"

    sale_history_id = fields.Many2one(
        comodel_name="sale.order.line.price.history",
        string="History",
    )
    history_sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string="history sale order line",
    )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale order line',
    )
    order_id = fields.Many2one(
        related="sale_order_line_id.order_id",
        readonly=True,
    )
    partner_id = fields.Many2one(
        related="sale_order_line_id.order_partner_id",
        readonly=True,
    )
    sale_order_date_order = fields.Datetime(
        related="sale_order_line_id.order_id.date_order",
        readonly=True,
    )
    sale_order_product_id = fields.Many2one(
        related="sale_order_line_id.product_id",
        readonly=True,
    )
    product_uom_qty = fields.Float(
        related="sale_order_line_id.product_uom_qty",
        readonly=True,
    )
    price_unit = fields.Float(
        related="sale_order_line_id.price_unit",
        readonly=True,
    )

    @api.multi
    def action_set_price(self):
        self.ensure_one()
        self.history_sale_order_line_id.price_unit = self.price_unit

    @api.model
    def get_value_pricelist(self, lwrite=False):
        if lwrite:
            return {'pricelist_id': self.history_sale_order_line_id.order_id.pricelist_id.id, 'default_base':'list_price',
                    'compute_price': 'fixed', 'product_id':  self.sale_order_product_id.id,
                    'applied_on': '0_product_variant', 'fixed_price': self.price_unit}
        else:
            return {'compute_price': 'fixed', 'applied_on': '0_product_variant',
                    'product_id':  self.sale_order_product_id.id,
                    'base_pricelist_id': False, 'price_surcharge': 0.0, 'price_discount': 0.0,
                    'price_round': 0.0, 'price_min_margin': 0.0, 'price_max_margin': 0.0,
                    'percent_price': 0.0, 'fixed_price': self.price_unit}

    @api.multi
    def save_in_pricelist(self):
        self.ensure_one()
        #_logger.info("PRICELIST %s" % self.history_sale_order_line_id.order_id.pricelist_id)
        if self.history_sale_order_line_id.order_id.pricelist_id:
            pricelist_id = self.history_sale_order_line_id.order_id.pricelist_id
            product_id = self.sale_order_product_id
            pricelist_rule_id = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist_id.id), "|",
                                                                           ('product_id', '=', product_id.id),
                                                                           ('product_tmpl_id', '=', product_id.product_tmpl_id.id)])
            _logger.info("SAVE PRICELIST %s" % self.get_value_pricelist())
            if pricelist_rule_id:
                pricelist_rule_id.write(self.get_value_pricelist(False))
            else:
                self.env['product.pricelist.item'].create(self.get_value_pricelist(True))
