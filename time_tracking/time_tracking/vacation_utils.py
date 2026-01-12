import calendar

import frappe
from frappe.utils import cint, flt, getdate

WEEKS_PER_MONTH = 52 / 12


def get_vacation_project():
    return frappe.db.get_single_value("Time Tracking Settings", "vacation_booking_project")


def get_allow_negative_vacation_balance():
    return cint(
        frappe.db.get_single_value(
            "Time Tracking Settings", "allow_negative_vacation_balance"
        )
        or 0
    )


def get_default_workdays_per_week():
    return flt(
        frappe.db.get_single_value("Time Tracking Settings", "default_workdays_per_week")
        or 0
    )


def get_hours_per_vacation_day(profile):
    workdays = flt(profile.workdays_per_week) or get_default_workdays_per_week()
    if not workdays:
        return 0

    if profile.target_period == "Weekly":
        weekly_hours = flt(profile.weekly_target_hours)
    elif profile.target_period == "Monthly":
        weekly_hours = flt(profile.monthly_target_hours) / WEEKS_PER_MONTH
    else:
        weekly_hours = 0

    if weekly_hours <= 0:
        return 0

    return weekly_hours / workdays


def _get_year_range(date):
    booking_date = getdate(date)
    year = booking_date.year
    start = booking_date.replace(month=1, day=1)
    last_day = calendar.monthrange(year, 12)[1]
    end = booking_date.replace(month=12, day=last_day)
    return start, end


def get_vacation_used_minutes(profile_name, date, exclude_booking_name=None):
    vacation_project = get_vacation_project()
    if not vacation_project or not profile_name or not date:
        return 0

    start, end = _get_year_range(date)
    filters = {
        "time_tracking_profile": profile_name,
        "project": vacation_project,
        "date": ["between", [start, end]],
    }
    if exclude_booking_name:
        filters["name"] = ["!=", exclude_booking_name]

    totals = frappe.get_all(
        "Time Booking", filters=filters, fields=["sum(duration_minutes) as total"]
    )
    if totals and totals[0].total is not None:
        return flt(totals[0].total)
    return 0


def get_vacation_balance(profile, date, exclude_booking_name=None):
    vacation_project = get_vacation_project()
    if not vacation_project or not profile or not date:
        return None

    hours_per_day = get_hours_per_vacation_day(profile)
    if hours_per_day <= 0:
        return {
            "enabled": True,
            "valid": False,
        }

    allowance_minutes = flt(profile.vacation_days_per_year) * hours_per_day * 60
    used_minutes = get_vacation_used_minutes(
        profile.name, date, exclude_booking_name=exclude_booking_name
    )
    remaining_minutes = allowance_minutes - used_minutes

    allowance_days = allowance_minutes / (hours_per_day * 60)
    used_days = used_minutes / (hours_per_day * 60)
    remaining_days = remaining_minutes / (hours_per_day * 60)

    return {
        "enabled": True,
        "valid": True,
        "hours_per_day": hours_per_day,
        "allowance_minutes": allowance_minutes,
        "used_minutes": used_minutes,
        "remaining_minutes": remaining_minutes,
        "allowance_days": allowance_days,
        "used_days": used_days,
        "remaining_days": remaining_days,
    }
