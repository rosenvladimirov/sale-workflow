# © 2020 Rosen Vladimirov
# © 2016 OdooMRP team
# © 2016 AvanzOSC
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Eficent Business and IT Consulting Services, S.L.
# Copyright 2017 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Sale Order Line Date",
    "version": "11.0.1.0.0",
    "author": "Rosen Vladimirov,"
              "OdooMRP team,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Odoo Community Association (OCA)",
    "website": "https://odoo-community.org/",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": [
        "sale_order_dates",
        "datetime_formatter",
    ],
    "data": [
        "views/sale_order_view.xml",
        'views/report_sale_templates.xml',
    ],
    "installable": True,
}
