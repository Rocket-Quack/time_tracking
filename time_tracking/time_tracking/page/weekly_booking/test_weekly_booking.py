import json

import frappe
from frappe.tests.utils import FrappeTestCase

from time_tracking.time_tracking.page.weekly_booking.weekly_booking import (
	get_assigned_projects,
	get_weekly_booking,
	save_weekly_booking,
)


class TestWeeklyBooking(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "require_project_assignment", 0)
		frappe.db.set_single_value("Time Tracking Settings", "enable_holiday_list", 0)
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 0)

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

	def test_project_only_row_is_rejected(self):
		user = self._make_user("project-only")
		project = self._make_project(f"ProjectOnly-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)

		frappe.set_user(user)
		with self.assertRaisesRegex(frappe.ValidationError, "Note and time are required for bookings."):
			save_weekly_booking(
				json.dumps(
					{
						"user": user,
						"week_start_date": "2026-04-13",
						"rows": [
							{
								"project": project,
								"note": "",
								"monday_hours": 0,
								"tuesday_hours": 0,
								"wednesday_hours": 0,
								"thursday_hours": 0,
								"friday_hours": 0,
								"saturday_hours": 0,
								"sunday_hours": 0,
							}
						],
					}
				)
			)

	def test_project_and_note_without_time_is_rejected(self):
		user = self._make_user("note-no-time")
		project = self._make_project(f"NoTime-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)

		frappe.set_user(user)
		with self.assertRaisesRegex(frappe.ValidationError, "Time is required for bookings."):
			save_weekly_booking(
				json.dumps(
					{
						"user": user,
						"week_start_date": "2026-04-13",
						"rows": [
							{
								"project": project,
								"note": "No time yet",
								"monday_hours": 0,
								"tuesday_hours": 0,
								"wednesday_hours": 0,
								"thursday_hours": 0,
								"friday_hours": 0,
								"saturday_hours": 0,
								"sunday_hours": 0,
							}
						],
					}
				)
			)

	def test_time_without_note_is_rejected(self):
		user = self._make_user("time-no-note")
		project = self._make_project(f"NoNote-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)

		frappe.set_user(user)
		with self.assertRaisesRegex(frappe.ValidationError, "Note is required for bookings."):
			save_weekly_booking(
				json.dumps(
					{
						"user": user,
						"week_start_date": "2026-04-13",
						"rows": [
							{
								"project": project,
								"note": "",
								"monday_hours": 1,
								"tuesday_hours": 0,
								"wednesday_hours": 0,
								"thursday_hours": 0,
								"friday_hours": 0,
								"saturday_hours": 0,
								"sunday_hours": 0,
							}
						],
					}
				)
			)

	def test_group_project_is_available_and_bookable_when_setting_enabled(self):
		user = self._make_user("weekly-group")
		group = (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Project",
					"project_name": f"WeeklyGroup-{frappe.generate_hash(length=6)}",
					"is_group": 1,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		self._make_profile(user, group)
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 1)

		frappe.set_user(user)
		projects = get_assigned_projects(user=user)
		self.assertIn(group, {project.name for project in projects})

		save_weekly_booking(
			json.dumps(
				{
					"user": user,
					"week_start_date": "2026-04-13",
					"rows": [
						{
							"project": group,
							"note": "Grouped work",
							"monday_hours": 1,
							"tuesday_hours": 0,
							"wednesday_hours": 0,
							"thursday_hours": 0,
							"friday_hours": 0,
							"saturday_hours": 0,
							"sunday_hours": 0,
						}
					],
				}
			)
		)

		result = get_weekly_booking(week_start_date="2026-04-13")
		self.assertTrue(any(row["project"] == group for row in result["rows"]))
