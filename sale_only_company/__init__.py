# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from odoo.api import Environment, SUPERUSER_ID


def Environment_upadate_email_templates(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    model_id = env['ir.model'].search([('name', '=', 'sale.order')])
    id = env.ref('sale.email_template_edi_sale')
    mail = env['mail.template'].search([('model_id', '=', model_id), ('id', '=', id)])
    if mail:
        mail.write({'partner_to': '${object.partner_contact_id.id}'})
