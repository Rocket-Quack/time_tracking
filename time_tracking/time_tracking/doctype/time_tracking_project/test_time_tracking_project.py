from uuid import UUID

import frappe
from frappe.permissions import has_permission
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
	update_project_metrics,
)


class TestTimeTrackingProject(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 0)

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
		user.add_roles("Time Tracking Employee")
		return user.name

	def _make_profile(self, user):
		return (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Profile",
					"user": user,
					"target_period": "Weekly",
					"weekly_target_hours": 40,
					"workdays_per_week": 5,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

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

	def test_unbillable_time_counts_hours_but_not_revenue(self):
		user = self._make_user("metrics")
		self._make_profile(user)
		project = self._make_project(self._unique("Metrics"))
		project.bill_rate = 100
		project.pay_rate = 50
		project.pay_rate_source = "Project"
		project.save(ignore_permissions=True)

		for bill_type in ("Billable", "Unbillable"):
			frappe.get_doc(
				{
					"doctype": "Time Booking",
					"time_tracking_profile": user,
					"date": today(),
					"project": project.name,
					"bill_type": bill_type,
					"duration_minutes": 60,
					"notes": f"{bill_type} booking",
				}
			).insert(ignore_permissions=True)

		update_project_metrics(project.name)
		project.reload()

		self.assertEqual(project.actual_hours, 2)
		self.assertEqual(project.actual_amount, 100)
		self.assertEqual(project.actual_pay_amount, 100)

	def test_group_metrics_include_direct_group_bookings(self):
		user = self._make_user("group-metrics")
		self._make_profile(user)
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 1)

		group = self._make_project(self._unique("Metrics Group"), is_group=1)
		group.bill_rate = 100
		group.pay_rate = 50
		group.pay_rate_source = "Project"
		group.save(ignore_permissions=True)

		child = self._make_project(self._unique("Metrics Child"), parent=group.name, is_group=0)
		child.bill_rate = 100
		child.pay_rate = 50
		child.pay_rate_source = "Project"
		child.save(ignore_permissions=True)

		profile = frappe.get_doc("Time Tracking Profile", user)
		profile.append("project_assignments", {"project": group.name, "active": 1})
		profile.save(ignore_permissions=True)

		for project_name in (group.name, child.name):
			frappe.get_doc(
				{
					"doctype": "Time Booking",
					"time_tracking_profile": user,
					"date": today(),
					"project": project_name,
					"bill_type": "Billable",
					"duration_minutes": 60,
					"notes": f"{project_name} booking",
				}
			).insert(ignore_permissions=True)

		update_project_metrics(group.name)
		group.reload()

		self.assertEqual(group.actual_hours, 2)
		self.assertEqual(group.actual_amount, 200)
		self.assertEqual(group.actual_pay_amount, 100)

	def test_employee_has_no_direct_project_read_access(self):
		user = self._make_user("projectread")
		project = self._make_project(self._unique("Restricted Read"))

		frappe.set_user(user)

		self.assertFalse(has_permission("Time Tracking Project", "read", doc=project.name))
		with self.assertRaises(frappe.PermissionError):
			frappe.client.get("Time Tracking Project", project.name)
