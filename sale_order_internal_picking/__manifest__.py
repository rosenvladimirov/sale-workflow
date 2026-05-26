# Copyright 2025 Your Company Name
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Sales Order Link with Internal Picking',
    'version': '18.0.1.0.0',
    'category': 'Sales/Inventory',
    'summary': 'Add extra info for transfers to internal locations',
    'author': 'Your Company, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'license': 'AGPL-3',
    'description': """
Sales Order Link with Internal Picking
======================================
This module adds functionality to link sales orders with internal transfers.
    """,
    'depends': [
        'sale',
        'stock',
        'account',
        'web_m2x_options',
        'stock_location_consignment_owner',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_order_import_picking.xml',
        'views/sale_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_view.xml',
    ],
    'demo': [],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {},
}
