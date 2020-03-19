# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales order Customer side',
    'version': '11.0.1.0',
    'category': 'Sales',
    'summary': 'Add summary from customer PO',
    'description': """
    """,
    'depends': ['sale', 'stock', 'account', 'web_widget_many2many_tags_open'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        #'views/stock_picking_views.xml',
        'views/account_invoice_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
