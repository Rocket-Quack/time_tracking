import json

import frappe
from frappe.tests.utils import FrappeTestCase

from time_tracking.time_tracking.page.weekly_booking.weekly_booking import (
	get_weekly_booking,
	save_weekly_booking,
)


class TestWeeklyBooking(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "require_project_assignment", 0)
		frappe.db.set_single_value("Time Tracking Settings", "enable_holiday_list", 0)

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

	def test_bill_type_keeps_rows_separate(self):
		user = self._make_user("weekly")
		project = self._make_project(f"Weekly-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)

		frappe.set_user(user)
		save_weekly_booking(
			json.dumps(
				{
					"user": user,
					"week_start_date": "2026-04-13",
					"rows": [
						{
							"project": project,
							"bill_type": "Billable",
							"note": "Same note",
							"monday_hours": 1,
							"tuesday_hours": 0,
							"wednesday_hours": 0,
							"thursday_hours": 0,
							"friday_hours": 0,
							"saturday_hours": 0,
							"sunday_hours": 0,
						},
						{
							"project": project,
							"bill_type": "Unbillable",
							"note": "Same note",
							"monday_hours": 1,
							"tuesday_hours": 0,
							"wednesday_hours": 0,
							"thursday_hours": 0,
							"friday_hours": 0,
							"saturday_hours": 0,
							"sunday_hours": 0,
						},
					],
				}
			)
		)

		result = get_weekly_booking(week_start_date="2026-04-13")
		rows = result["rows"]

		self.assertEqual(len(rows), 2)
		self.assertEqual({row["bill_type"] for row in rows}, {"Billable", "Unbillable"})
