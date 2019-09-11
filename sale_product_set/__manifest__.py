# Copyright 2019 dXFactory Ltd.
# Copyright 2015 Anybox
# Copyright 2018 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Sale product set',
    'category': 'Sale',
    'license': 'AGPL-3',
    'author': 'Rosen Vladimirov, dXFactory Ltd., Anybox, Odoo Community Association (OCA)',
    'version': '11.0.3.0.0',
    'website': 'https://github.com/rosenvladimirov/sale-workflow',
    'summary': "Sale product set",
    'depends': [
        'account',
        'sale',
        'product',
        'purchase',
        'stock',
    ],
    'data': [
        'data/product_set_data.xml',
        'security/sale_set_security.xml',
        'security/ir.model.access.csv',
        'views/product_set.xml',
        'views/product.xml',
        'wizard/product_set_add.xml',
        'views/sale_order.xml',
        'views/purchase_views.xml',
        'views/account_invoice_view.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'views/product_pricelist_views.xml',
        'views/invoice_report_templates.xml',
        'views/sale_report_templates.xml',
        'views/report_invoice.xml',
        'report/sale_report.xml',
    ],
    'demo': [
        'demo/product_set.xml',
        'demo/product_set_line.xml',
    ],
    'installable': True,
}
