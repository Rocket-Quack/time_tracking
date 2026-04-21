import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestTimeBooking(FrappeTestCase):
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

	def _make_project(self, name, not_bookable=0):
		doc = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": name,
				"not_bookable": not_bookable,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_profile(self, user, project):
		profile = frappe.get_doc(
			{
				"doctype": "Time Tracking Profile",
				"user": user,
				"target_period": "Weekly",
				"weekly_target_hours": 40,
				"workdays_per_week": 5,
				"project_assignments": [{"project": project, "active": 1}],
			}
		)
		profile.insert(ignore_permissions=True)
		return profile.name

	def test_not_bookable_project_blocks_booking(self):
		user = self._make_user("booker")
		project = self._make_project(
			f"NotBookable-{frappe.generate_hash(length=6)}",
			not_bookable=1,
		)
		self._make_profile(user, project)

		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": project,
				"duration_minutes": 60,
				"notes": "Test booking",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			booking.insert(ignore_permissions=True)

	def test_group_assignment_allows_child_booking(self):
		user = self._make_user("group")
		group = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": f"Group-{frappe.generate_hash(length=6)}",
				"is_group": 1,
			}
		).insert(ignore_permissions=True)
		child = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": f"Child-{frappe.generate_hash(length=6)}",
				"parent_time_tracking_project": group.name,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._make_profile(user, group.name)

		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": child.name,
				"duration_minutes": 60,
				"notes": "Test booking",
			}
		)
		booking.insert(ignore_permissions=True)

	def test_group_project_blocks_booking_by_default(self):
		user = self._make_user("group-blocked")
		group = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": f"BlockedGroup-{frappe.generate_hash(length=6)}",
				"is_group": 1,
			}
		).insert(ignore_permissions=True)
		self._make_profile(user, group.name)

		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": group.name,
				"duration_minutes": 60,
				"notes": "Group booking",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			booking.insert(ignore_permissions=True)

	def test_group_project_booking_allowed_when_setting_enabled(self):
		user = self._make_user("group-allowed")
		group = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": f"AllowedGroup-{frappe.generate_hash(length=6)}",
				"is_group": 1,
			}
		).insert(ignore_permissions=True)
		self._make_profile(user, group.name)
		frappe.db.set_single_value("Time Tracking Settings", "allow_group_project_booking", 1)

		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": group.name,
				"duration_minutes": 60,
				"notes": "Group booking",
			}
		)
		booking.insert(ignore_permissions=True)

	def test_bill_type_defaults_to_billable(self):
		user = self._make_user("bill-type")
		project = self._make_project(f"BillableDefault-{frappe.generate_hash(length=6)}")
		self._make_profile(user, project)

		frappe.set_user(user)
		booking = frappe.get_doc(
			{
				"doctype": "Time Booking",
				"time_tracking_profile": user,
				"date": today(),
				"project": project,
				"duration_minutes": 60,
				"notes": "Default bill type booking",
			}
		)
		booking.insert(ignore_permissions=True)

		self.assertEqual(booking.bill_type, "Billable")
