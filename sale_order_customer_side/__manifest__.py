# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order Customer side',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Add summary from customer PO',
    'description': """
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
