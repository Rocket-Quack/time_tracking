import csv
import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import load_workbook

from time_tracking.time_tracking.page.time_tracking_export.time_tracking_export import (
	_get_project_names,
	export_bookings,
)


class TestTimeTrackingExport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "require_project_assignment", 0)
		frappe.db.set_single_value("Time Tracking Settings", "enable_holiday_list", 0)
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 0)

	def _unique_email(self, prefix):
		return f"{prefix}-{frappe.generate_hash(length=8)}@example.com"

	def _make_user(self, prefix, first_name=None):
		email = self._unique_email(prefix)
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name or prefix,
				"last_name": "Export",
				"enabled": 1,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		user.add_roles("Time Tracking Employee")
		return user.name

	def _make_project(self, name, parent=None, is_group=0):
		return (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Project",
					"project_name": name,
					"parent_time_tracking_project": parent,
					"is_group": is_group,
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

	def _make_booking(self, user, project, booking_date, duration_minutes, notes):
		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": booking_date,
				"project": project,
				"duration_minutes": duration_minutes,
				"notes": notes,
			}
		)
		booking.insert(ignore_permissions=True)
		frappe.set_user("Administrator")
		return booking

	def _run_export(self, **kwargs):
		frappe.set_user("Administrator")
		frappe.local.response = frappe._dict()
		export_bookings(**kwargs)
		return frappe.local.response

	def test_group_project_filter_keeps_group_without_children(self):
		group = self._make_project(f"ExportGroup-{frappe.generate_hash(length=6)}", is_group=1)
		child = self._make_project(
			f"ExportChild-{frappe.generate_hash(length=6)}",
			parent=group,
			is_group=0,
		)

		self.assertEqual(_get_project_names(group, include_children=0), [group])
		self.assertEqual(_get_project_names(group, include_children=1), [group, child])

	def test_csv_export_sorts_by_date_then_employee(self):
		booking_date = "2026-04-01"
		user_alice = self._make_user("alice", first_name="Alice")
		user_bob = self._make_user("bob", first_name="Bob")
		project_zeta = self._make_project(f"Zeta-{frappe.generate_hash(length=6)}")
		project_alpha = self._make_project(f"Alpha-{frappe.generate_hash(length=6)}")
		self._make_profile(user_alice, project_zeta)
		self._make_profile(user_bob, project_alpha)
		self._make_booking(user_alice, project_zeta, booking_date, 60, "Alice booking")
		self._make_booking(user_bob, project_alpha, booking_date, 60, "Bob booking")

		response = self._run_export(
			export_format="CSV",
			from_date=booking_date,
			to_date=booking_date,
			date_format="YYYY-MM-DD",
			decimal_separator=".",
			duration_format="Decimal Hours",
		)

		rows = list(csv.reader(io.StringIO(response["filecontent"].decode("utf-8")), delimiter=","))
		self.assertEqual(rows[0][1], "Employee")
		self.assertEqual(rows[1][1], "Alice")
		self.assertEqual(rows[2][1], "Bob")

	def test_csv_export_uses_semicolon_for_decimal_comma(self):
		booking_date = "2026-04-02"
		user = self._make_user("decimal-comma", first_name="Dora")
		project = self._make_project(f"Decimal-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)
		self._make_booking(user, project, booking_date, 75, "Decimal booking")

		response = self._run_export(
			export_format="CSV",
			from_date=booking_date,
			to_date=booking_date,
			date_format="YYYY-MM-DD",
			decimal_separator=",",
			duration_format="Decimal Hours",
		)

		content = response["filecontent"].decode("utf-8")
		self.assertIn(";", content.splitlines()[0])
		rows = list(csv.reader(io.StringIO(content), delimiter=";"))
		self.assertEqual(rows[1][5], "1,25")

	def test_xlsx_export_writes_decimal_hours_as_numeric_cells(self):
		booking_date = "2026-04-03"
		user = self._make_user("xlsx-numeric", first_name="Nina")
		project = self._make_project(f"Numeric-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)
		self._make_booking(user, project, booking_date, 75, "Numeric booking")

		response = self._run_export(
			export_format="XLSX",
			from_date=booking_date,
			to_date=booking_date,
			date_format="YYYY-MM-DD",
			decimal_separator=",",
			duration_format="Decimal Hours",
		)

		workbook = load_workbook(io.BytesIO(response["filecontent"]))
		worksheet = workbook.active
		duration_cell = worksheet["F2"]
		self.assertEqual(duration_cell.data_type, "n")
		self.assertEqual(duration_cell.value, 1.25)
		self.assertEqual(duration_cell.number_format, "0.00")
