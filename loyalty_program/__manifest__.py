# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Loyalty Program on sales',
    'version': '11.0.0.1.0',
    'category': 'Sale',
    'sequence': 30,
    'summary': 'Loyalty Program for the Point of Sale and Sales',
    'description': """
This module allows you to define a loyalty program in
the point of sale and sales, where the customers earn loyalty points
and get rewards.
""",
    'author': 'Rosen Vladimirov',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'security/loyalty_programs_security.xml',
        'views/loyalty_program_views.xml',
        'views/sale_views.xml',
        'views/res_partner_views.xml',
        'views/product.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}