# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sale product set include fleets',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov',
    'version': '11.0.1.0.0',
    'summary': "Sale product set include fleets",
    'depends': [
        'sale_product_set',
    ],
    'data': [
        'views/product_set.xml',
        'views/fleet_vehicle_model_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
