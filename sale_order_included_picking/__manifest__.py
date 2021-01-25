# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order direct access to pickings',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Add functionality to fill pickings data directly from sale order',
    'description': """
    """,
    'depends': ['sale', 'sale_stock', 'stock_quant_manual_assign'],
    'data': [
        'views/sale_order.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
