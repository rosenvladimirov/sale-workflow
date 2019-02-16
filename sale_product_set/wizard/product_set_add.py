# Copyright 2015 Anybox S.A.S
# Copyright 2016-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class ProductSetAdd(models.TransientModel):
    _name = 'product.set.add'
    _rec_name = 'product_set_id'
    _description = "Wizard model to add product set into a quotation"

    def _get_default(self):
        return self._context.get('set_line_ids')

    product_set_id = fields.Many2one('product.set', 'Product set', required=True, domain="[('state', '=', 'progress'), ('active', '=', True)]")
    partner_id = fields.Many2one('res.partner', string='Partner', default=lambda self: self.env['res.company']._company_default_get('product.set').partner_id)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('product.set').partner_id)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    amount_total = fields.Monetary(string='Total', related="product_set_id.amount_total", store=True)
    split_sets = fields.Boolean("Split set")
    edit_sets = fields.Boolean("Edit set")
    set_lines = fields.One2many('product.set.add.line', 'product_set_id', string="Products", copy=True, default=_get_default)


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        }
        self.update(values)

    @api.multi
    @api.onchange('product_set_id')
    def onchange_product_set_id(self):
        for rec in self:
            if not rec.edit_sets:
                rec.set_lines.unlink()
                values = []
                for line in rec.product_set_id.set_lines:
                    _logger.info("Line %s:%s" % (line, rec.set_lines))
                    values.append((0, False, {
                        'product_tmpl_id': line.product_tmpl_id.id,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        #'product_set_id': line.product_set_id.id,
                        'sequence': line.sequence,
                        }))
                _logger.info("Values %s:%s" % (values, rec.product_set_id.set_lines))
                rec.update({'set_lines': values})
                self.set_lines.onchange_product_tmpl_id()

    @api.multi
    def sale_add_set(self):
        """ Add product set, multiplied by quantity in sale order line """
        so_id = self._context['active_id']
        if not so_id:
            return
        order_obj = self.env['sale.order']
        so = order_obj.browse(so_id)
        max_sequence = 0
        if so.order_line:
            max_sequence = max([line.sequence for line in so.order_line])
        sale_order_line = self.env['sale.order.line']
        set_lines = self.env['sale.order.sets']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in self.set_lines:
                if self.edit_sets:
                    domain = [('order_id', '=', self.id), ('product_set_id', '=', set.id), ('product_id', '=', set_line.product_id.id)]
                    line = self.order_line.search(domain, limit=1)
                    if set_line.product_alt_id:
                        line.write(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity, max_sequence=max_sequence, split_sets=self.split_sets, set_alt=True))
                    else:
                        line.write(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity,
                                                                              max_sequence=max_sequence,
                                                                              split_sets=self.split_sets, set_alt=False))
                else:
                    line = sale_order_line.create(order_obj.prepare_sale_order_line_set_data(so_id, set, set_line, self.quantity, max_sequence=max_sequence, split_sets=self.split_sets))
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                amount_untaxed += line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)['total_excluded']
                set_old = set_lines.search(
                    [('order_id', '=', so_id), ('product_set_id', '=', set.id), ('split_sets', '=', self.split_sets)])
                if set_old and not self.split_sets:
                    # _logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                    set_old.write(order_obj.prepare_sale_order_set_data(so_id, set, self.quantity + sum(
                        ss.quantity for ss in set_old), sum(
                        ss.amount_total for ss in set_old) + self.pricelist_id.currency_id.round(amount_untaxed),
                                                                        split_sets=self.split_sets))
                else:
                    set_old = set_lines.create(order_obj.prepare_sale_order_set_data(so_id, set, self.quantity,
                                                                           self.pricelist_id.currency_id.round(
                                                                           amount_untaxed),
                                                                           split_sets=self.split_sets))
                line.write({'set_id': set_old.id})

    @api.multi
    def purchase_add_set(self):
        """ Add product set, multiplied by quantity in purchase order line """
        po_id = self._context['active_id']
        if not po_id:
            return
        order_obj = self.env['purchase.order']
        po = order_obj.browse(po_id)
        max_sequence = 0
        if po.order_line:
            max_sequence = max([line.sequence for line in po.order_line])
        purchase_order_line = self.env['purchase.order.line']
        set_lines = self.env['purchase.order.sets']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = purchase_order_line.create(order_obj.prepare_purchase_order_line_set_data(po_id, set, set_line, self.quantity, max_sequence=max_sequence))
                price = line.price_unit
                amount_untaxed += line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)['total_excluded']
            set_old = set_lines.search([('order_id', '=', po_id), ('product_set_id', '=', set.id)])
            if set_old and not self.split_sets:
                #_logger.info("Add set %s:%s" % (self.quantity, set_old.quantity))
                set_old.write({
                        'order_id': po_id,
                        'product_set_id': set.id,
                        'quantity': self.quantity+set_old.quantity,
                        'amount_total': set_old.amount_total+self.pricelist_id.currency_id.round(amount_untaxed),
                        })
            else:
                set_lines.create(order_obj.prepare_purchase_order_set_data(po_id, set, self.quantity, self.pricelist_id.currency_id.round(amount_untaxed)))

    @api.multi
    def picking_add_set(self):
        """ Add product set, multiplied by quantity in sale order line """
        picking_id = self._context['active_id']
        if not picking_id:
            return
        picking_obj = self.env['stock.picking']
        picking = picking_obj.browse(picking_id)
        max_sequence = 0
        if picking.move_lines:
            max_sequence = max([line.sequence for line in picking.move_lines])
        picking_move_line = self.env['stock.move']
        for set in self.product_set_id:
            amount_untaxed = 0.0
            for set_line in set.set_lines:
                line = picking.move_lines.filtered(lambda r: r.picking_id.id == picking_id and r.product_id == set_line.product_id.id)
                if line:
                    line.write(picking.prepare_stock_move_pset_data(picking_id, set_line, self.quantity, max_sequence=max_sequence))
                else:
                    line = picking_move_line.create(picking.prepare_stock_move_pset_data(picking_id, set_line, self.quantity, max_sequence=max_sequence))

class ProductSetLine(models.TransientModel):
    _name = 'product.set.add.line'
    _description = 'Product set line'
    _rec_name = 'product_id'
    _order = 'sequence'


    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product template', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    product_alt_id = fields.Many2one(comodel_name='product.product', string='Product for virtual add')

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    quantity_alt = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))

    product_uom = fields.Many2one('product.uom', related="product_id.uom_id", string='Unit of Measure', readonly=True)
    product_uom_alt = fields.Many2one('product.uom', related="product_alt_id.uom_id", string='Unit of Measure', readonly=True)

    product_set_id = fields.Many2one('product.set', string='Set', ondelete='cascade',)
    sequence = fields.Integer(string='Sequence', required=True, default=0,)
    type = fields.Selection("product.set", related='product_set_id.type', string="Type", readonly=True)


    @api.multi
    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_id = rec.product_tmpl_id.product_variant_id.id
                return {'domain': {'product_id': [('product_tmpl_id', '=', rec.product_tmpl_id.id)]}}
