{
    'name': 'Product set Global Medical Device Nomenclature (GMDN)',
    'category': 'Sales',
    "author" : "Rosen Vladimirov",
    'summary': 'Add product set gmdn',
    'version': '11.0.1.0',
    'description': "",
    'depends': ['sale_product_set', 'l10n_gr_extend'],
    'data': [
        'views/product_set_views.xml',
        'views/report_invoice.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
}
