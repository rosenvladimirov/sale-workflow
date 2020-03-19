# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_contact_id = fields.Many2one('res.partner', string='Customer Contact', required=True, states={
                            'done': [('readonly', True)],
                            'cancel': [('readonly', True)],
                            }, change_default=True, track_visibility='always')

    @api.model
    def create(self, vals):
        mail_channel_obj = self.env['mail.channel']
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner.parent_id:
            vals['partner_id'] = partner.parent_id.id
            vals['partner_contact_id'] = partner.id
        if 'partner_contact_id' not in vals:
            vals['partner_contact_id'] = partner.child_ids and partner.mapped('child_ids')[0].id or partner.id
        if 'partner_contact_id' in vals:
            vals['message_follower_ids'] = vals.get('message_follower_ids', False) or []
            if vals['partner_contact_id'] != self.env.user.partner_id.id and vals['partner_contact_id'] != partner.id:
                user_partner = self.env['res.users'].search([('partner_id', '=', vals['partner_contact_id'])])
                if user_partner:
                    vals['message_follower_ids'] += self.env['mail.followers']._add_follower_command(self._name, [], {vals['partner_contact_id']: None}, {})[0]
            else:
                vals['message_follower_ids'] = False
            #_logger.info("Messages %s" % vals['message_follower_ids'])
        res = super(SaleOrder, self).create(vals)
        channel = mail_channel_obj.sudo().channel_get_extend(list(set([res.user_id.partner_id and res.user_id.partner_id.id or res.company_id.partner_id.id, res.partner_contact_id.name and res.partner_contact_id.id or res.company_id.partner_id.id])))
        mail_channel = mail_channel_obj.sudo().browse(channel['id'])
        if mail_channel:
            message_content = _('Created a new sale order: %s') % res.name
            mail_channel.with_context(mail_create_nosubscribe=True).message_post(author_id=res.partner_contact_id.id, email_from=False, body=message_content, message_type='comment', subtype='mail.mt_comment', content_subtype='plaintext')
        return res

    @api.multi
    def write(self, values):
        if 'partner_contact_id' in values and values['partner_contact_id'] and values['partner_contact_id'] not in [x.partner_id.id for x in self.message_follower_ids]:
            mail_channel_obj = self.env['mail.channel']
            channel = mail_channel_obj.sudo().channel_get_extend([values['partner_contact_id']])
            mail_channel = mail_channel_obj.sudo().browse(channel['id'])
            if not mail_channel:
                values['message_follower_ids'] = self.env['mail.followers']._add_follower_command(self._name, [], {values['partner_contact_id']: None}, {})[0]
            self.message_subscribe([values['partner_contact_id']])
        return super(SaleOrder, self).write(values)

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
        return res

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        self.ensure_one()
        invoice_vals.update({
            'partner_id': self.partner_invoice_id.vat and self.partner_invoice_id.id or self.partner_id.id,
            'partner_contact_id': self.partner_contact_id and self.partner_contact_id.id or False,
        })
        return invoice_vals

    @api.multi
    def _action_confirm(self):
        for order in self.filtered(lambda order: order.partner_contact_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_contact_id.id])
        for res in self:
            mail_channel_obj = self.env['mail.channel']
            channel = mail_channel_obj.sudo().channel_get_extend([res.user_id.partner_id.id, res.partner_contact_id.name and res.partner_contact_id.id or res.company_id.partner_id.id])
            mail_channel = mail_channel_obj.sudo().browse(channel['id'])
            if mail_channel:
                message_content = _('The sale order: %s were confirmed') % res.name
                mail_channel.with_context(mail_create_nosubscribe=True).message_post(author_id=res.partner_contact_id.id, email_from=False, body=message_content, message_type='comment', subtype='mail.mt_comment', content_subtype='plaintext')
        return super(SaleOrder, self)._action_confirm()
