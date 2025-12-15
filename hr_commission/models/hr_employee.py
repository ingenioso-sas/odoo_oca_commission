# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, exceptions, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    agent_ids = fields.One2many(
        comodel_name="res.partner",
        inverse_name="employee_id",
        string="Related agent",
    )
    agents_count = fields.Integer(
        compute="_compute_agents_count",
        string="Agents",
    )

    @api.depends("agent_ids")
    def _compute_agents_count(self):
        for record in self:
            record.agents_count = len(record.agent_ids)

    def _get_or_create_commission(self):
        commission_model = self.env["sale.commission"]
        commission = commission_model.search([], limit=1)
        if not commission:
            commission = commission_model.create({
                "name": "Default",
            })
        return commission

    def create_agent(self):
        self.ensure_one()
        commission = self._get_or_create_commission()
        agent = self.env["res.partner"].create({
            "name": self.name,
            "employee_id": self.id,
            "agent_type": "salesman",
            "commission_id": commission.id,
            "agent": True,
        })
        return {
            "name": _("Agent"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "res.partner",
            "res_id": agent.id,
        }

    def action_view_agents(self):
        self.ensure_one()
        return {
            "name": _("Agents"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "res.partner",
            "domain": [("id", "in", self.agent_ids.ids)],
        }

    def write(self, vals):
        """Check if there's an agent linked to that employee."""
        if not vals.get("user_id"):
            salesmen = self.mapped("user_id.partner_id").filtered(
                lambda x: x.agent_type == "salesman"
            )
            if salesmen:
                raise exceptions.ValidationError(
                    _(
                        "You can't remove the user, as it's linked to a commission agent."
                    )
                )
        return super().write(vals)
