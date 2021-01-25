# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

import logging

_logger = logging.getLogger(__name__)


class ProductSetAdd(models.TransientModel):
    _name = 'sale.order.sign'
    _rec_name = 'order_id'
    _description = "Wizard model to sing ready document"

    order_id = fields.Many2one('sale.order', 'Sing order')
    invoice_ids = fields.One2many('account.invoice', string='Sing invoice', compute="_compute_invoice_ids")
    picking_id = fields.Many2one('stock.picking', 'Sing Picking')
    state = fields.Selection([('sale', 'Sale order'),
                               ('stock', 'Stock picking'),
                               ('invoice', 'Invoice')],
                             string='Type form',
                             default='sale',
                             copy=False, index=True,
                             track_visibility='onchange')
    model_type = fields.Char('Model')
    customer_sign = fields.Html('Customer sign', compute="_get_customer_sign")
    customer_signature = fields.Binary(string='Customer acceptance')
    report_sign = fields.Many2one('ir.actions.report', 'Choice report')
    model = fields.Char('Model Name', related='report_sign.model')


    @api.multi
    def _compute_invoice_ids(self):
        for record in self:
            if record.order_id:
                record.invoice_ids = False
                for line in record.order_id.invoice_ids:
                    record.invoice_ids |= line

    def _get_ref_name(self, rcontext):
        if self.report_sign:
            report = self.env['ir.ui.view'].search([('key', '=', self.report_sign.report_name)])
            _logger.info("CHOICE REPORT %s::%s:%s" % (report, rcontext, self.report_sign.report_name))
            if report:
                report_name = self.report_sign.report_name
                for report_line in report:
                    xml = etree.XML(report_line.arch_base)
                    find = etree.XPath("//t[@t-call]")
                    find_arg = etree.XPath("//t[@t-set]")
                    arg = {}
                    for line in find(xml):
                        if line is not None:
                            report_name = line.get("t-call")
                            _logger.info("LINE REPORT %s" % report_name)
                            if report_name.find("web.html_container") < 0 \
                                    or report_name.find("web.external_layout") < 0 \
                                    or report_name.find("web.internal_layout") < 0 \
                                    or report_name.find("l10n_bg_extend.signature") < 0:
                                continue

                    for line in find_arg(xml):
                        if line is not None:
                            _logger.info("ARG %s=%s" % (line.get('t-set'), line.get('t-value')))
                            arg[line.get('t-set')] = safe_eval(line.get('t-value'), rcontext, mode="exec", nocopy=True)
                _logger.info("REPORT %s=>%s::%s:%s" % (report, self.report_sign.report_name, report_name, arg))
                if report_name:
                    return report_name, arg, report.key, report.model
        return 'l10n_bg_extend.report_saleorder_document', False, 'sale.report_saleorder', 'sale.order'

    def _get_set_sign_html(self):
        result = {}
        rcontext = {}
        context = dict(self._context)
        if self.model_type == 'sale.order' and self.order_id:
            active_id = self.order_id and self.order_id.id or self._context.get('default_order_id', False)
            active_model = self.order_id._name
            context = dict(context, active_ids=[active_id], active_model=active_model)
        elif self.model_type == 'account.invoice' and self.invoice_ids:
            context = dict(context, active_ids=self.invoice_ids.ids, active_model=self.invoice_id._name)
        elif self.model_type == 'stock.picking' and self.picking_id:
            context = dict(context, active_ids=[self.picking_id.id], active_model=self.picking_id._name)
        else:
            active_id = self.order_id and self.order_id.id or self._context.get('default_order_id', False)
            active_model = self.order_id._name
            context = dict(context, active_ids=[active_id], active_model=active_model)

        obj = self.env[context['active_model']].browse(context['active_ids'])
        rcontext['doc'] = obj
        rcontext['o'] = obj
        name, arg, report, model = self._get_ref_name(rcontext)
        if arg:
            rcontext.update(arg)
        result['html'] = self.env.ref(name).with_context(context).render(rcontext)
        _logger.info("REPORT EXECUTE %s::%s::%s:%s:%s:%s" % (self.model_type, report, name, arg, context, rcontext))
        return result

    @api.multi
    def _get_customer_sign(self):
        for rec in self:
            rec.customer_sign = rec._get_set_sign_html()['html']

    @api.onchange('report_sign')
    def _onchange_report_sign(self):
        for record in self:
            if record.report_sign:
                record.customer_sign = record._get_set_sign_html()['html']

    @api.onchange('state')
    @api.multi
    def _onchange_state(self):
        for record in self:
            if record.state == 'invoice':
                record.picking_id = False
                record.model_type = 'account.invoice'
            elif record.state == 'stock':
                record.invoice_id = False
                record.model_type = 'stock.picking'
            elif record.state == 'sale':
                record.invoice_id = False
                record.picking_id = False
                record.model_type = 'sale.order'
            return {'domain': {'report_sign': [('model', '=', record.model_type)]}}

    @api.model
    def default_get(self, fields):
        res = super(ProductSetAdd, self).default_get(fields)
        order = self.env['sale.order'].browse(self._context.get('default_order_id', False))
        res.update({'order_id': self._context.get('default_order_id', False),
                    #'invoice_ids': order and order.invoice_ids.ids or False,
                    'customer_signature': self._context.get('default_customer_signature', False),
                    'customer_sign': self._get_set_sign_html()['html']})
        return res

    @api.multi
    def sale_sign_print(self):
        model = self.model_type
        if model == 'sale.order' and self.order_id:
            context = dict(self.env.context or {}, active_ids=[self.order_id.id], active_model=self.order_id._name)
        elif model == 'account.invoice' and self.invoice_id:
            context = dict(self.env.context or {}, active_ids=[self.invoice_id.id], active_model=self.invoice_id._name)
        elif model == 'stock.picking' and self.picking_id:
            context = dict(self.env.context or {}, active_ids=[self.picking_id.id], active_model=self.picking_id._name)
        else:
            context = dict(self.env.context or {}, active_ids=[self.order_id.id], active_model=self.order_id._name)
        name, arg, report, model = self._get_ref_name(context)
        if self.order_id and self.customer_signature:
            self.order_id.write({'customer_signature': self.customer_signature})
        elif self.invoice_ids and self.customer_signature:
            self.invoice_ids.write({'customer_signature': self.customer_signature})
        elif self.picking_id and self.customer_signature:
            self.picking_id.write({'customer_signature': self.customer_signature})

        return {
            'type': 'ir.actions.report',
            'report_name': report,
            'context': context,
        }

    @api.multi
    def sale_sign_save(self):
        if self.order_id and self.customer_signature:
            self.order_id.write({'customer_signature': self.customer_signature})
        elif self.invoice_id and self.customer_signature:
            self.invoice_id.write({'customer_signature': self.customer_signature})
        elif self.picking_id and self.customer_signature:
            self.picking_id.write({'customer_signature': self.customer_signature})
        return {'type': 'ir.actions.act_window_close'}
