from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from time_tracking.utils import DEFAULT_WORKSPACE_ROUTE, ensure_default_workspace


class TestLoginWorkspaceRedirect(FrappeTestCase):
	def tearDown(self):
		if hasattr(frappe.local.flags, "home_page"):
			del frappe.local.flags.home_page
		super().tearDown()

	def test_sets_home_page_for_users_without_explicit_workspace(self):
		with (
			patch.object(frappe.session, "user", "test@example.com"),
			patch.object(
				frappe.db,
				"get_value",
				side_effect=["System User", None],
			),
			patch.object(frappe.db, "exists", return_value=True),
		):
			ensure_default_workspace()

		self.assertEqual(frappe.local.flags.home_page, DEFAULT_WORKSPACE_ROUTE)

	def test_sets_home_page_for_existing_time_tracking_default_workspace(self):
		with (
			patch.object(frappe.session, "user", "test@example.com"),
			patch.object(
				frappe.db,
				"get_value",
				side_effect=["System User", "Time Tracking"],
			),
			patch.object(frappe.db, "exists", return_value=True),
		):
			ensure_default_workspace()

		self.assertEqual(frappe.local.flags.home_page, DEFAULT_WORKSPACE_ROUTE)

	def test_keeps_other_explicit_default_workspace(self):
		with (
			patch.object(frappe.session, "user", "test@example.com"),
			patch.object(
				frappe.db,
				"get_value",
				side_effect=["System User", "Accounts"],
			),
			patch.object(frappe.db, "exists", return_value=True),
		):
			ensure_default_workspace()

		self.assertFalse(hasattr(frappe.local.flags, "home_page"))
