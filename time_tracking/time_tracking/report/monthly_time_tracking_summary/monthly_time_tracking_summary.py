import calendar
import unicodedata

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, nowdate

from time_tracking.time_tracking.db_aggregates import sum_as
from time_tracking.time_tracking.vacation_utils import (
    get_hours_per_vacation_day,
    get_vacation_balance,
    get_vacation_project,
    get_sickness_project,
    get_expected_holiday_list_name,
    get_holiday_list_for_range,
    get_holidays_enabled,
)

GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "maerz": 3,
    "marz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

ENGLISH_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def _is_admin():
    roles = frappe.get_roles(frappe.session.user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def _get_columns():
    return [
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 180,
        },
        {
            "label": _("Workdays"),
            "fieldname": "workdays",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": _("Holidays"),
            "fieldname": "holidays",
            "fieldtype": "Float",
            "width": 90,
        },
        {
            "label": _("Total Days"),
            "fieldname": "total_days",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": _("Hours per Day"),
            "fieldname": "hours_per_day",
            "fieldtype": "Float",
            "width": 110,
        },
        {
            "label": _("Holiday Hours"),
            "fieldname": "holiday_hours",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Planned Hours"),
            "fieldname": "planned_hours",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Worked Hours"),
            "fieldname": "worked_hours",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Vacation Hours"),
            "fieldname": "vacation_hours",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Sickness Hours"),
            "fieldname": "sickness_hours",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Total Hours"),
            "fieldname": "total_hours",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Monthly Delta"),
            "fieldname": "monthly_delta",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Hours Balance"),
            "fieldname": "hours_balance",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Vacation Remaining"),
            "fieldname": "vacation_remaining",
            "fieldtype": "Float",
            "width": 150,
        },
    ]


def _get_month_index(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    if raw.isdigit():
        return cint(raw)
    lowered = raw.lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    normalized = "".join(ch for ch in normalized if ord(ch) < 128)
    if normalized in GERMAN_MONTHS:
        return GERMAN_MONTHS[normalized]
    return ENGLISH_MONTHS.get(normalized)


def _get_month_range(year, month):
    last_day = calendar.monthrange(year, month)[1]
    start = getdate(f"{year}-{month:02d}-01")
    end = getdate(f"{year}-{month:02d}-{last_day}")
    return start, end


def _count_weekdays(start_date, end_date):
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current = add_days(current, 1)
    return count


def _get_holiday_dates(holiday_list, start_date, end_date):
    if not holiday_list:
        return set()

    holidays = frappe.get_all(
        "Time Tracking Holiday",
        filters={
            "parent": holiday_list,
            "parenttype": "Time Tracking Holiday List",
            "parentfield": "holidays",
            "holiday_date": ["between", [start_date, end_date]],
        },
        fields=["holiday_date"],
    )
    dates = set()
    for row in holidays:
        holiday_date = getdate(row.holiday_date)
        if holiday_date.weekday() >= 5:
            continue
        dates.add(holiday_date)
    return dates


def _get_profiles(filters):
    if not _is_admin():
        return frappe.get_all(
            "Time Tracking Profile",
            filters={"user": frappe.session.user},
            fields=[
                "name",
                "user",
                "overtime_balance_hours",
                "target_period",
                "weekly_target_hours",
                "monthly_target_hours",
                "workdays_per_week",
                "vacation_days_per_year",
            ],
        )

    user_filter = (filters or {}).get("user")
    if user_filter:
        return frappe.get_all(
            "Time Tracking Profile",
            filters={"user": user_filter},
            fields=[
                "name",
                "user",
                "overtime_balance_hours",
                "target_period",
                "weekly_target_hours",
                "monthly_target_hours",
                "workdays_per_week",
                "vacation_days_per_year",
            ],
        )

    return frappe.get_all(
        "Time Tracking Profile",
        filters={"user": ["!=", ""]},
        fields=[
            "name",
            "user",
            "overtime_balance_hours",
            "target_period",
            "weekly_target_hours",
            "monthly_target_hours",
            "workdays_per_week",
            "vacation_days_per_year",
        ],
    )


def _get_booking_totals(profile_name, start_date, end_date):
    totals = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        fields=["project", sum_as("duration_minutes", "total_minutes")],
        group_by="project",
    )
    totals_by_project = {}
    total_minutes = 0
    for row in totals:
        minutes = flt(row.total_minutes)
        totals_by_project[row.project] = minutes
        total_minutes += minutes
    return totals_by_project, total_minutes


def execute(filters=None):
    filters = filters or {}

    month_index = _get_month_index(filters.get("month"))
    if not month_index:
        month_index = cint(getdate(nowdate()).month)
    year = cint(filters.get("year") or getdate(nowdate()).year)

    start_date, end_date = _get_month_range(year, month_index)

    weekday_count = _count_weekdays(start_date, end_date)
    holiday_cache = {}
    holidays_enabled = get_holidays_enabled()

    vacation_project = get_vacation_project()
    sickness_project = get_sickness_project()

    rows = []
    for profile in _get_profiles(filters):
        holiday_list = get_holiday_list_for_range(start_date, end_date)
        if holidays_enabled and not holiday_list:
            expected_name = get_expected_holiday_list_name(start_date.year)
            frappe.throw(
                _("Holiday List for {0} must be named {1}.").format(
                    start_date.year, expected_name
                )
            )
        if not holidays_enabled:
            holiday_count = 0
        elif holiday_list not in holiday_cache:
            holiday_cache[holiday_list] = _get_holiday_dates(
                holiday_list, start_date, end_date
            )
        if holidays_enabled:
            holiday_dates = holiday_cache.get(holiday_list, set())
            holiday_count = len(holiday_dates)
        workday_count = max(weekday_count - holiday_count, 0)
        total_days = workday_count + holiday_count

        hours_per_day = flt(get_hours_per_vacation_day(profile))
        planned_hours = flt(total_days * hours_per_day, 2)
        holiday_hours = flt(holiday_count * hours_per_day, 2)

        totals_by_project, total_minutes = _get_booking_totals(
            profile.name, start_date, end_date
        )
        vacation_minutes = flt(totals_by_project.get(vacation_project, 0))
        sickness_minutes = flt(totals_by_project.get(sickness_project, 0))
        worked_minutes = total_minutes - vacation_minutes - sickness_minutes

        worked_hours = flt(worked_minutes / 60, 2)
        vacation_hours = flt(vacation_minutes / 60, 2)
        sickness_hours = flt(sickness_minutes / 60, 2)
        total_hours = flt(total_minutes / 60, 2)
        monthly_delta = flt(total_hours - planned_hours, 2)

        vacation_remaining = None
        if vacation_project:
            balance = get_vacation_balance(profile, end_date)
            if balance and balance.get("valid"):
                vacation_remaining = flt(balance.get("remaining_days"), 2)

        rows.append(
            {
                "user": profile.user,
                "workdays": workday_count,
                "holidays": holiday_count,
                "total_days": total_days,
                "hours_per_day": flt(hours_per_day, 2),
                "holiday_hours": holiday_hours,
                "planned_hours": planned_hours,
                "worked_hours": worked_hours,
                "vacation_hours": vacation_hours,
                "sickness_hours": sickness_hours,
                "total_hours": total_hours,
                "monthly_delta": monthly_delta,
                "hours_balance": flt(profile.overtime_balance_hours, 2),
                "vacation_remaining": vacation_remaining,
            }
        )

    return _get_columns(), rows
