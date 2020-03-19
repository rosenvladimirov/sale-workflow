# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale order invoicing policy',
    'version': '11.0.1.0',
    'summary': 'Add to sale order possibility to change the product invoce police.',
    'category': 'Sales',
    'author': 'Rosen Vladimmirov, '
              'Bioprint Ltd.',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    "license" : "AGPL-3",
    'depends': ['sale', 'sale_stock'],
    'data': [
        'views/sale_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}