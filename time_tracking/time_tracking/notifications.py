import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, nowdate

from time_tracking.time_tracking.overtime_utils import get_holiday_dates_for_range

TRIGGER_MONTH_END = "Month End"
TRIGGER_MONTHLY = "Monthly"
TRIGGER_WEEKLY = "Weekly"
TRIGGER_INACTIVITY = "Inactivity"
TRIGGER_MISSING_THRESHOLD = "Missing Days Threshold"

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _is_reminder_day(reminder_day, today):
    reminder_day = cint(reminder_day)
    if reminder_day <= 0:
        return False

    last_day = calendar.monthrange(today.year, today.month)[1]
    normalized_day = min(reminder_day, last_day)
    return today.day == normalized_day


def _is_month_end(today):
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day == last_day


def _is_weekday_match(reminder_weekday, today):
    reminder_weekday = (reminder_weekday or "").strip()
    if reminder_weekday not in WEEKDAY_MAP:
        return False
    return today.weekday() == WEEKDAY_MAP[reminder_weekday]


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


def _get_last_booking_date(profile_name):
    rows = frappe.get_all(
        "Time Booking",
        filters={"time_tracking_profile": profile_name},
        fields=["max(date) as last_date"],
    )
    if rows and rows[0].last_date:
        return getdate(rows[0].last_date)
    return None


def _get_missing_dates(profile, start_date, end_date):
    if not start_date or not end_date or start_date > end_date:
        return set()

    try:
        holiday_dates = get_holiday_dates_for_range(start_date, end_date)
    except Exception:
        frappe.log_error(
            "Failed to load holiday dates for reminder job.",
            "Time Tracking Reminder",
        )
        holiday_dates = set()

    expected_dates = _get_expected_workdays(start_date, end_date, holiday_dates)
    if not expected_dates:
        return set()

    booked_dates = _get_booked_dates(profile.name, start_date, end_date)
    return expected_dates - booked_dates


def send_booking_reminders():
    settings = frappe.get_cached_doc("Time Tracking Settings")
    if not cint(settings.enable_monthly_booking_reminder):
        return

    today = getdate(nowdate())
    trigger = (settings.booking_reminder_trigger or TRIGGER_MONTH_END).strip()
    if trigger == TRIGGER_MONTHLY and not _is_reminder_day(
        settings.monthly_booking_reminder_day, today
    ):
        return
    if trigger == TRIGGER_MONTH_END and not _is_month_end(today):
        return
    if trigger == TRIGGER_WEEKLY and not _is_weekday_match(
        settings.booking_reminder_weekday, today
    ):
        return

    for profile in _get_profiles():
        profile_start = getdate(profile.creation)
        if profile_start > today:
            continue

        month_start = today.replace(day=1)
        if trigger == TRIGGER_WEEKLY:
            week_start = add_days(today, -today.weekday())
            start_date = max(week_start, profile_start)
            missing_dates = _get_missing_dates(profile, start_date, today)
            if not missing_dates:
                continue
            message = _(
                "You still have {0} missing booking days for this week. Please complete your time bookings."
            ).format(len(missing_dates))
        else:
            start_date = max(month_start, profile_start)
            missing_dates = _get_missing_dates(profile, start_date, today)
            if not missing_dates and trigger != TRIGGER_INACTIVITY:
                continue
            message = _(
                "You still have {0} missing booking days for {1} {2}. Please complete your time bookings."
            ).format(len(missing_dates), calendar.month_name[today.month], today.year)

        if trigger == TRIGGER_INACTIVITY:
            threshold = cint(settings.booking_reminder_inactivity_days or 0)
            last_booking = _get_last_booking_date(profile.name)
            last_activity = last_booking or profile_start
            inactive_days = (today - last_activity).days
            if threshold <= 0 or inactive_days < threshold:
                continue
            if not missing_dates:
                continue
            message = _(
                "You have not booked time for {0} days. Please update your time bookings."
            ).format(inactive_days)

        if trigger == TRIGGER_MISSING_THRESHOLD:
            threshold = cint(settings.booking_reminder_missing_days_threshold or 0)
            if threshold <= 0 or len(missing_dates) < threshold:
                continue

        recipient = _get_user_email(profile.user)
        if not recipient:
            continue

        subject = _("Time Booking Reminder")

        frappe.sendmail(recipients=[recipient], subject=subject, message=message)
