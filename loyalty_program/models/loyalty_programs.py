# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class LoyaltyProgram(models.Model):
    _name = 'loyalty.program'
    _description = 'Loyalty program for customers'

    name = fields.Char(string="Name", index=True, required=True, translate=True, help="An internal identification for the loyalty program configuration")
    code = fields.Char(string="Code", required=True, help="An internal identification code for the loyalty program configuration")
    display_name = fields.Char(compute='_compute_display_name')

    pp_currency = fields.Float(string='Points per currency',help="How many loyalty points are given to the customer by sold currency")
    pp_product = fields.Float(string='Points per product',help="How many loyalty points are given to the customer by product sold")
    pp_order = fields.Float(string='Points per order',help="How many loyalty points are given to the customer for each sale or order")
    rounding = fields.Float(string='Points Rounding', default=1, help="The loyalty point amounts are rounded to multiples of this value.")

    rule_ids = fields.One2many(string="Rules", comodel_name="loyalty.rule", inverse_name="loyalty_program_id")
    reward_ids = fields.One2many(string="Rules", comodel_name="loyalty.reward", inverse_name="loyalty_program_id")

    @api.multi
    def calculate_loyalty_points(self, product, qty, price, **kwargs):
        for rule in self.rule_ids.sorted(lambda r: r.sequence):
            if rule.check_match(product, qty, price, **kwargs):
                return rule.calculate_points(product, qty, price, **kwargs)
        return 0

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for program in self:
            program.display_name = "[%s] %s" % (program.code, program.name)


class LoyaltyRule(models.Model):
    _name = 'loyalty.rule'
    _description = 'Loyalty rules'

    @api.one
    @api.depends('product_id', 'category_id')
    def _compute_type(self):
        return ((not self.product_id and self.category_id) and 'category' or 'product')

    sequence = fields.Integer(string='Sequence', default=100)

    name = fields.Char(string="Name", index=True, required=True, translate=True, help="An internal identification for this loyalty program rule")
    code = fields.Char(string="Code", required=True, help="An internal identification code for the loyalty program rule")

    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program',string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    type = fields.Char(string="Type of Loyalty Rule", compute="_compute_type", help="Differend type of lloyalty rules (product or category)")

    product_id = fields.Many2one(comodel_name='product.product',string='Target Product', help='The product affected by the rule')
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', string='Product template', readonly=True)

    category_id = fields.Many2one(comodel_name='product.category',string='Target Category', help='The category affected by the rule')
    cumulative = fields.Boolean(string="Cumulative", help='How many points the product will earn per product ordered')

    pp_product = fields.Integer(string="Points per product",  help="How many points the product will earn per product ordered")
    pp_currency = fields.Integer(string="Points per currency", help="How many points the product will earn per value sold")


    @api.multi
    def _check_match(self, product, qty, price, **kwargs):
        _logger.info("Rulse %s" % kwargs)
        return True

    @api.multi
    def check_match(self, product, qty, price, **kwargs):
        self.ensure_one()
        def is_child_of(p_categ, c_categ):
            if p_categ == c_categ:
                return True
            elif not c_categ.parent_id:
                return False
            else:
                return is_child_of(p_categ, c_categ.parent_id)
        #Add quantity to rules matching?
        return (not self.product_id or self.product_id == product) and (not self.category_id or is_child_of(self.category_id, product.categ_id)) and self._check_match(product, qty, price, **kwargs)

    @api.multi
    def calculate_points(self, product, qty, price, **kwargs):
        self.ensure_one()
        return self.pp_product * qty + self.pp_currency * price

class LoyaltyReward(models.Model):
    _name = 'loyalty.reward'

    name = fields.Char(string="Name", index=True, required=True, translate=True, help="An internal identification for this loyalty reward")
    code = fields.Char(string="Code", required=True, help="An internal identification code for the loyalty program reward")

    loyalty_program_id = fields.Many2one(string="Loyalty Program", comodel_name="loyalty.program", help="The Loyalty Program this reward belongs to")
    minimum_points = fields.Integer(string="Minimum Points", help="The minimum amount of points the customer must have to qualify for this reward")

    type = fields.Selection(string="Type", selection=[("gift","Gift"), ("discount","Discount"), ("resale","Resale")], help="The type of the reward")
    gift_product_id = fields.Many2one(string="Gift Product", comodel_name="product.product", help="The product given as a reward")
    point_cost = fields.Integer(string="Point Cost", help="The cost of the reward per monetary unit discounted")
    discount_product_id = fields.Many2one(string="Discount Product", comodel_name="product.product", help="The product used to apply discounts")
    discount = fields.Float(string="Discount", help="The discount percentage")
    point_product_id = fields.Many2one(string="Point Product", comodel_name="product.product", help="The product that represents a point that is sold by the customer")

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")


    @api.multi
    @api.constrains("type", "gift_product_id")
    def _check_gift_product(self):
        for reward in self:
            if reward.type == 'gift':
                return bool(reward.gift_product_id)
            else:
                return True

    @api.multi
    @api.constrains("type", "discount_product_id")
    def _check_discount_product(self):
        for reward in self:
            if reward.type == 'discount':
                return bool(reward.discount_product_id)
            else:
                return True

    @api.multi
    @api.constrains("type", "discount_product_id")
    def _check_point_product(self):
        for reward in self:
            if reward.type == 'resale':
                return bool(reward.discount_product_id)
            else:
                return True

