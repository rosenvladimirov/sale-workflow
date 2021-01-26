# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale product set show detailed lines',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, '
              'BioPrint Ltd., '
              'Odoo Community Association (OCA)',
    'version': '11.0.1.0.0',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    'summary': "Sale product set add button for detailed lines",
    'depends': [
        'stock',
        'account',
        'sale',
        'purchase',
        'sale_product_set',
    ],
    'data': [
        'views/stock_move_line_views.xml',
        'views/stock_picking_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
