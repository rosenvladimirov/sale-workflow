# Copyright 2026 Rosen Vladimirov, BioPrint Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import Command, api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stock_int_picking_ids = fields.One2many(
        "stock.picking",
        compute="_compute_stock_int_picking_ids",
        inverse="_set_stock_int_picking_ids",
        search="_search_stock_int_picking_ids",
        string="Internal Transfers ref.",
    )
    location_int_display_name = fields.Char(
        string="Int. source Picking Info", compute="_compute_location_int_display_name")
    location_dest_int_display_name = fields.Char(
        string="Int. dest Picking Info", compute="_compute_location_int_display_name")
    int_delivery_count = fields.Integer(
        string="Internal delivery Orders", compute="_get_int_delivery_count")

    @api.depends("stock_int_picking_ids")
    def _get_int_delivery_count(self):
        for order in self:
            order.int_delivery_count = len(order.stock_int_picking_ids)

    @api.depends("order_line.stock_int_picking_ids")
    def _compute_stock_int_picking_ids(self):
        # 🚨 ЗАВАРЕН ДЕФЕКТ, видян в продукция. Старият код правеше само
        # `record.stock_int_picking_ids |= ...` в цикъл, БЕЗ да присвои полето
        # първо. При поръчка без нито един ред с вътрешен пикинг цикълът не се
        # изпълнява, полето остава неприсвоено и ORM-ът гърми с
        # „Compute method failed to assign stock_int_picking_ids".
        # Оттам идваше и падането при четене на всички полета на записа.
        # Липсваше и `@api.depends` — полето не се преизчисляваше при промяна.
        for record in self:
            record.stock_int_picking_ids = record.order_line.stock_int_picking_ids

    def _set_stock_int_picking_ids(self):
        for record in self:
            if not record.stock_int_picking_ids:
                record.order_line.filtered("stock_int_picking_ids").write(
                    {"stock_int_picking_ids": [Command.clear()]})
            else:
                lines = record.order_line.filtered(lambda r: not r.stock_int_picking_ids)
                lines.write({
                    "stock_int_picking_ids": [Command.set(record.stock_int_picking_ids.ids)]})

    @api.depends("order_line.stock_int_picking_ids")
    def _compute_location_int_display_name(self):
        for record in self:
            pickings = record.order_line.stock_int_picking_ids
            names = pickings.mapped("location_id.name")
            dest_names = pickings.mapped("location_dest_id.name")
            record.location_int_display_name = " - ".join(names) if names else False
            record.location_dest_int_display_name = " - ".join(dest_names) if dest_names else False

    def _search_stock_int_picking_ids(self, operator, value):
        # 🚨 Старият код връщаше домейн върху САМОТО поле, което е рекурсия:
        # ORM-ът пак вика този search метод. Търсенето минава през реда, който
        # държи истинската релация.
        if operator == "like":
            operator = "ilike"
        return [("order_line.stock_int_picking_ids", operator, value)]

    def _prepare_sale_order_line_picking_data(self, line, picking):
        return {
            "order_id": self.id,
            "product_id": line.product_id.id,
            # 🚨 `sale.order.line.product_uom` е `product_uom_id` в 19.0.
            "product_uom_id": line.product_uom.id,
            # 🚨 `stock.move.product_qty` е количеството, преизчислено в мерната
            # единица по подразбиране на АРТИКУЛА, а тук се сдвоява с мярката на
            # ДВИЖЕНИЕТО. Вярната двойка е `product_uom_qty` — тя по определение
            # е изразена в `product_uom`. Старият код мълчаливо смесваше двете
            # и даваше грешно количество при мярка, различна от базовата.
            "product_uom_qty": line.product_uom_qty,
            "stock_int_picking_ids": [Command.set([picking.id])],
        }

    def prepare_sale_order_line_picking_data(self, pickings):
        self.ensure_one()
        order_line = []
        for picking in pickings:
            # 🚨 `stock.picking.move_lines` е преименувано на `move_ids` още
            # преди 16.0. Портът 11→16 е поправил другия файл и е пропуснал
            # този, тъй че визардът е мъртъв вече две мажорни версии — и точно
            # затова никой не се е оплакал.
            for line in picking.move_ids:
                # 🚨 `default_get()` беше извикано БЕЗ задължителния аргумент —
                # TypeError. Изобщо не трябва: `Command.create` минава през
                # `create()` на реда, който сам попълва подразбиранията.
                order_line.append(
                    Command.create(self._prepare_sale_order_line_picking_data(line, picking)))
        # 🚨 `return` беше ВЪТРЕ в цикъла — от целия избор влизаше само първият
        # пикинг.
        return False, order_line

    def action_view_int_delivery(self):
        return self._get_action_int_view_picking(self.stock_int_picking_ids)

    def _get_action_int_view_picking(self, pickings):
        """Отваря вътрешните трансфери — списък при много, форма при един."""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref("stock.view_picking_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = pickings.id
        else:
            return False
        picking_id = pickings.filtered(lambda p: p.picking_type_id.code == "internal")
        picking_id = picking_id[0] if picking_id else pickings[0]
        cleaned_context = {k: v for k, v in self.env.context.items() if k != "form_view_ref"}
        action["context"] = dict(
            cleaned_context,
            default_partner_id=self.partner_id.id,
            default_picking_type_id=picking_id.picking_type_id.id,
            default_origin=self.name,
            # 🚨 `default_group_id` е МАХНАТ: в 19.0 `stock.picking` няма
            # `group_id` — `procurement.group` отпадна. Обръщението гърмеше с
            # AttributeError при всяко отваряне на действието.
        )
        return action


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_int_picking_ids = fields.Many2many(
        "stock.picking",
        "sale_order_line_int_picking_rel",
        "so_line_id",
        "picking_line_id",
        string="Internal Transfers ref.",
    )
    order_partner_shipping_id = fields.Many2one(
        related="order_id.partner_shipping_id", store=True, string="Customer")
