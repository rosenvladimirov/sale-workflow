# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order import from purchase order',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Add new wizard to import all detailed data from sale order',
    'description': """
    """,
    'depends': ['sale'],
    'data': [
        'wizard/sale_order_import_po.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
