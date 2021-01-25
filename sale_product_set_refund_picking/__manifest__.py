# Copyright 2019 dXFactory Ltd.
# Copyright 2015 Anybox
# Copyright 2018 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale product set refund picking',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, dXFactory Ltd., Anybox, Odoo Community Association (OCA)',
    'version': '11.0.1.0.0',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    'summary': "Sale product set",
    'depends': [
        'stock',
        'sale_product_set',
    ],
    'data': [
        'wizard/stock_picking_return_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
