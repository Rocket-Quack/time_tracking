import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, nowdate

from time_tracking.time_tracking.db_aggregates import sum_as
from time_tracking.time_tracking.vacation_utils import (
    get_holiday_list_for_range,
    get_holidays_enabled,
    get_hours_per_vacation_day,
    get_sickness_project,
    get_vacation_carryover_days,
    get_vacation_balance,
    get_vacation_project,
    get_expected_holiday_list_name,
)
from time_tracking.time_tracking.overtime_utils import get_overtime_carryover_minutes


def _is_admin():
    roles = frappe.get_roles(frappe.session.user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def _get_columns():
    return [
        {
            "label": _("Month"),
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Workdays"),
            "fieldname": "workdays",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Holidays"),
            "fieldname": "holidays",
            "fieldtype": "Int",
            "width": 90,
        },
        {
            "label": _("Total Days"),
            "fieldname": "total_days",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": _("Planned Hours (incl. Holidays)"),
            "fieldname": "planned_hours",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Overtime Carryover"),
            "fieldname": "overtime_carryover",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": _("Bookings Total"),
            "fieldname": "booked_total",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Bookings Vacation"),
            "fieldname": "booked_vacation",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Bookings Sickness"),
            "fieldname": "booked_sickness",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Monthly Delta"),
            "fieldname": "monthly_delta",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": _("Overtime Balance"),
            "fieldname": "overtime_balance",
            "fieldtype": "Float",
            "width": 140,
        },
        {
            "label": _("Vacation Carryover"),
            "fieldname": "vacation_carryover",
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "label": _("Vacation Days Taken"),
            "fieldname": "vacation_days_taken",
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "label": _("Vacation Remaining"),
            "fieldname": "vacation_remaining",
            "fieldtype": "Float",
            "width": 150,
        },
    ]


def _get_profile(user):
    profile_name = frappe.db.get_value("Time Tracking Profile", {"user": user}, "name")
    if not profile_name:
        return None
    return frappe.get_doc("Time Tracking Profile", profile_name)


def _get_user(filters):
    if not _is_admin():
        return frappe.session.user
    user = (filters or {}).get("user")
    return user or frappe.session.user


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
    year = cint(filters.get("year") or getdate(nowdate()).year)
    user = _get_user(filters)
    if not user:
        frappe.throw(_("User is required."))

    profile = _get_profile(user)
    if not profile:
        frappe.throw(_("Time Tracking Profile is required."))

    settings = frappe.get_cached_doc("Time Tracking Settings")
    include_vacation = cint(settings.include_vacation_in_overtime)
    include_sickness = cint(settings.include_sickness_in_overtime)
    allow_negative = cint(settings.allow_negative_overtime_balance)

    overtime_carryover_minutes = get_overtime_carryover_minutes(
        profile, year, settings=settings
    )
    vacation_carryover_days = get_vacation_carryover_days(profile, year)
    running_minutes = int(round(overtime_carryover_minutes))

    vacation_project = get_vacation_project()
    sickness_project = get_sickness_project()
    holidays_enabled = get_holidays_enabled()

    rows = []
    for month in range(1, 13):
        start_date, end_date = _get_month_range(year, month)
        holiday_list = get_holiday_list_for_range(start_date, end_date)
        if holidays_enabled and not holiday_list:
            expected_name = get_expected_holiday_list_name(start_date.year)
            frappe.throw(
                _("Holiday List for {0} must be named {1}.").format(
                    start_date.year, expected_name
                )
            )

        holiday_dates = _get_holiday_dates(holiday_list, start_date, end_date)
        holiday_count = len(holiday_dates) if holidays_enabled else 0
        weekday_count = _count_weekdays(start_date, end_date)
        workday_count = max(weekday_count - holiday_count, 0)
        total_days = workday_count + holiday_count

        hours_per_day = flt(get_hours_per_vacation_day(profile))
        planned_hours = flt(total_days * hours_per_day, 2)
        holiday_minutes = holiday_count * hours_per_day * 60 if hours_per_day > 0 else 0

        totals_by_project, total_minutes = _get_booking_totals(
            profile.name, start_date, end_date
        )
        has_bookings = bool(totals_by_project)
        vacation_minutes = flt(totals_by_project.get(vacation_project, 0))
        sickness_minutes = flt(totals_by_project.get(sickness_project, 0))

        if has_bookings:
            actual_minutes = flt(total_minutes)
            if not include_vacation:
                actual_minutes -= vacation_minutes
            if not include_sickness:
                actual_minutes -= sickness_minutes
            actual_minutes += holiday_minutes

            delta_minutes = actual_minutes - (planned_hours * 60)
            running_minutes += delta_minutes
            if not allow_negative:
                running_minutes = max(running_minutes, 0)

            vacation_days_taken = 0
            if hours_per_day > 0:
                vacation_days_taken = flt(vacation_minutes / (hours_per_day * 60), 2)

            vacation_remaining = None
            if vacation_project:
                balance = get_vacation_balance(profile, end_date)
                if balance and balance.get("valid"):
                    vacation_remaining = flt(balance.get("remaining_days"), 2)
        else:
            delta_minutes = None
            vacation_days_taken = None
            vacation_remaining = None

        rows.append(
            {
                "month": calendar.month_name[month],
                "workdays": cint(workday_count),
                "holidays": cint(holiday_count),
                "total_days": cint(total_days),
                "planned_hours": planned_hours,
                "overtime_carryover": (
                    flt(overtime_carryover_minutes / 60, 2) if month == 1 else None
                ),
                "booked_total": flt(total_minutes / 60, 2) if has_bookings else None,
                "booked_vacation": flt(vacation_minutes / 60, 2) if has_bookings else None,
                "booked_sickness": flt(sickness_minutes / 60, 2) if has_bookings else None,
                "monthly_delta": (
                    flt(delta_minutes / 60, 2) if has_bookings else None
                ),
                "overtime_balance": (
                    flt(running_minutes / 60, 2) if has_bookings else None
                ),
                "vacation_carryover": (
                    flt(vacation_carryover_days, 2) if month == 1 else None
                ),
                "vacation_days_taken": vacation_days_taken,
                "vacation_remaining": vacation_remaining,
            }
        )

    return _get_columns(), rows
