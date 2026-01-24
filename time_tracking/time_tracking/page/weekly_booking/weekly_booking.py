import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, formatdate, getdate

from time_tracking.time_tracking.overtime_utils import (
    get_holiday_dates_for_range,
    get_weekly_forecast,
    recalculate_overtime_for_date,
)
from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
    build_project_path_labels,
)
from time_tracking.time_tracking.vacation_utils import (
    get_hours_per_vacation_day,
    get_vacation_balance,
    get_vacation_project,
    get_sickness_project,
    validate_holiday_list_for_date,
)

DAY_FIELDS = [
    "monday_hours",
    "tuesday_hours",
    "wednesday_hours",
    "thursday_hours",
    "friday_hours",
    "saturday_hours",
    "sunday_hours",
]


def get_context(context):
    context.no_cache = True
    return {}


def _is_admin():
    roles = frappe.get_roles(frappe.session.user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def _require_profile(user):
    profile_name = _get_profile_name(user)
    if not profile_name:
        frappe.throw(_("Time Tracking Profile is required."))
    return profile_name


def _get_week_info(week_start_date):
    start_date = getdate(week_start_date)
    end_date = add_days(start_date, 6)
    iso_year, calendar_week, _ = start_date.isocalendar()
    calendar_year = iso_year
    period_label = f"{formatdate(start_date, 'dd.MM.yyyy')} - {formatdate(end_date, 'dd.MM.yyyy')}"

    warning = None
    if start_date.weekday() != 0:
        warning = _("Week start date should be a Monday.")

    return calendar_week, calendar_year, end_date, period_label, warning


def _coerce_hours(value, fieldname):
    hours = flt(value or 0)
    if hours < 0:
        frappe.throw(_("Hours for {0} cannot be negative.").format(fieldname))
    return hours


def _get_increment_minutes():
    return cint(
        frappe.db.get_single_value("Time Tracking Settings", "time_booking_increment_minutes")
        or 15
    )


def _get_day_label_date_format():
    return (
        frappe.db.get_single_value("Time Tracking Settings", "weekly_booking_day_label_format")
        or "DD.MM.YYYY"
    )


def _get_weekly_target_hours(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "weekly_target_hours")


def _get_monthly_target_hours(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "monthly_target_hours")


def _get_target_period(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "target_period")


def _get_overtime_balance_hours(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "overtime_balance_hours")


def _get_month_total_hours(user, week_start_date):
    start_date = getdate(week_start_date)
    month_start = start_date.replace(day=1)
    last_day = calendar.monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=last_day)
    total_minutes = _get_time_booking_minutes(user, month_start, month_end)

    profile_name = _get_profile_name(user)
    if not profile_name:
        return total_minutes / 60

    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    hours_per_day = flt(get_hours_per_vacation_day(profile))
    if hours_per_day > 0:
        holiday_dates = get_holiday_dates_for_range(month_start, month_end)
        total_minutes += len(holiday_dates) * hours_per_day * 60
    return total_minutes / 60


def _get_profile_name(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "name")


def _get_time_booking_minutes(user, start_date, end_date):
    profile_name = _get_profile_name(user)
    if not profile_name:
        return 0

    durations = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        pluck="duration_minutes",
    )
    return sum(flt(duration) for duration in durations)


def _get_assigned_projects(user):
    profile_name = _require_profile(user)

    assignments = frappe.get_all(
        "Time Tracking Profile Project",
        filters={
            "parenttype": "Time Tracking Profile",
            "parent": profile_name,
            "parentfield": "project_assignments",
            "active": 1,
        },
        fields=["project"],
    )
    project_names = [row.project for row in assignments if row.project]
    vacation_project = get_vacation_project()
    if vacation_project and vacation_project not in project_names:
        project_names.append(vacation_project)
    sickness_project = get_sickness_project()
    if sickness_project and sickness_project not in project_names:
        project_names.append(sickness_project)
    if not project_names:
        return []

    projects = frappe.get_all(
        "Time Tracking Project",
        filters={"name": ["in", project_names], "is_group": 0, "not_bookable": 0},
        fields=["name", "project_name"],
    )
    project_map = {project.name: project for project in projects}
    path_labels = build_project_path_labels(list(project_map.keys()))
    ordered = []
    for name in project_names:
        if name not in project_map:
            continue
        project = project_map[name]
        project.path_label = path_labels.get(name, project.project_name or name)
        ordered.append(project)
    return ordered


