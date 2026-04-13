import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from time_tracking.time_tracking.report.service_report.service_report import execute


class TestServiceReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "require_project_assignment", 0)
		self.project = self._make_project(f"Report-{frappe.generate_hash(length=6)}")
		self.user_a = self._make_user("report-a")
		self.user_b = self._make_user("report-b")
		self._make_profile(self.user_a, self.project)
		self._make_profile(self.user_b, self.project)
		self._make_booking(self.user_a, self.project, "Own booking")
		self._make_booking(self.user_b, self.project, "Foreign booking")

	def _unique_email(self, prefix):
		return f"{prefix}-{frappe.generate_hash(length=8)}@example.com"

	def _make_user(self, prefix):
		email = self._unique_email(prefix)
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

	def _make_project(self, name):
		return (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Project",
					"project_name": name,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def _make_profile(self, user, project):
		return (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Profile",
					"user": user,
					"target_period": "Weekly",
					"weekly_target_hours": 40,
					"workdays_per_week": 5,
					"project_assignments": [{"project": project, "active": 1}],
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def _make_booking(self, user, project, note):
		frappe.set_user(user)
		frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": project,
				"bill_type": "Unbillable" if "Foreign" in note else "Billable",
				"duration_minutes": 60,
				"notes": note,
			}
		).insert(ignore_permissions=True)
		frappe.set_user("Administrator")

	def test_employee_only_sees_own_bookings(self):
		frappe.set_user(self.user_a)

		columns, rows = execute({"period": "Day", "date": today(), "user": self.user_b})

		self.assertTrue(columns)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["user"], self.user_a)
		self.assertEqual(rows[0]["note"], "Own booking")
		self.assertEqual(rows[0]["bill_type"], "Billable")

	def test_admin_can_filter_other_user(self):
		frappe.set_user("Administrator")

		columns, rows = execute({"period": "Day", "date": today(), "user": self.user_b})

		self.assertTrue(columns)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["user"], self.user_b)
		self.assertEqual(rows[0]["note"], "Foreign booking")
		self.assertEqual(rows[0]["bill_type"], "Unbillable")
