from uuid import UUID

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestTimeTrackingProject(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _unique(self, prefix):
		return f"{prefix}-{frappe.generate_hash(length=8)}"

	def _make_project(self, name, parent=None, is_group=0):
		doc = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": name,
				"parent_time_tracking_project": parent,
				"is_group": is_group,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def test_project_name_duplicate_fails(self):
		parent = self._make_project(self._unique("Parent"), is_group=1)
		child_name = self._unique("Child")
		self._make_project(child_name, parent=parent.name)

		with self.assertRaises(Exception):
			self._make_project(child_name, parent=parent.name)

	def test_temporary_frontend_name_is_replaced_with_uuid(self):
		doc = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"name": "new-time-tracking-project-gsdzaapdej",
				"project_name": self._unique("UI Project"),
			}
		)
		doc.insert(ignore_permissions=True)

		self.assertNotEqual(doc.name, "new-time-tracking-project-gsdzaapdej")
		self.assertFalse(doc.name.startswith("new-time-tracking-project-"))
		UUID(doc.name)
