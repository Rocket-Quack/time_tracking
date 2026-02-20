import frappe
from frappe.tests.utils import FrappeTestCase


class TestRoleHierarchy(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_user(self, prefix):
		email = f"{prefix}-{frappe.generate_hash(length=8)}@example.com"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Test",
				"last_name": prefix,
				"enabled": 1,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		return user.name

	def _set_user_roles(self, user, roles):
		doc = frappe.get_doc("User", user)
		doc.set("roles", [])
		for role in roles:
			doc.append("roles", {"role": role})
		doc.save(ignore_permissions=True)
		return frappe.get_doc("User", user)

	def test_manager_inherits_employee_role(self):
		user = self._make_user("manager")
		doc = self._set_user_roles(user, ["Time Tracking Manager"])
		role_names = {row.role for row in doc.roles if row.role}

		self.assertIn("Time Tracking Manager", role_names)
		self.assertIn("Time Tracking Employee", role_names)

	def test_admin_inherits_manager_and_employee_roles(self):
		user = self._make_user("admin")
		doc = self._set_user_roles(user, ["Time Tracking Admin"])
		role_names = {row.role for row in doc.roles if row.role}

		self.assertIn("Time Tracking Admin", role_names)
		self.assertIn("Time Tracking Manager", role_names)
		self.assertIn("Time Tracking Employee", role_names)
