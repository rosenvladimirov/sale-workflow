# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_contact_id = fields.Many2one('res.partner', string='Customer Contact', required=True, states={
                            'done': [('readonly', True)],
                            'cancel': [('readonly', True)],
                            }, change_default=True, track_visibility='always')

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner.parent_id:
            vals['partner_id'] = partner.parent_id.id
            vals['partner_contact_id'] = partner.id
        if 'partner_contact_id' not in vals:
            vals['partner_contact_id'] = partner.child_ids and partner.mapped('child_ids')[0] or False
        return super(SaleOrder, self).create(vals)

    @api.onchange('partner_contact_id')
    def onchange_partner_contact_id(self):
        partner_id = False
        if not self.partner_contact_id:
            self.partner_id = False
        elif self.partner_contact_id.parent_id:
            self.partner_id = self.partner_contact_id.parent_id
            partner_id = self.partner_contact_id.parent_id
        else:
            self.partner_id = self.partner_contact_id
            partner_id = self.partner_contact_id
        return {'domain': {'partner_id': partner_id and [('id', '=', partner_id.id)] or []}}

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if not res:
            res = {}
        if (not self.partner_contact_id and self.partner_id) or (self.partner_contact_id and self.partner_id and self.partner_contact_id.parent_id != self.partner_id):
            self.partner_contact_id = self.partner_id.child_ids and self.partner_id.mapped('child_ids')[0] or False
            if self.partner_contact_id:
                res.update({'domain': {'partner_contact_id': [('customer', '=', True), ('parent_id', '=', self.partner_id.id)]}})
            else:
                res.update({'domain': {'partner_contact_id': [('customer', '=', True), ('id', '=', self.partner_id.id)]}})
        #else:
        #    res.update({'domain': {'partner_contact_id': []}})
        return res

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        invoice_vals.update({
            'partner_id': self.partner_invoice_id.vat and self.partner_invoice_id.id or self.partner_id.id,
        })
        return invoice_vals

    @api.model
    def create(self, vals):
        if 'partner_id' in vals and not vals.get('partner_contact_id', False):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            vals['partner_contact_id'] = partner.child_ids and partner.mapped('child_ids')[0].id or vals.get('partner_id')
        return super(SaleOrder, self).create(vals)
