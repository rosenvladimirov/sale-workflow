# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, api, _

import logging
_logger = logging.getLogger(__name__)

class MailGroup(models.Model):
    _inherit = 'mail.channel'

    # Additional User methods
    @api.model
    def channel_get_extend(self, channel_partner_to_add, pin=True):
        if not channel_partner_to_add:
            return False
        # determine type according to the number of partner in the channel
        self.env.cr.execute("""
            SELECT P.channel_id as channel_id
            FROM mail_channel C, mail_channel_partner P
            WHERE P.channel_id = C.id
                AND C.public LIKE 'private'
                AND P.partner_id IN %s
                AND channel_type LIKE 'chat'
            GROUP BY P.channel_id
            HAVING array_agg(P.partner_id ORDER BY P.partner_id) = %s
        """, (tuple(channel_partner_to_add), sorted(list(channel_partner_to_add)),))
        result = self.env.cr.dictfetchall()
        if result:
            # get the existing channel between the given partners
            channel = self.browse(result[0].get('channel_id'))
            # pin up the channel for the current partner
            if pin:
                self.env['mail.channel.partner'].search([('partner_id', '=', channel_partner_to_add[0]), ('channel_id', '=', channel.id)]).write({'is_pinned': True})
        else:
            # create a new one
            channel = self.create({
                'channel_partner_ids': [(4, partner_id) for partner_id in channel_partner_to_add],
                'public': 'private',
                'channel_type': 'chat',
                'email_send': False,
                'name': ', '.join(self.env['res.partner'].sudo().browse(channel_partner_to_add).mapped('name')),
            })
        return channel.channel_info()[0]
