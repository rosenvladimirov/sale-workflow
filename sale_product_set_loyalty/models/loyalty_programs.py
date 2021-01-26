# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class LoyaltyRule(models.Model):
    _inherit = 'loyalty.rule'


    product_set_id = fields.Many2one('product.set', string='Product Set', ondelete='restrict')

    @api.multi
    def check_match_ext(self, product, qty, price, **kwargs):
        verify, force_break = super(LoyaltyRule, self).check_match_ext(product, qty, price, **kwargs)
        if force_break:
            return verify, True
        if verify:
            return True, force_break
        if kwargs.get('product_set'):
            for record in self:
                #_logger.info("LOYALTY ROW %s:%s:%s:%s:%s:%s" % ( kwargs.get('product_set'),
                #                                              record.product_set_id,
                #                                              product,
                #                                              record.product_set_id == kwargs['product_set'],
                #                                              record.product_id and (record.product_id == product),
                #                                              record.product_tmpl_id and (record.product_tmpl_id == product.product_tmpl_id)))
                if record.product_set_id != kwargs['product_set']:
                    return False, True
                #_logger.info("EXT %s:%s:%s:%s" % (kwargs, self.product_set_id.name, self.product_set_id == kwargs['product_set'], self.product_id == product))
                if (record.product_set_id == kwargs['product_set']) \
                    and ((record.product_id == product) or (record.product_tmpl_id == product.product_tmpl_id)):
                    _logger.info("LOYALTY last %s" % self.product_set_id)
                    return True, True
        return False, False
