# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    website_login_note = fields.Text(string='Default SingUp Terms', translate=True)

    def __init__(self, pool, cr):
        cr.execute("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'res_company' AND column_name = 'website_login_note'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE res_company '
                       'ADD COLUMN website_login_note text;')
        return super(ResCompany, self).__init__(pool, cr)
