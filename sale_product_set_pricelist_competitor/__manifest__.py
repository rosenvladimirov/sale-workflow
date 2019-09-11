# Copyright 2015 Anybox
# Copyright 2018 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Competitor Price list for sale product set',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov',
    'version': '11.0.1.0.0',
    'summary': "Competitor Sale product set",
    'depends': [
            'sale_product_set',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_set_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
