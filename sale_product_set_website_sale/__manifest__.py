# Copyright 2019 dXFactory Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale product set website sale',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'version': '11.0.1.0.0',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    'summary': "Sale product set on website e-shop",
    'depends': [
        'sale_product_set',
        'website_sale',
        'website_sale_extend',
        'partner_multi_relation',
    ],
    'data': [
        'views/website_sale_sets_template.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
