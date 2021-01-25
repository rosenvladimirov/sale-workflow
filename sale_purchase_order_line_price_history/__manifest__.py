# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale and Purchase order line price history",
    "version": "11.0.1.0.0",
    "category": "Sales Management",
    "author": "Rosen Vladimirov (BioPrint Ltd., "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow/",
    "license": "AGPL-3",
    "depends": [
        "sale_order_line_price_history",
        "purchase_order_line_price_history",
    ],
    "data": [
        "wizards/sale_orderLine_price_history.xml",
    ],
    "installable": True,
}
