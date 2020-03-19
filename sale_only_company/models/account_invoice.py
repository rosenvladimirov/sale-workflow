# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    partner_contact_id = fields.Many2one('res.partner', string='Customer Contact', required=False, states={
                            'done': [('readonly', True)],
                            'cancel': [('readonly', True)],
                            }, change_default=True, track_visibility='always')

    @api.onchange('partner_contact_id')
    def _onchange_partner_contact_id(self):
        if self.partner_contact_id:
            for line in self.invoice_line_ids:
                if not line.partner_contact_id:
                    line.partner_contact_id = self.partner_contact_id

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        invoice_line_obj = self.env['account.invoice.line']
        for vals in res:
            if vals.get('invl_id'):
                invline = invoice_line_obj.browse(vals['invl_id'])
                if invline.partner_contact_id:
                    vals['partner_contact_id'] = invline.partner_contact_id.id
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    partner_contact_id = fields.Many2one('res.partner', string='Customer Contact', required=False, states={
                            'done': [('readonly', True)],
                            'cancel': [('readonly', True)],
                            }, change_default=True, track_visibility='always')

