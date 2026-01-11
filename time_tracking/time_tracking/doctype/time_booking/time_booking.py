import frappe
from frappe import _
from frappe.model.document import Document

class TimeBooking(Document):
    def validate(self):
        self._set_default_profile()
        self._validate_profile_permission()
        self._validate_project()
        self._validate_notes()
        self._validate_duration_increment()

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

        return set(
            frappe.get_all(
                "Time Tracking Profile Project",
                filters={
                    "parenttype": "Time Tracking Profile",
                    "parent": profile_name,
                    "parentfield": "project_assignments",
                    "active": 1,
                },
                pluck="project",
            )
        )

    def _validate_profile_permission(self):
        if not self.time_tracking_profile:
            frappe.throw(_("Time Tracking Profile is required."))

        if not frappe.db.exists("Time Tracking Profile", self.time_tracking_profile):
            frappe.throw(
                _("Time Tracking Profile {0} does not exist.").format(self.time_tracking_profile)
            )

        if frappe.session.user != "Administrator" and not self._is_admin():
            if self.time_tracking_profile != frappe.session.user:
                frappe.throw(_("You can only book time for yourself."))

    def _validate_project(self):
        if not self.project:
            frappe.throw(_("Project is required for bookings."))

        is_group = frappe.db.get_value("Time Tracking Project", self.project, "is_group")
        if is_group:
            frappe.throw(_("Project {0} is a group and cannot be booked.").format(self.project))

        if not self._is_admin():
            assigned_projects = self._get_assigned_project_names()
            if self.project not in assigned_projects:
                frappe.throw(
                    _("Project {0} is not assigned to your profile.").format(self.project)
                )

    def _validate_notes(self):
        if not (self.notes or "").strip():
            frappe.throw(_("Note is required for bookings."))

    def _validate_duration_increment(self):
        if not self.duration_minutes:
            return

        if self.duration_minutes <= 0:
            frappe.throw(_("Duration must be greater than 0 minutes."))

        increment = frappe.db.get_single_value(
            "Time Tracking Settings", "time_booking_increment_minutes"
        ) or 15
        increment = int(increment)

        if self.duration_minutes % increment:
            frappe.throw(
                _("Duration must be a multiple of {0} minutes.").format(increment)
            )
