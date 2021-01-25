# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLinePriceHistory(models.TransientModel):
    _inherit = "sale.order.line.price.history"

    purchase_line_ids = fields.One2many(
        comodel_name="purchase.order.line.price.history.line",
        inverse_name="purchase_history_id",
        string="History line",
        readonly=True,
    )
    move_line_ids = fields.One2many(
        comodel_name="stock.move.line.price.history.line",
        inverse_name="purchase_history_id",
        string="History moves",
        readonly=True,
    )

    @api.onchange("partner_id", "include_quotations",
                  "include_commercial_partner")
    def _onchange_partner_id(self):
        self.purchase_line_ids = False
        self.move_line_ids = False
        move_ids = self.env['stock.move']
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

        states = ["purchase", "done"]
        move_states = ["done"]
        if self.include_quotations:
            states += ["draft", "sent"]
        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "in", states),
        ]

        vals = []
        order_lines = self.env['purchase.order.line'].search(domain, limit=20)
        for order_line in order_lines:
            move_ids |= order_line.move_ids
            vals.append((0, False, {
                'purchase_order_line_id': order_line.id,
                'history_sale_order_line_id': self.sale_order_line_id.id,
            }))
        self.purchase_line_ids = vals
        vals = []
        for move_line in move_ids:
            if move_line.state in move_states:
                for line in move_line.move_line_ids:
                    vals.append((0, False, {
                        'sale_history_id': self.id,
                        'stock_move_line_id': line.id,
                        'history_sale_order_line_id': self.sale_order_line_id.id,
                    }))
        self.move_line_ids = vals


class PurchaseOrderLinePriceHistoryline(models.TransientModel):
    _inherit = "purchase.order.line.price.history.line"

    history_sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string="history sale order line",
    )

    @api.multi
    def action_set_price_in_sale(self):
        self.ensure_one()
        _logger.info("PRICE %s" % (self.price_unit))
        self.history_sale_order_line_id.price_unit = self.price_unit
        return {'type': 'ir.actions.act_window_close'}


class StockMoveLinePriceHistoryline(models.TransientModel):
    _inherit = "stock.move.line.price.history.line"

    sale_history_id = fields.Many2one(
        comodel_name="sale.order.line.price.history",
        string="History",
    )
    history_sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string="history sale order line",
    )
    sale_price_unit = fields.Float(
        compute="_compute_sale_price_uit"
    )
    currency_id = fields.Many2one(
        related="history_sale_order_line_id.order_id.currency_id",
        readonly=True,
    )

    def _compute_sale_price_uit(self):
        for record in self:
            sale_price_unit = record.history_sale_order_line_id.product_id.with_context(pricelist=record.sale_history_id.pricelist_id.id, forceprice=record.price_unit).price
            record.update({'custom_price_unit': sale_price_unit, 'sale_price_unit': sale_price_unit})
            #record.sale_history_id.custom_price_unit = sale_price_unit

    @api.multi
    def action_set_purchase_price_in_sale(self):
        for record in self:
            sale_price_unit = record.history_sale_order_line_id.product_id.with_context(pricelist=record.history_sale_order_line_id.order_id.pricelist_id.id, forceprice=record.price_unit).price
            #_logger.info("ACTIVE ID %s-%s" % (record.history_sale_order_line_id, record.sale_history_id) )
            #_logger.info("PRICE %s:%s:%s:%s" % (record.price_unit, record.sale_price_unit, record.custom_price_unit, sale_price_unit))
            record.history_sale_order_line_id.price_unit = sale_price_unit != record.custom_price_unit and record.custom_price_unit or sale_price_unit
        return {'type': 'ir.actions.act_window_close'}
