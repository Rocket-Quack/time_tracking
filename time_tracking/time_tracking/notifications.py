import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, nowdate

from time_tracking.time_tracking.overtime_utils import get_holiday_dates_for_range


def _is_reminder_day(reminder_day, today):
    reminder_day = cint(reminder_day)
    if reminder_day <= 0:
        return False

    last_day = calendar.monthrange(today.year, today.month)[1]
    normalized_day = min(reminder_day, last_day)
    return today.day == normalized_day


def _get_profiles():
    return frappe.get_all(
        "Time Tracking Profile",
        fields=["name", "user", "creation"],
        filters={"user": ["!=", ""]},
    )


def _get_user_email(user):
    if not user or user in ("Administrator", "Guest"):
        return None
    user_doc = frappe.db.get_value("User", user, ["enabled", "email"], as_dict=True)
    if not user_doc or not user_doc.enabled:
        return None
    return user_doc.email or None


def _get_expected_workdays(start_date, end_date, holiday_dates):
    expected = set()
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in holiday_dates:
            expected.add(current)
        current = add_days(current, 1)
    return expected


def _get_booked_dates(profile_name, start_date, end_date):
    rows = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        fields=["date"],
        group_by="date",
    )
    return {getdate(row.date) for row in rows}


def send_monthly_booking_reminders():
    settings = frappe.get_cached_doc("Time Tracking Settings")
    if not cint(settings.enable_monthly_booking_reminder):
        return

    today = getdate(nowdate())
    if not _is_reminder_day(settings.monthly_booking_reminder_day, today):
        return

    month_start = today.replace(day=1)

    for profile in _get_profiles():
        start_date = max(month_start, getdate(profile.creation))
        if start_date > today:
            continue

        try:
            holiday_dates = get_holiday_dates_for_range(start_date, today)
        except Exception:
            frappe.log_error(
                "Failed to load holiday dates for reminder job.",
                "Time Tracking Reminder",
            )
            holiday_dates = set()

        expected_dates = _get_expected_workdays(start_date, today, holiday_dates)
        if not expected_dates:
            continue

        booked_dates = _get_booked_dates(profile.name, start_date, today)
        missing_dates = expected_dates - booked_dates
        if not missing_dates:
            continue

        recipient = _get_user_email(profile.user)
        if not recipient:
            continue

        month_label = calendar.month_name[today.month]
        missing_count = len(missing_dates)

        subject = _("Time Booking Reminder for {0} {1}").format(
            month_label, today.year
        )
        message = _(
            "You still have {0} missing booking days for {1} {2}. Please complete your time bookings."
        ).format(missing_count, month_label, today.year)

        frappe.sendmail(recipients=[recipient], subject=subject, message=message)
