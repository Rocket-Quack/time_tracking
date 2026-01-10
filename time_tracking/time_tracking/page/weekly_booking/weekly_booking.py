import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, formatdate, getdate


def get_context(context):
    context.no_cache = True
    return {}


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


def _get_existing_doc_name(user, week_start_date):
    return frappe.db.get_value(
        "Weekly Booking Data", {"user": user, "week_start_date": week_start_date}, "name"
    )


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


def _get_overtime_balance_hours(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "overtime_balance_hours")


def _get_month_total_hours(user, week_start_date):
    start_date = getdate(week_start_date)
    month_start = start_date.replace(day=1)
    last_day = calendar.monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=last_day)
    overlap_start = add_days(month_start, -6)

    week_docs = frappe.get_all(
        "Weekly Booking Data",
        filters={
            "user": user,
            "week_start_date": ["between", [overlap_start, month_end]],
        },
        pluck="name",
    )

    if not week_docs:
        return 0

    total_minutes = 0
    day_fields = [
        "monday_hours",
        "tuesday_hours",
        "wednesday_hours",
        "thursday_hours",
        "friday_hours",
        "saturday_hours",
        "sunday_hours",
    ]

    for name in week_docs:
        doc = frappe.get_doc("Weekly Booking Data", name)
        week_start = getdate(doc.week_start_date)
        for row in doc.bookings:
            for idx, field in enumerate(day_fields):
                hours = flt(row.get(field))
                if not hours:
                    continue
                day_date = add_days(week_start, idx)
                if month_start <= day_date <= month_end:
                    total_minutes += hours * 60

    return total_minutes / 60


def _get_profile_name(user):
    return frappe.db.get_value("Time Tracking Profile", {"user": user}, "name")


def _get_assigned_projects(user):
    profile_name = _get_profile_name(user)
    if not profile_name:
        return []

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
    if not project_names:
        return []

    projects = frappe.get_all(
        "Time Tracking Project",
        filters={"name": ["in", project_names], "is_group": 0},
        fields=["name", "project_name"],
    )
    project_map = {project.name: project for project in projects}
    return [project_map[name] for name in project_names if name in project_map]


@frappe.whitelist()
def get_weekly_booking(user=None, week_start_date=None):
    if not week_start_date:
        frappe.throw(_("Week start date is required."))

    if not user:
        user = frappe.session.user

    if user != frappe.session.user and not frappe.has_role("System Manager"):
        frappe.throw(_("Not permitted to load bookings for another user."))

    doc_name = _get_existing_doc_name(user, week_start_date)
    if doc_name:
        doc = frappe.get_doc("Weekly Booking Data", doc_name)
    else:
        doc = frappe.new_doc("Weekly Booking Data")
        doc.user = user
        doc.week_start_date = week_start_date

    calendar_week, calendar_year, week_end_date, period_label, warning = _get_week_info(
        week_start_date
    )
    doc.calendar_week = calendar_week
    doc.calendar_year = calendar_year
    doc.week_end_date = week_end_date
    doc.period_label = period_label

    return {
        "doc": doc.as_dict(),
        "warning": warning,
        "increment_minutes": _get_increment_minutes(),
        "day_label_date_format": _get_day_label_date_format(),
        "weekly_target_hours": _get_weekly_target_hours(user),
        "monthly_target_hours": _get_monthly_target_hours(user),
        "overtime_balance_hours": _get_overtime_balance_hours(user),
        "monthly_total_hours": _get_month_total_hours(user, week_start_date),
    }


@frappe.whitelist()
def get_assigned_projects(user=None):
    if not user:
        user = frappe.session.user

    if user != frappe.session.user and not frappe.has_role("System Manager"):
        frappe.throw(_("Not permitted to load projects for another user."))

    return _get_assigned_projects(user)


@frappe.whitelist()
def save_weekly_booking(data):
    if not data:
        frappe.throw(_("No data received."))

    payload = frappe.parse_json(data)
    name = payload.get("name")
    user = payload.get("user") or frappe.session.user
    week_start_date = payload.get("week_start_date")
    rows = payload.get("rows") or []

    if not week_start_date:
        frappe.throw(_("Week start date is required."))

    if user != frappe.session.user and not frappe.has_role("System Manager"):
        frappe.throw(_("Not permitted to save bookings for another user."))

    if name:
        doc = frappe.get_doc("Weekly Booking Data", name)
    else:
        existing_name = _get_existing_doc_name(user, week_start_date)
        doc = frappe.get_doc("Weekly Booking Data", existing_name) if existing_name else None

    if doc and doc.user and doc.user != user and not frappe.has_role("System Manager"):
        frappe.throw(_("Not permitted to update another user's booking."))

    if not doc:
        doc = frappe.new_doc("Weekly Booking Data")

    doc.user = user
    doc.week_start_date = week_start_date

    calendar_week, calendar_year, week_end_date, period_label, warning = _get_week_info(
        week_start_date
    )
    doc.calendar_week = calendar_week
    doc.calendar_year = calendar_year
    doc.week_end_date = week_end_date
    doc.period_label = period_label

    doc.bookings = []

    hour_fields = [
        "monday_hours",
        "tuesday_hours",
        "wednesday_hours",
        "thursday_hours",
        "friday_hours",
        "saturday_hours",
        "sunday_hours",
    ]

    for row in rows:
        row_project = row.get("project")
        row_note = row.get("note")
        hours = {field: _coerce_hours(row.get(field), field) for field in hour_fields}

        if not row_project and not row_note and not any(hours.values()):
            continue

        if row_project:
            if not frappe.db.exists("Time Tracking Project", row_project):
                frappe.throw(_("Project {0} does not exist.").format(row_project))

            is_group = frappe.db.get_value("Time Tracking Project", row_project, "is_group")
            if is_group:
                frappe.throw(
                    _("Project {0} is a group and cannot be booked.").format(row_project)
                )

        row_dict = {"project": row_project, "note": row_note}
        row_dict.update(hours)
        doc.append("bookings", row_dict)

    doc.save()

    return {"status": "ok", "name": doc.name, "warning": warning}
