# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Sale Order Line Description to Picking",
    "version": "11.0.1.0.0",
    "author": "Rosen Vladimirov, "
              "dXFactory Ltd.",
    "website": "https://www.dxfactory.eu/",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "stock",
    ],
    "data": [
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
