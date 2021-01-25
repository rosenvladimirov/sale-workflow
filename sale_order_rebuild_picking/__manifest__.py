# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Rebuild qty for picking',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Compare and rebuild qty in sale',
    'description': """
    """,
    'depends': ['sale', 'sale_stock'],
    'data': [
        'views/sale_order.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
