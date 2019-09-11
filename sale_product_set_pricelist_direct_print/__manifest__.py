{
    'name': 'Product Sets on Pricelist Direct Print',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, dXFactory Ltd.',
    'version': '11.0.1.0.0',
    'summary': "Product Sets on Pricelist Direct Print",
    'depends': [
            'sale_product_set',
            'product_pricelist_direct_print',
        ],
    'data': [
        'views/report_product_pricelist.xml',
        'wizards/product_pricelist_print_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
}
