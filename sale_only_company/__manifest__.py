# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order only by partner like company',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'When made Sales Orders from contact partner, when confirm it to switch to partner',
    'description': """
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_views.xml',
        'views/account_invoice_views.xml',
        'views/account_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': '_upadate_email_templates',
}