def _get_assigned_project_names(user):
    return {project.name for project in _get_assigned_projects(user)}


def _get_not_bookable_projects(project_names):
    if not project_names:
        return set()

    return set(
        frappe.get_all(
            "Time Tracking Project",
            filters={"name": ["in", list(project_names)], "not_bookable": 1},
            pluck="name",
        )
    )


def _get_vacation_summary(profile_name, week_start_date):
    vacation_project = get_vacation_project()
    if not vacation_project:
        return {"enabled": False}

    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    balance = get_vacation_balance(profile, week_start_date)
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


def _get_time_booking_rows(user, week_start_date):
    profile_name = _require_profile(user)

    week_start = getdate(week_start_date)
    week_end = add_days(week_start, 6)

    bookings = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [week_start, week_end]],
        },
        fields=["project", "notes", "date", "duration_minutes"],
    )
    if not bookings:
        return []

    day_fields = DAY_FIELDS
    rows = {}

    for booking in bookings:
        if not booking.project or not booking.date:
            continue

        note = booking.notes or ""
        key = (booking.project, note)

        row = rows.get(key)
        if not row:
            row = {"project": booking.project, "note": note}
            row.update({field: 0 for field in day_fields})
            rows[key] = row

        day_index = (getdate(booking.date) - week_start).days
        if 0 <= day_index < len(day_fields):
            row[day_fields[day_index]] += flt(booking.duration_minutes) / 60

    return list(rows.values())


def _get_previous_week_rows(user, week_start_date):
    week_start = getdate(week_start_date)
    previous_week_start = add_days(week_start, -7)
    rows = _get_time_booking_rows(user, previous_week_start)
    if not rows:
        return []

    project_names = {row.get("project") for row in rows if row.get("project")}
    not_bookable_projects = _get_not_bookable_projects(project_names)
    if not not_bookable_projects:
        return rows

    return [row for row in rows if row.get("project") not in not_bookable_projects]


def _build_booking_minutes_map(bookings):
    minutes_map = {}
    for booking in bookings:
        date_key = str(getdate(booking.date))
        key = (booking.project, booking.notes or "", date_key)
        minutes_map[key] = minutes_map.get(key, 0) + int(flt(booking.duration_minutes))
    return minutes_map


@frappe.whitelist()
def get_weekly_booking(user=None, week_start_date=None):
    if not week_start_date:
        frappe.throw(_("Week start date is required."))

    if not user:
        user = frappe.session.user

    if user != frappe.session.user and not _is_admin():
        frappe.throw(_("Not permitted to load bookings for another user."))

    profile_name = _require_profile(user)

    calendar_week, calendar_year, week_end_date, period_label, warning = _get_week_info(
        week_start_date
    )

    response = {
        "rows": _get_time_booking_rows(user, week_start_date),
        "previous_week_rows": _get_previous_week_rows(user, week_start_date),
        "warning": warning,
        "calendar_week": calendar_week,
        "calendar_year": calendar_year,
        "week_end_date": week_end_date,
        "period_label": period_label,
        "increment_minutes": _get_increment_minutes(),
        "day_label_date_format": _get_day_label_date_format(),
        "weekly_target_hours": _get_weekly_target_hours(user),
        "monthly_target_hours": _get_monthly_target_hours(user),
        "target_period": _get_target_period(user),
        "overtime_balance_hours": _get_overtime_balance_hours(user),
        "monthly_total_hours": _get_month_total_hours(user, week_start_date),
    }

    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    weekly_forecast = get_weekly_forecast(profile, week_start_date)
    response.update(
        {
            "weekly_forecast_minutes": weekly_forecast.get("forecast_minutes"),
            "weekly_actual_minutes": weekly_forecast.get("actual_minutes"),
            "holiday_dates": weekly_forecast.get("holiday_dates"),
            "holiday_hours_per_day": flt(get_hours_per_vacation_day(profile)),
        }
    )

    response["vacation"] = _get_vacation_summary(profile_name, week_start_date)
    return response


