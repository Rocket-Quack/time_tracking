import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from time_tracking.time_tracking.vacation_utils import get_expected_holiday_list_name


class TestTimeTrackingSettings(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.current_year = getdate(nowdate()).year
		self.expected_name = get_expected_holiday_list_name(self.current_year)
		self.original_enable_holiday_list = frappe.db.get_single_value(
			"Time Tracking Settings",
			"enable_holiday_list",
		)
		if frappe.db.exists("Time Tracking Holiday List", self.expected_name):
			frappe.delete_doc(
				"Time Tracking Holiday List",
				self.expected_name,
				force=1,
				ignore_permissions=True,
			)
		frappe.db.set_single_value("Time Tracking Settings", "enable_holiday_list", 0)

	def tearDown(self):
		if frappe.db.exists("Time Tracking Holiday List", self.expected_name):
			frappe.delete_doc(
				"Time Tracking Holiday List",
				self.expected_name,
				force=1,
				ignore_permissions=True,
			)
		frappe.db.set_single_value(
			"Time Tracking Settings",
			"enable_holiday_list",
			self.original_enable_holiday_list or 0,
		)

	def _create_current_year_holiday_list(self):
		return frappe.get_doc(
			{
				"doctype": "Time Tracking Holiday List",
				"year": str(self.current_year),
				"holidays": [],
			}
		).insert(ignore_permissions=True)

	def test_enable_holidays_requires_current_year_holiday_list(self):
		settings = frappe.get_single("Time Tracking Settings")
		settings.enable_holiday_list = 1

		with self.assertRaises(frappe.ValidationError):
			settings.save()

	def test_enable_holidays_allowed_when_current_year_holiday_list_exists(self):
		self._create_current_year_holiday_list()
		settings = frappe.get_single("Time Tracking Settings")
		settings.enable_holiday_list = 1
		settings.save()

		self.assertEqual(settings.enable_holiday_list, 1)

	def test_disable_holidays_does_not_require_holiday_list(self):
		settings = frappe.get_single("Time Tracking Settings")
		settings.enable_holiday_list = 0
		settings.save()

		self.assertEqual(settings.enable_holiday_list, 0)
