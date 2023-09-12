# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, exceptions, models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    agent_id = fields.One2many(
        comodel_name="res.partner",         
        inverse_name="employee_id",
        string='Agente asociado.',
        help="Agente asociado."
        #domain = [('employee_id','!=', 'NULL')]
    )

    def write(self, vals):
        """Check if there's an agent linked to that employee."""
        if "user_id" in vals and not vals["user_id"]:
            for emp in self:
                if emp.user_id.partner_id.agent_type == "salesman":
                    raise exceptions.ValidationError(
                        _(
                            "You can't remove the user, as it's linked to "
                            "a commission agent."
                        )
                    )
        return super().write(vals)