@frappe.whitelist()
def get_assigned_projects(user=None):
    if not user:
        user = frappe.session.user

    if user != frappe.session.user and not _is_admin():
        frappe.throw(_("Not permitted to load projects for another user."))

    _require_profile(user)

    return _get_assigned_projects(user)


@frappe.whitelist()
def save_weekly_booking(data):
    if not data:
        frappe.throw(_("No data received."))

    payload = frappe.parse_json(data)
    user = payload.get("user") or frappe.session.user
    week_start_date = payload.get("week_start_date")
    rows = payload.get("rows") or []

    if not week_start_date:
        frappe.throw(_("Week start date is required."))

    if user != frappe.session.user and not _is_admin():
        frappe.throw(_("Not permitted to save bookings for another user."))

    profile_name = _require_profile(user)
    week_start = getdate(week_start_date)
    week_end = add_days(week_start, 6)

    hour_fields = DAY_FIELDS
    row_projects = {row.get("project") for row in rows if row.get("project")}
    existing_bookings = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [week_start, week_end]],
        },
        fields=["project", "notes", "date", "duration_minutes"],
    )
    existing_minutes = _build_booking_minutes_map(existing_bookings) if existing_bookings else {}
    existing_projects = {booking.project for booking in existing_bookings if booking.project}
    not_bookable_projects = _get_not_bookable_projects(row_projects | existing_projects)
    existing_not_bookable_minutes = {}
    if existing_minutes and not_bookable_projects:
        existing_not_bookable_minutes = {
            key: minutes
            for key, minutes in existing_minutes.items()
            if key[0] in not_bookable_projects
        }

    assigned_project_names = None
    existing_unassigned_minutes = {}
    existing_unassigned_projects = set()
    row_unassigned_minutes = {}
    row_not_bookable_minutes = {}
    if not _is_admin():
        assigned_project_names = _get_assigned_project_names(user)
        if existing_minutes:
            if assigned_project_names:
                existing_unassigned_minutes = {
                    key: minutes
                    for key, minutes in existing_minutes.items()
                    if key[0] not in assigned_project_names
                    and key[0] not in not_bookable_projects
                }
            else:
                existing_unassigned_minutes = {
                    key: minutes
                    for key, minutes in existing_minutes.items()
                    if key[0] not in not_bookable_projects
                }
        existing_unassigned_projects = {key[0] for key in existing_unassigned_minutes}

    increment = _get_increment_minutes()
    time_bookings = []

    frappe.flags.skip_overtime_recalc = True
    try:
        for row in rows:
            row_project = row.get("project")
            row_note = (row.get("note") or "").strip()
            hours = {field: _coerce_hours(row.get(field), field) for field in hour_fields}

            if not row_project and not row_note and not any(hours.values()):
                continue

            if any(hours.values()):
                if not row_project:
                    frappe.throw(_("Project is required for bookings."))
                if not row_note:
                    frappe.throw(_("Note is required for bookings."))

            if row_project:
                if row_project in not_bookable_projects:
                    for idx, field in enumerate(hour_fields):
                        minutes = int(round(flt(hours.get(field)) * 60))
                        if minutes <= 0:
                            continue
                        date_key = str(add_days(week_start, idx))
                        key = (row_project, row_note, date_key)
                        row_not_bookable_minutes[key] = (
                            row_not_bookable_minutes.get(key, 0) + minutes
                        )
                    continue

                if assigned_project_names is not None and row_project not in assigned_project_names:
                    if row_project not in existing_unassigned_projects:
                        frappe.throw(
                            _("Project {0} is not assigned to your profile.").format(row_project)
                        )
                    for idx, field in enumerate(hour_fields):
                        minutes = int(round(flt(hours.get(field)) * 60))
                        if minutes <= 0:
                            continue
                        date_key = str(add_days(week_start, idx))
                        key = (row_project, row_note, date_key)
                        row_unassigned_minutes[key] = row_unassigned_minutes.get(key, 0) + minutes
                    continue

                if not frappe.db.exists("Time Tracking Project", row_project):
                    frappe.throw(_("Project {0} does not exist.").format(row_project))

                is_group = frappe.db.get_value(
                    "Time Tracking Project", row_project, "is_group"
                )
                if is_group:
                    frappe.throw(
                        _("Project {0} is a group and cannot be booked.").format(row_project)
                    )

            for idx, field in enumerate(hour_fields):
                minutes = int(round(flt(hours.get(field)) * 60))
                if minutes <= 0:
                    continue
                if minutes % increment:
                    frappe.throw(
                        _("Duration must be a multiple of {0} minutes.").format(increment)
                    )

                time_bookings.append(
                    {
                        "date": add_days(week_start, idx),
                        "project": row_project,
                        "notes": row_note,
                        "duration_minutes": minutes,
                    }
                )

        if time_bookings:
            booking_dates = {booking["date"] for booking in time_bookings}
            for booking_date in booking_dates:
                validate_holiday_list_for_date(booking_date)

        if existing_not_bookable_minutes or row_not_bookable_minutes:
            mismatched_projects = set()
            for key, minutes in existing_not_bookable_minutes.items():
                if row_not_bookable_minutes.get(key) != minutes:
                    mismatched_projects.add(key[0])
            for key in row_not_bookable_minutes:
                if key not in existing_not_bookable_minutes:
                    mismatched_projects.add(key[0])
            if mismatched_projects:
                project_list = ", ".join(sorted(mismatched_projects))
                frappe.throw(
                    _("Projects not bookable cannot be edited: {0}").format(project_list)
                )

        if assigned_project_names is not None and existing_unassigned_minutes:
            mismatched_projects = set()
            for key, minutes in existing_unassigned_minutes.items():
                if row_unassigned_minutes.get(key) != minutes:
                    mismatched_projects.add(key[0])
            for key in row_unassigned_minutes:
                if key not in existing_unassigned_minutes:
                    mismatched_projects.add(key[0])
            if mismatched_projects:
                project_list = ", ".join(sorted(mismatched_projects))
                frappe.throw(
                    _(
                        "Projects not assigned to your profile cannot be edited. Reassign to update: {0}"
                    ).format(project_list)
                )

        if assigned_project_names is None:
            delete_filters = {
                "time_tracking_profile": profile_name,
                "date": ["between", [week_start, week_end]],
            }
            if not_bookable_projects:
                delete_filters["project"] = ["not in", list(not_bookable_projects)]
            frappe.db.delete("Time Booking", delete_filters)
        elif assigned_project_names:
            editable_projects = set(assigned_project_names) - set(not_bookable_projects)
            if editable_projects:
                frappe.db.delete(
                    "Time Booking",
                    {
                        "time_tracking_profile": profile_name,
                        "date": ["between", [week_start, week_end]],
                        "project": ["in", list(editable_projects)],
                    },
                )

        for booking in time_bookings:
            doc = frappe.new_doc("Time Booking")
            doc.time_tracking_profile = profile_name
            doc.date = booking["date"]
            doc.project = booking["project"]
            doc.notes = booking.get("notes")
            doc.duration_minutes = booking["duration_minutes"]
            doc.insert()
    finally:
        frappe.flags.skip_overtime_recalc = False

    recalculate_overtime_for_date(user, week_start_date, source="weekly_booking")

    calendar_week, calendar_year, week_end_date, period_label, warning = _get_week_info(
        week_start_date
    )
    profile = frappe.get_doc("Time Tracking Profile", profile_name)
    weekly_forecast = get_weekly_forecast(profile, week_start_date)

    return {
        "status": "ok",
        "warning": warning,
        "calendar_week": calendar_week,
        "calendar_year": calendar_year,
        "week_end_date": week_end_date,
        "period_label": period_label,
        "monthly_total_hours": _get_month_total_hours(user, week_start_date),
        "target_period": _get_target_period(user),
        "overtime_balance_hours": profile.overtime_balance_hours,
        "weekly_forecast_minutes": weekly_forecast.get("forecast_minutes"),
        "weekly_actual_minutes": weekly_forecast.get("actual_minutes"),
        "holiday_dates": weekly_forecast.get("holiday_dates"),
        "holiday_hours_per_day": flt(get_hours_per_vacation_day(profile)),
        "vacation": _get_vacation_summary(profile_name, week_start_date),
    }
