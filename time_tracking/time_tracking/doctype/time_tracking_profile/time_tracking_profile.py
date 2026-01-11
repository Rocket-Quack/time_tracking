import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

TARGET_PERIOD_WEEKLY = "Weekly"
TARGET_PERIOD_MONTHLY = "Monthly"
TARGET_PERIODS = {TARGET_PERIOD_WEEKLY, TARGET_PERIOD_MONTHLY}

class TimeTrackingProfile(Document):
    def validate(self):
        self._validate_overtime_balance()
        self._validate_target_period()
        self._validate_target_values()
        self._validate_hourly_rate()
        self._validate_vacation_days()

    def _validate_overtime_balance(self):
        if _is_admin():
            return

        previous = self.get_doc_before_save()
        if previous and flt(previous.overtime_balance_hours) != flt(self.overtime_balance_hours):
            frappe.throw(_("Overtime balance can only be updated by an admin."))

    def _validate_target_period(self):
        target_period = (self.target_period or "").strip()
        if not target_period:
            weekly_value = flt(self.weekly_target_hours)
            monthly_value = flt(self.monthly_target_hours)
            if weekly_value and not monthly_value:
                target_period = TARGET_PERIOD_WEEKLY
            elif monthly_value and not weekly_value:
                target_period = TARGET_PERIOD_MONTHLY
            elif weekly_value and monthly_value:
                target_period = TARGET_PERIOD_WEEKLY
            else:
                frappe.throw(_("Target period is required."))
            self.target_period = target_period
        if target_period not in TARGET_PERIODS:
            frappe.throw(_("Target period must be Weekly or Monthly."))

        previous = self.get_doc_before_save()
        if previous and previous.target_period != target_period:
            if not self.flags.get("allow_target_period_change"):
                frappe.throw(_("Target period cannot be changed after creation."))

    def _validate_target_values(self):
        target_period = (self.target_period or "").strip()
        previous = self.get_doc_before_save()

        if not previous:
            if target_period == TARGET_PERIOD_WEEKLY:
                if flt(self.weekly_target_hours) <= 0:
                    frappe.throw(_("Weekly target hours are required."))
                self.monthly_target_hours = 0
            elif target_period == TARGET_PERIOD_MONTHLY:
                if flt(self.monthly_target_hours) <= 0:
                    frappe.throw(_("Monthly target hours are required."))
                self.weekly_target_hours = 0
            return

        changed_weekly = flt(previous.weekly_target_hours) != flt(self.weekly_target_hours)
        changed_monthly = flt(previous.monthly_target_hours) != flt(self.monthly_target_hours)

        if not (changed_weekly or changed_monthly):
            return

        if self.flags.get("allow_target_adjustment"):
            return

        if not _is_admin():
            frappe.throw(_("Targets can only be updated by an admin."))

        frappe.throw(_("Targets can only be updated using the target adjustment buttons."))

    def _validate_vacation_days(self):
        if _is_admin():
            return

        previous = self.get_doc_before_save()
        if previous and flt(previous.vacation_days_per_year) != flt(self.vacation_days_per_year):
            frappe.throw(_("Vacation days can only be updated by an admin."))

    def _validate_hourly_rate(self):
        previous = self.get_doc_before_save()
        current = flt(self.hourly_rate)

        if current < 0:
            frappe.throw(_("Hourly rate cannot be negative."))

        allow_override = cint(
            frappe.db.get_single_value(
                "Time Tracking Settings", "allow_profile_rate_override"
            )
            or 0
        )
        if not allow_override:
            if current and (not previous or flt(previous.hourly_rate) != current):
                frappe.throw(_("Profile rate overrides are disabled in settings."))
            if not previous:
                self.hourly_rate = 0
            return

        if not _is_admin():
            if previous and flt(previous.hourly_rate) != current:
                frappe.throw(_("Hourly rate can only be updated by an admin."))


def _is_admin(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def _is_manager(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "Time Tracking Manager" in roles


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    if _is_admin(user) or _is_manager(user):
        return ""
    return f"`tabTime Tracking Profile`.`user` = {frappe.db.escape(user)}"


def has_permission(doc, user):
    if not user:
        user = frappe.session.user
    if _is_admin(user):
        return True
    if not doc:
        return False
    return doc.user == user


@frappe.whitelist()
def adjust_target(profile_name, target_period, delta_hours):
    if not _is_admin():
        frappe.throw(_("Only administrators can adjust targets."))

    if not profile_name:
        frappe.throw(_("Time Tracking Profile is required."))

    target_period = (target_period or "").strip()
    if target_period not in TARGET_PERIODS:
        frappe.throw(_("Target period must be Weekly or Monthly."))

    delta = flt(delta_hours)
    if delta == 0:
        frappe.throw(_("Adjustment value must be non-zero."))

    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    if profile.target_period != target_period:
        frappe.throw(_("Target period does not match the profile configuration."))

    fieldname = "weekly_target_hours" if target_period == TARGET_PERIOD_WEEKLY else "monthly_target_hours"
    old_value = flt(profile.get(fieldname))
    new_value = old_value + delta
    if new_value < 0:
        frappe.throw(_("Target hours cannot be negative."))

    profile.set(fieldname, new_value)
    profile.flags.allow_target_adjustment = True
    profile.append(
        "target_adjustments",
        {
            "adjusted_on": now_datetime(),
            "adjusted_by": frappe.session.user,
            "previous_period": target_period,
            "target_period": target_period,
            "old_value": old_value,
            "new_value": new_value,
            "delta_hours": delta,
        },
    )
    profile.save(ignore_permissions=True)

    return {
        "target_period": target_period,
        "old_value": old_value,
        "new_value": new_value,
    }


@frappe.whitelist()
def switch_target_period(profile_name, new_period, new_value):
    if not _is_admin():
        frappe.throw(_("Only administrators can switch target periods."))

    if not profile_name:
        frappe.throw(_("Time Tracking Profile is required."))

    new_period = (new_period or "").strip()
    if new_period not in TARGET_PERIODS:
        frappe.throw(_("Target period must be Weekly or Monthly."))

    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    if profile.target_period == new_period:
        frappe.throw(_("Target period is already set to {0}.").format(new_period))

    old_period = profile.target_period
    if old_period not in TARGET_PERIODS:
        frappe.throw(_("Current target period is invalid."))

    new_value = flt(new_value)
    if new_value <= 0:
        frappe.throw(_("Target hours must be greater than 0."))

    old_value = (
        flt(profile.weekly_target_hours)
        if old_period == TARGET_PERIOD_WEEKLY
        else flt(profile.monthly_target_hours)
    )

    profile.target_period = new_period
    if new_period == TARGET_PERIOD_WEEKLY:
        profile.weekly_target_hours = new_value
        profile.monthly_target_hours = 0
    else:
        profile.monthly_target_hours = new_value
        profile.weekly_target_hours = 0

    profile.flags.allow_target_adjustment = True
    profile.flags.allow_target_period_change = True
    profile.append(
        "target_adjustments",
        {
            "adjusted_on": now_datetime(),
            "adjusted_by": frappe.session.user,
            "previous_period": old_period,
            "target_period": new_period,
            "old_value": old_value,
            "new_value": new_value,
            "delta_hours": new_value - old_value,
        },
    )
    profile.save(ignore_permissions=True)

    return {
        "target_period": new_period,
        "old_period": old_period,
        "old_value": old_value,
        "new_value": new_value,
    }
