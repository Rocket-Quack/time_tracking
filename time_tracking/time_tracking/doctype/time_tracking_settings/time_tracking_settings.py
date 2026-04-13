import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, nowdate

from time_tracking.time_tracking.vacation_utils import (
	get_holiday_list_status_for_year,
	require_holiday_list_for_year,
)


class TimeTrackingSettings(Document):
	def validate(self):
		self._validate_current_year_holiday_list()

	def _validate_current_year_holiday_list(self):
		if not cint(self.enable_holiday_list):
			return
		require_holiday_list_for_year(getdate(nowdate()).year)


def _is_admin(user=None):
	if not user:
		user = frappe.session.user
	roles = frappe.get_roles(user)
	return "System Manager" in roles or "Time Tracking Admin" in roles


@frappe.whitelist()
def get_current_year_holiday_list_status():
	if not _is_admin():
		frappe.throw(_("Only administrators can access holiday list status."))

	current_year = getdate(nowdate()).year
	status = get_holiday_list_status_for_year(current_year)
	return {
		"year": status.get("year"),
		"expected_name": status.get("expected_name"),
		"exists": cint(status.get("exists")),
		"doctype": "Time Tracking Holiday List",
	}
