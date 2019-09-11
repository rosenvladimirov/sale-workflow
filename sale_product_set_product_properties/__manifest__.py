# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product properties on product sets',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'sequence': 5,
    'summary': 'Product properties on product sets',
    'description': """
Product set informations about Product properties
""",
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'depends': [
                'product_properties',
                'sale_product_set',
                ],
    'data': [
            'views/sale_views.xml',
            'views/product_set_views.xml',
            'views/product_properties_linename_templates.xml',
            'views/sale_report_templates.xml',
            #'views/sale_report_templates.xml',
            ],
    'demo': [],
    'installable': True,
}
