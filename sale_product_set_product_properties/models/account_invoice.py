# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def set_all_print_properties(self):
        super(AccountInvoice, self).set_all_print_properties()
        print_ids = False
        for record in self:
            for r in record.invoice_line_ids.mapped('product_set_id'):
                #_logger.info("LINE %s" % r)
                if print_ids:
                    print_ids |= r.product_properties_ids
                else:
                    print_ids = r.product_properties_ids
            #_logger.info("PROPERTIES %s" % print_ids)
            if print_ids:
                record.print_properties = [(0, False, {'name': x.name.id, 'order_id': self.id, 'print': True, 'sequence': x.sequence}) for x in print_ids]
