# Copyright 2015 Anybox S.A.S
# Copyright 2016-2020 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class ProductSetTemplateAdd(models.TransientModel):
    _name = "product.set.template.add"
    _rec_name = "product_set_id"
    _description = "Wizard model to add product set into a quotation"

    order_id = fields.Many2one(
        "sale.order.template",
        "Sale Order Template",
        required=True,
        default=lambda self: self.env.context.get("active_id")
        if self.env.context.get("active_model") == "sale.order.template"
        else None,
        ondelete="cascade",
    )
    product_set_id = fields.Many2one(
        "product.set", "Product set", required=True, ondelete="cascade"
    )
    product_set_line_ids = fields.Many2many(
        "product.set.line",
        string="Product set lines",
        required=True,
        store=True,
        ondelete="cascade",
        compute="_compute_product_set_line_ids",
        readonly=False,
    )
    quantity = fields.Float(
        digits="Product Unit of Measure", required=True, default=1.0
    )
    skip_existing_products = fields.Boolean(
        default=False,
        help="Enable this to not add new lines "
             "for products already included in SO lines.",
    )
    reset_product_set = fields.Boolean(
        default=True,
        help="Enable this to not empty rows if choice different product set."
    )

    @api.depends_context("product_set_add__set_line_ids")
    @api.depends("product_set_id")
    def _compute_product_set_line_ids(self):
        line_ids = self.env.context.get("product_set_add__set_line_ids", [])
        lines_from_ctx = self.env["product.set.line"].browse(line_ids)
        for rec in self:
            if rec.product_set_line_ids and not rec.reset_product_set:
                # Passed on creation
                continue
            elif rec.product_set_line_ids and rec.reset_product_set:
                rec.product_set_line_ids = False

            lines = lines_from_ctx.filtered(
                lambda x: x.product_set_id == rec.product_set_id
            )
            if lines:
                # Use the ones from ctx but make sure they belong to the same set.
                rec.product_set_line_ids = lines
            else:
                # Fallback to all lines from current set
                rec.product_set_line_ids = rec.product_set_id.set_line_ids


    def add_set(self):
        """Add product set, multiplied by quantity in sale order line"""
        order_lines = self._prepare_order_lines()
        if order_lines:
            max_sequence = self._get_max_sequence()
            section = [(0, 0, self.product_set_id.prepare_sale_order_template_values(max_sequence + 1))]
            if self.with_context(dict(self._context, create_new_set=True)).order_id.write({"sale_order_template_line_ids": section}):
                product_set_section_id = self.order_id.sale_order_template_line_ids[-1]
                for vals in order_lines:
                    command, key, values = vals
                    values.update({
                        'product_set_section_id': product_set_section_id.id,
                    })
                # _logger.info(f"Preparing sale order line {order_lines}")
                self.with_context(dict(self._context, create_new_set=True)).order_id.write({"sale_order_template_line_ids": order_lines})
        return order_lines

    def _prepare_order_lines(self):
        max_sequence = self._get_max_sequence()
        order_lines = []
        # order_lines.append((0, 0, self.product_set_id.prepare_sale_order_values(max_sequence + 1)))
        for seq, set_line in enumerate(self._get_lines(), start=1):
            values = self.prepare_sale_order_line_data(set_line)
            # When we play with sequence widget on a set of product,
            # it's possible to have a negative sequence.
            # In this case, the line is not added at the correct place.
            # So we have to force it with the order of the line.
            values.update({"sequence": max_sequence + 1 + seq})
            order_lines.append((0, 0, values))
        return order_lines

    def _get_max_sequence(self):
        max_sequence = 0
        if self.order_id.sale_order_template_line_ids:
            max_sequence = max(line.sequence for line in self.order_id.sale_order_template_line_ids)
        return max_sequence

    def _get_lines(self):
        # hook here to take control on used lines
        so_product_ids = self.order_id.sale_order_template_line_ids.mapped("product_id").ids
        for set_line in self.product_set_line_ids:
            if self.skip_existing_products and set_line.product_id.id in so_product_ids:
                continue
            yield set_line

    def prepare_sale_order_line_data(self, set_line, max_sequence=0):
        self.ensure_one()
        line_values = set_line.prepare_sale_order_template_line_values(
            set_line.id, self.order_id, self.quantity, max_sequence=max_sequence
        )
        if set_line.display_type:
            line_values.update(
                {"name": set_line.name, "display_type": set_line.display_type}
            )
        return line_values
