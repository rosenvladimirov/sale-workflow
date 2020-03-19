# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_contact_id = fields.Many2one('res.partner', compute='_compute_partner_id', string="Partner", store=True, readonly=True)

    @api.multi
    @api.depends('line_ids.partner_contact_id')
    def _compute_partner_id(self):
        for move in self:
            partner_contact = move.line_ids.mapped('partner_contact_id')
            move.partner_contact_id = partner_contact.id if len(partner_contact) == 1 else False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partner_contact_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
