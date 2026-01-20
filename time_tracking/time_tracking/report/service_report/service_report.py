import calendar

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

PERIOD_DAY = "Day"
PERIOD_WEEK = "Week"
PERIOD_MONTH = "Month"
PERIOD_RANGE = "Range"


def _get_period_range(filters):
    period = (filters or {}).get("period") or PERIOD_MONTH
    period = period.strip()

    if period == PERIOD_RANGE:
        start_date = getdate(filters.get("from_date") or nowdate())
        end_date = getdate(filters.get("to_date") or start_date)
        if end_date < start_date:
            start_date, end_date = end_date, start_date
        return start_date, end_date

    date_value = getdate(filters.get("date") or nowdate())
    if period == PERIOD_WEEK:
        start_date = add_days(date_value, -date_value.weekday())
        end_date = add_days(start_date, 6)
        return start_date, end_date

    if period == PERIOD_MONTH:
        start_date = date_value.replace(day=1)
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = start_date.replace(day=last_day)
        return start_date, end_date

    return date_value, date_value


def _get_project_names(project, include_children):
    if not project:
        return None

    if not include_children:
        return [project]

    node = frappe.db.get_value(
        "Time Tracking Project",
        project,
        ["lft", "rgt"],
        as_dict=True,
    )
    if not node:
        return [project]

    return frappe.get_all(
        "Time Tracking Project",
        filters={"lft": [">=", node.lft], "rgt": ["<=", node.rgt]},
        pluck="name",
        order_by="lft asc",
    )


def _get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 170,
        },
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Time Tracking Project",
            "width": 220,
        },
        {
            "label": _("Note"),
            "fieldname": "note",
            "fieldtype": "Data",
            "width": 260,
        },
        {
            "label": _("Hours"),
            "fieldname": "hours",
            "fieldtype": "Float",
            "width": 90,
        },
    ]


def execute(filters=None):
    filters = filters or {}

    start_date, end_date = _get_period_range(filters)
    project = filters.get("project")
    include_children = flt(filters.get("include_child_projects")) == 1
    project_names = _get_project_names(project, include_children)
    user_filter = (filters.get("user") or "").strip()

    conditions = ["tb.date between %(start_date)s and %(end_date)s"]
    values = {"start_date": start_date, "end_date": end_date}

    if project_names:
        conditions.append("tb.project in %(projects)s")
        values["projects"] = tuple(project_names)

    if user_filter:
        conditions.append("ttp.user = %(user)s")
        values["user"] = user_filter

    where_clause = " and ".join(conditions)
    rows = frappe.db.sql(
        f"""
        select
            tb.date as date,
            ttp.user as user,
            tb.project as project,
            tb.notes as note,
            tb.duration_minutes as duration_minutes
        from `tabTime Booking` tb
        left join `tabTime Tracking Profile` ttp
            on ttp.name = tb.time_tracking_profile
        where {where_clause}
        order by tb.date asc, tb.project asc, ttp.user asc
        """,
        values,
        as_dict=True,
    )

    data = []
    for row in rows:
        data.append(
            {
                "date": row.date,
                "user": row.user,
                "project": row.project,
                "note": row.note,
                "hours": flt(row.duration_minutes) / 60,
            }
        )

    return _get_columns(), data
