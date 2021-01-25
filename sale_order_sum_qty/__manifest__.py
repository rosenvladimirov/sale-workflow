# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order direct sum of line quantity',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Add total for quantity on lines',
    'description': """
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_order.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
