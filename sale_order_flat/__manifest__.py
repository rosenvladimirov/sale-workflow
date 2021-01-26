# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order flat mode',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Flad views for sale order',
    'description': """
    """,
    'depends': ['sale', 'hospital'],
    'data': [
        'views/sale_order_flat_template.xml',
        'views/sale_order.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
