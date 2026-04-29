import frappe
from frappe.tests.utils import FrappeTestCase


class TestTimeTrackingProfileAssignments(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("Time Tracking Settings", "require_project_assignment", 0)

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

	def _make_project(self, name, assignment_mode="Open", allowed_users=None):
		doc = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": name,
				"assignment_mode": assignment_mode,
				"allowed_users": [{"user": user} for user in (allowed_users or [])],
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _make_profile(self, user, projects):
		profile = frappe.get_doc(
			{
				"doctype": "Time Tracking Profile",
				"user": user,
				"target_period": "Weekly",
				"weekly_target_hours": 40,
				"workdays_per_week": 5,
				"project_assignments": [{"project": project, "active": 1} for project in projects],
			}
		)
		profile.insert(ignore_permissions=True)
		return profile.name

	def test_restricted_project_allows_listed_user(self):
		user = self._make_user("allowed")
		project = self._make_project(
			f"Restricted-{frappe.generate_hash(length=6)}",
			assignment_mode="Restricted",
			allowed_users=[user],
		)

		frappe.set_user(user)
		self._make_profile(user, [project])

	def test_restricted_project_blocks_unlisted_user(self):
		allowed = self._make_user("allowed")
		project = self._make_project(
			f"Restricted-{frappe.generate_hash(length=6)}",
			assignment_mode="Restricted",
			allowed_users=[allowed],
		)

		user = self._make_user("blocked")
		frappe.set_user(user)
		with self.assertRaises(frappe.ValidationError):
			self._make_profile(user, [project])

	def test_admin_can_assign_restricted_project(self):
		allowed = self._make_user("allowed")
		project = self._make_project(
			f"Restricted-{frappe.generate_hash(length=6)}",
			assignment_mode="Restricted",
			allowed_users=[allowed],
		)

		user = self._make_user("adminassign")
		frappe.set_user("Administrator")
		self._make_profile(user, [project])

	def test_profile_insert_creates_opening_ledgers(self):
		user = self._make_user("openingledger")
		frappe.set_user("Administrator")
		profile_name = self._make_profile(user, [])

		overtime_entry = frappe.db.exists(
			"Time Tracking Overtime Ledger",
			{
				"time_tracking_profile": profile_name,
				"entry_type": "Opening Balance",
			},
		)
		self.assertTrue(overtime_entry)

		vacation_entry = frappe.db.exists(
			"Time Tracking Vacation Ledger",
			{
				"time_tracking_profile": profile_name,
				"entry_type": "Opening Balance",
			},
		)
		self.assertTrue(vacation_entry)

	def test_employee_can_load_profile_ui_settings_without_settings_read_access(self):
		user = self._make_user("ui-settings")

		frappe.set_user(user)
		settings = frappe.call(
			"time_tracking.time_tracking.doctype.time_tracking_profile.time_tracking_profile.get_profile_ui_settings"
		)

		self.assertIn("track_target_adjustments", settings)
		self.assertIn("require_project_assignment", settings)

	def test_duplicate_project_assignment_error_uses_project_label(self):
		user = self._make_user("duplicate-project")
		parent_label = f"Parent-{frappe.generate_hash(length=6)}"
		parent = self._make_project(parent_label)
		project = frappe.get_doc(
			{
				"doctype": "Time Tracking Project",
				"project_name": f"Child-{frappe.generate_hash(length=6)}",
				"parent_time_tracking_project": parent,
			}
		).insert(ignore_permissions=True)

		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError) as exc:
			self._make_profile(user, [project.name, project.name])

		self.assertIn(parent_label, str(exc.exception))
		self.assertIn(project.project_name, str(exc.exception))
		self.assertNotIn(project.name, str(exc.exception))
