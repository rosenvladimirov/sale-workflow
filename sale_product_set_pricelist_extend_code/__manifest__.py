# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale product set clue with price list extend code',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, BioPrint Ltd., Odoo Community Association (OCA)',
    'version': '11.0.1.0.0',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    'summary': "Sale product set and extend price list code",
    'depends': [
        'sale_product_set_pricelist_extend',
        'product_pricelist_extend',
    ],
    'data': [
        'views/product_set.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
