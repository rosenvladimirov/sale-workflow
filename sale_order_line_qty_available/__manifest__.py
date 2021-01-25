# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order line qty available',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Show in Sale order line available qty for product',
    'description': """
    """,
    'depends': ['sale', 'sale_stock', 'web_notify'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
