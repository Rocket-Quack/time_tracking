import uuid

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, nowdate

from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
	expand_project_assignments,
)
from time_tracking.time_tracking.vacation_utils import (
	get_allow_negative_vacation_balance,
	get_hours_per_vacation_day,
	get_sickness_project,
	get_vacation_balance,
	get_vacation_project,
	validate_holiday_list_for_date,
)


class TimeBooking(Document):
	def autoname(self):
		if self.name:
			return
		# Use UUID without hyphens for stable external references (e.g. imports).
		self.name = uuid.uuid4().hex

	def before_insert(self):
		self._set_booking_code()

	def validate(self):
		self._set_default_profile()
		self._validate_profile_permission()
		self._validate_project()
		self._validate_notes()
		self._validate_duration_increment()
		self._validate_vacation_balance()
		self._validate_holiday_list()

	def _is_admin(self):
		roles = frappe.get_roles(frappe.session.user)
		return "System Manager" in roles or "Time Tracking Admin" in roles

	def _set_default_profile(self):
		if not self.time_tracking_profile:
			self.time_tracking_profile = frappe.session.user

	def _get_profile_name(self):
		return self.time_tracking_profile

	def _get_assigned_project_names(self):
		profile_name = self._get_profile_name()
		if not profile_name:
			return set()

		assigned = [
			row
			for row in frappe.get_all(
				"Time Tracking Profile Project",
				filters={
					"parenttype": "Time Tracking Profile",
					"parent": profile_name,
					"parentfield": "project_assignments",
					"active": 1,
				},
				pluck="project",
			)
			if row
		]
		if not assigned:
			return set()

		return set(expand_project_assignments(assigned, include_not_bookable=True))

	def _validate_profile_permission(self):
		if not self.time_tracking_profile:
			frappe.throw(_("Time Tracking Profile is required."))

		if not frappe.db.exists("Time Tracking Profile", self.time_tracking_profile):
			frappe.throw(_("Time Tracking Profile {0} does not exist.").format(self.time_tracking_profile))

		if frappe.session.user != "Administrator" and not self._is_admin():
			if self.time_tracking_profile != frappe.session.user:
				frappe.throw(_("You can only book time for yourself."))

	def _validate_project(self):
		if not self.project:
			frappe.throw(_("Project is required for bookings."))

		is_group = frappe.db.get_value("Time Tracking Project", self.project, "is_group")
		if is_group:
			frappe.throw(_("Project {0} is a group and cannot be booked.").format(self.project))

		is_not_bookable = frappe.db.get_value("Time Tracking Project", self.project, "not_bookable")
		if is_not_bookable:
			frappe.throw(_("Project {0} is not bookable.").format(self.project))

		if not self._is_admin():
			vacation_project = get_vacation_project()
			sickness_project = get_sickness_project()
			assigned_projects = self._get_assigned_project_names()
			if self.project not in assigned_projects and self.project not in (
				vacation_project,
				sickness_project,
			):
				frappe.throw(_("Project {0} is not assigned to your profile.").format(self.project))

	def _validate_notes(self):
		if not (self.notes or "").strip():
			frappe.throw(_("Note is required for bookings."))

	def _validate_duration_increment(self):
		if not self.duration_minutes:
			return

		if self.duration_minutes <= 0:
			frappe.throw(_("Duration must be greater than 0 minutes."))

		increment = (
			frappe.db.get_single_value("Time Tracking Settings", "time_booking_increment_minutes") or 15
		)
		increment = int(increment)

		if self.duration_minutes % increment:
			frappe.throw(_("Duration must be a multiple of {0} minutes.").format(increment))

	def _validate_vacation_balance(self):
		vacation_project = get_vacation_project()
		if not vacation_project or self.project != vacation_project:
			return

		if not self.date:
			return

		profile = frappe.get_doc("Time Tracking Profile", self.time_tracking_profile)
		hours_per_day = get_hours_per_vacation_day(profile)
		if hours_per_day <= 0:
			frappe.throw(_("Vacation balance requires target hours and workdays per week."))

		balance = get_vacation_balance(
			profile,
			self.date,
			exclude_booking_name=None if self.is_new() else self.name,
		)
		if not balance or not balance.get("valid"):
			frappe.throw(_("Vacation balance requires target hours and workdays per week."))

		allowance_minutes = flt(balance.get("allowance_minutes"))
		used_minutes = flt(balance.get("used_minutes"))
		total_minutes = used_minutes + flt(self.duration_minutes)
		remaining_minutes = allowance_minutes - total_minutes

		if remaining_minutes < 0 and not get_allow_negative_vacation_balance():
			remaining_days = abs(remaining_minutes) / (hours_per_day * 60)
			frappe.throw(
				_("Vacation balance would become negative by {0} days.").format(flt(remaining_days, 2))
			)

	def _validate_holiday_list(self):
		if not self.date or not self.time_tracking_profile:
			return
		validate_holiday_list_for_date(self.date)

	def _set_booking_code(self):
		if self.booking_code:
			return
		date_key = nowdate().replace("-", "")
		self.booking_code = make_autoname(f"TTB-{date_key}-.####")
