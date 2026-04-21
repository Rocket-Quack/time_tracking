import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
	expand_project_assignments,
)


class WeeklyBookingData(Document):
	def validate(self):
		self._require_profile()
		self._validate_rows()

	def _is_admin(self):
		roles = frappe.get_roles(frappe.session.user)
		return "System Manager" in roles or "Time Tracking Admin" in roles

	def _require_profile(self):
		if not frappe.db.exists("Time Tracking Profile", {"user": self.user}):
			frappe.throw(_("Time Tracking Profile is required."))

	def _get_assigned_project_names(self):
		if self._is_admin():
			return None

		profile_name = frappe.db.get_value("Time Tracking Profile", {"user": self.user}, "name")
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

	def _validate_rows(self):
		assigned_projects = self._get_assigned_project_names()
		day_fields = [
			"monday_hours",
			"tuesday_hours",
			"wednesday_hours",
			"thursday_hours",
			"friday_hours",
			"saturday_hours",
			"sunday_hours",
		]

		for row in self.bookings or []:
			row_project = row.project
			row_note = (row.note or "").strip()
			hours = [flt(row.get(field)) for field in day_fields]
			has_hours = any(hours)
			if not row_project and not row_note and not has_hours:
				continue

			if not row_project:
				frappe.throw(_("Project is required for bookings."))

			if not row_note:
				if has_hours:
					frappe.throw(_("Note is required for bookings."))
				frappe.throw(_("Note and time are required for bookings."))

			if not has_hours:
				frappe.throw(_("Time is required for bookings."))

			if row_project:
				if assigned_projects is not None and row_project not in assigned_projects:
					frappe.throw(_("Project {0} is not assigned to your profile.").format(row_project))

				if not frappe.db.exists("Time Tracking Project", row_project):
					frappe.throw(_("Project {0} does not exist.").format(row_project))

				is_group = frappe.db.get_value("Time Tracking Project", row_project, "is_group")
				if is_group:
					frappe.throw(_("Project {0} is a group and cannot be booked.").format(row_project))


def _is_admin(user=None):
	if not user:
		user = frappe.session.user
	roles = frappe.get_roles(user)
	return "System Manager" in roles or "Time Tracking Admin" in roles


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user
	if _is_admin(user):
		return ""
	return f"`tabWeekly Booking Data`.`user` = {frappe.db.escape(user)}"


def has_permission(doc, user):
	if not user:
		user = frappe.session.user
	if _is_admin(user):
		return True
	if not doc:
		return False
	return doc.user == user
