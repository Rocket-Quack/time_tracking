import calendar

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

from time_tracking.time_tracking.overtime_utils import (
    get_holiday_dates_for_range,
    get_weekly_forecast,
)
from time_tracking.time_tracking.vacation_utils import (
    get_hours_per_vacation_day,
    get_vacation_balance,
    get_vacation_project,
)


def _get_profile(user):
    profile_name = frappe.db.get_value("Time Tracking Profile", {"user": user}, "name")
    if not profile_name:
        return None
    return frappe.get_doc("Time Tracking Profile", profile_name)


def _get_week_range(date):
    start = getdate(date)
    start = add_days(start, -start.weekday())
    end = add_days(start, 6)
    return start, end


def _get_month_range(date):
    month_start = getdate(date).replace(day=1)
    last_day = calendar.monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=last_day)
    return month_start, month_end


def _get_time_booking_minutes(profile_name, start_date, end_date):
    if not profile_name:
        return 0
    totals = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        fields=["sum(duration_minutes) as total"],
    )
    if totals and totals[0].total is not None:
        return int(round(flt(totals[0].total)))
    return 0


def _add_holiday_minutes(profile, start_date, end_date, total_minutes):
    hours_per_day = flt(get_hours_per_vacation_day(profile))
    if hours_per_day <= 0:
        return total_minutes
    holiday_dates = get_holiday_dates_for_range(start_date, end_date)
    if not holiday_dates:
        return total_minutes
    return total_minutes + int(round(len(holiday_dates) * hours_per_day * 60))


def _get_vacation_summary(profile, date):
    vacation_project = get_vacation_project()
    if not vacation_project:
        return {"enabled": False}

    balance = get_vacation_balance(profile, date)
    if not balance:
        return {"enabled": False}

    if not balance.get("valid"):
        return {
            "enabled": True,
            "valid": False,
            "error": _("Set target hours and workdays per week to calculate vacation."),
        }

    return {
        "enabled": True,
        "valid": True,
        "remaining_days": balance.get("remaining_days"),
        "used_days": balance.get("used_days"),
        "allowance_days": balance.get("allowance_days"),
    }


@frappe.whitelist()
def get_workspace_summary():
    user = frappe.session.user
    profile = _get_profile(user)
    if not profile:
        return {
            "profile_missing": True,
            "message": _("Time Tracking Profile is required."),
        }

    today = nowdate()
    week_start, week_end = _get_week_range(today)
    month_start, month_end = _get_month_range(today)

    weekly_total_minutes = _get_time_booking_minutes(profile.name, week_start, week_end)
    monthly_total_minutes = _get_time_booking_minutes(profile.name, month_start, month_end)
    weekly_total_minutes = _add_holiday_minutes(
        profile, week_start, week_end, weekly_total_minutes
    )
    monthly_total_minutes = _add_holiday_minutes(
        profile, month_start, month_end, monthly_total_minutes
    )
    hours_balance_minutes = int(round(flt(profile.overtime_balance_hours) * 60))
    weekly_forecast = get_weekly_forecast(profile, week_start)

    return {
        "profile_missing": False,
        "weekly_total_minutes": weekly_total_minutes,
        "monthly_total_minutes": monthly_total_minutes,
        "hours_balance_minutes": hours_balance_minutes,
        "weekly_forecast_minutes": weekly_forecast.get("forecast_minutes"),
        "weekly_target_hours": flt(profile.weekly_target_hours),
        "monthly_target_hours": flt(profile.monthly_target_hours),
        "target_period": profile.target_period,
        "vacation": _get_vacation_summary(profile, today),
    }
