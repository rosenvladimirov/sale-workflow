# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _

class AccountLoyalty(models.Model):
    _name = "account.loyalty"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Loyalty"
    _order = "date_loyalty desc, number desc, id desc"


    name = fields.Char(string='Reference/Description', index=True,
        readonly=True, states={'draft': [('readonly', False)]}, copy=False, help='The name that will be used on loyalty movement')
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this loyalty.",
        readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([
            ('out_loyalty','Paymnet with loyalty pooints'),
            ('in_loyalty','Colect loyalty points'),
        ], readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_loyalty'),
        track_visibility='always')
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Loyalty.\n"
             " * The 'Open' status is used when user creates Colect or payment with loyalty points.\n"
             " * The 'Cancelled' status is used when user cancel loyalty.")
    date_loyalty = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False)
    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')

    sale_order_ids = fields.One2many('sale.order', 'loyalty_id', string='Sale Orders',
        readonly=True, states={'draft': [('readonly', False)]})

    loyalty_line_ids = fields.One2many('account.loyalty.line', 'loyalty_id', string='Loyalty Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)



    def prepare_loyalty_line_set_data(self, loyalty_id, sale_line, sale_lines=False, old_qty=0.0):
        sale_line = self.env['account.loyalty.line'].new({
            'product_id': sale_line.product_id.id,
            'quantity': old_qty+sale_line.qty_invoiced,
            'price_unit': (old_price+sale_line.price_subtotal)/(old_qty+sale_line.qty_invoiced),
            'sale_lines': (6, 0, [x.id for x in sale_line | sale_lines]),
        })
        sale_line.product_id_change()
        line_values = sale_line._convert_to_write(sale_line._cache)
        return line_values



class AccountLoyaltyLine(models.Model):
    _name = "account.loyalty.line"
    _description = "Loyalty Line"
    _order = "loaylty_id,sequence,id"


    loyalty_id = fields.Many2one(comodel_name='account.loyalty', string='Loyalty')

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))

    gift_product_id = fields.Many2one(string="Gift Product", comodel_name="product.product", help="The product given as a reward")
    point_cost = fields.Integer(string="Point Cost", help="The cost of the reward per monetary unit discounted")
    discount_product_id = fields.Many2one(string="Discount Product", comodel_name="product.product", help="The product used to apply discounts")
    discount = fields.Float(string="Discount", help="The discount percentage")
    point_product_id = fields.Many2one(string="Point Product", comodel_name="product.product", help="The product that represents a point that is sold by the customer")
    sale_lines = fields.Many2many('sale.order.line', 'loyalty_sale_order_line_rel', 'loyalty', 'order_line_id', string='Sales Lines', copy=False)

