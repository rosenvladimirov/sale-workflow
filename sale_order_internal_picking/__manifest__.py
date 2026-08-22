# Copyright 2026 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sales order link with internal picking",
    "version": "19.0.1.0.2",
    "category": "Sales",
    "summary": "Add extra info for transfers to internal locations",
    "author": "Rosen Vladimirov, BioPrint Ltd.",
    # 🚨 16.0 версията НЕ обявяваше лиценз изобщо — Odoo подразбира LGPL-3, а
    # модулът зависи от `stock_location_consignment_owner`, който е AGPL-3.
    # Тоест мълчанието беше нарушение. Обявено изрично.
    "license": "AGPL-3",
    "depends": [
        "sale",
        "stock",
        "account",
        "web_m2x_options",
        "stock_location_consignment_owner",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_order_import_picking.xml",
        "views/sale_views.xml",
        "views/stock_picking_views.xml",
        # 🚩 `views/account_move_view.xml` НЕ се пренася: сочи модела
        # `account.invoice`, който не съществува от 13.0 насам. Беше
        # закоментиран и в 16.0 — мъртъв файл, не липсваща функционалност.
    ],
    "installable": True,
    "auto_install": False,
}
