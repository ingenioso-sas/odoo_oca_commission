# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import exceptions
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestHrCommission(common.TransactionCase):
    def setUp(self):
        super(TestHrCommission, self).setUp()
        self.employee = self.env["hr.employee"].create({"name": "Test employee"})
        self.user = self.env["res.users"].create(
            {"name": "Test user", "login": "test_hr_commission@example.org"}
        )
        self.partner = self.user.partner_id
        self.commission = self.env["sale.commission"].create(
            {"name": "Test Commission",}
        )

    def test_onchange_employee_id(self):
        self.partner.employee_id = self.employee
        self.partner._onchange_employee_id()
        self.assertFalse(self.partner.user_id)
        self.employee.user_id = self.user
        self.partner._onchange_employee_id()
        self.assertEqual(self.partner.user_id, self.user)

    def test_create_agent(self):
        action = self.employee.create_agent()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "res.partner")
        agent = self.env["res.partner"].browse(action["res_id"])
        self.assertEqual(agent.name, self.employee.name)
        self.assertEqual(agent.employee_id, self.employee)
        self.assertEqual(agent.agent_type, "salesman")

    def test_create_agent_no_commission(self):
        self.commission.unlink()
        action = self.employee.create_agent()
        agent = self.env["res.partner"].browse(action["res_id"])
        self.assertIsNot(agent.commission_id.id, False)

    def test_action_view_agents(self):
        self.employee.create_agent()
        action = self.employee.action_view_agents()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "res.partner")
        self.assertEqual(action["view_mode"], "tree,form")
        self.assertEqual(len(action["domain"][0][2]), 1)

    def test_write(self):
        self.employee.user_id = self.user
        self.partner.agent_type = "salesman"
        with self.assertRaises(exceptions.ValidationError):
            self.employee.write({"user_id": False})

    def test_compute_agents_count(self):
        self.assertEqual(self.employee.agents_count, 0)
        self.employee.create_agent()
        self.assertEqual(self.employee.agents_count, 1)

    def test_check_employee(self):
        with self.assertRaises(exceptions.ValidationError):
            self.env["res.partner"].create(
                {"name": "Test Partner", "agent_type": "salesman", "agent": True}
            )

    def test_compute_employee(self):
        self.partner.agent_type = "salesman"
        self.partner._compute_employee()
        self.assertFalse(self.partner.employee)
        self.partner.employee_id = self.employee
        self.partner._compute_employee()
        self.assertTrue(self.partner.employee)

    def test_onchange_agent_type_hr_commission(self):
        self.partner.agent_type = "salesman"
        self.partner._onchange_agent_type_hr_commission()
        self.assertTrue(self.partner.employee)
        self.partner.agent_type = "not_agent"
        self.partner._onchange_agent_type_hr_commission()
        self.assertFalse(self.partner.employee)
