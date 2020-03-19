# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product sets in Loyalty Programs',
    'version': '11.0.0.1.0',
    'category': 'Sale',
    'summary': 'Add filter by product set on Loyalty Programs',
    'author': 'Rosen Vladimirov',
    'depends': ['sale', 'loyalty_program', 'sale_product_set'],
    'data': [
        'views/loyalty_program_views.xml',
        'views/product_set_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}