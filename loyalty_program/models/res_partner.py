# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    loyalty_program_id = fields.Many2one(comodel_name='loyalty.program', string='Loyalty Program')

    def __init__(self, pool, cr):
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_partner' AND column_name = 'loyalty_program_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_partner '
                       'ADD COLUMN loyalty_program_id integer;')
        return super(Partner, self).__init__(pool, cr)
