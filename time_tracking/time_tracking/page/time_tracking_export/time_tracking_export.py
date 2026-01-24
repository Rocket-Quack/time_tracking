import io
import csv

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import cint, getdate
from frappe.utils.xlsxutils import make_xlsx

from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
    build_project_path_labels,
)


def get_context(context):
    context.no_cache = 1
    context.show_sidebar = True


def _is_admin(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def _get_date_range(from_date, to_date):
    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are required."))
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    if end_date < start_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


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


def _get_date_formatter(date_format):
    fmt = (date_format or "DD.MM.YYYY").strip().upper()
    if fmt == "YYYY-MM-DD":
        return "%Y-%m-%d"
    return "%d.%m.%Y"


def _format_decimal(value, separator):
    hours = f"{value:.2f}"
    if separator == ",":
        return hours.replace(".", ",")
    return hours


@frappe.whitelist()
def export_bookings(
    export_format="CSV",
    from_date=None,
    to_date=None,
    project=None,
    include_child_projects=0,
    user=None,
    date_format="DD.MM.YYYY",
    decimal_separator=".",
):
    if not _is_admin():
        frappe.throw(_("Not permitted."))

    start_date, end_date = _get_date_range(from_date, to_date)
    include_children = cint(include_child_projects) == 1
    project_names = _get_project_names(project, include_children)
    export_format = (export_format or "CSV").strip().upper()

    tb = DocType("Time Booking")
    ttp = DocType("Time Tracking Profile")
    usr = DocType("User")

    query = (
        frappe.qb.from_(tb)
        .left_join(ttp)
        .on(ttp.name == tb.time_tracking_profile)
        .left_join(usr)
        .on(usr.name == ttp.user)
        .select(
            tb.date.as_("date"),
            ttp.user.as_("user"),
            usr.full_name.as_("employee_name"),
            tb.project.as_("project"),
            tb.notes.as_("note"),
            tb.duration_minutes.as_("duration_minutes"),
        )
        .where(tb.date.between(start_date, end_date))
    )

    if project_names:
        query = query.where(tb.project.isin(project_names))

    if user:
        query = query.where(ttp.user == user)

    query = query.orderby(tb.date, tb.project, ttp.user)
    rows = query.run(as_dict=True)

    project_names_used = {row.project for row in rows if row.project}
    project_paths = build_project_path_labels(list(project_names_used))

    date_fmt = _get_date_formatter(date_format)
    separator = "," if decimal_separator == "," else "."

    columns = [
        _("Date"),
        _("Employee"),
        _("Project"),
        _("Comment"),
        _("Hours"),
    ]
    data = []

    for row in rows:
        date_value = row.date.strftime(date_fmt) if row.date else ""
        employee = row.employee_name or row.user or ""
        project_label = project_paths.get(row.project, row.project or "")
        hours_value = (row.duration_minutes or 0) / 60
        if export_format == "XLSX" and separator == ".":
            hours_display = round(hours_value, 2)
        else:
            hours_display = _format_decimal(hours_value, separator)

        data.append([date_value, employee, project_label, row.note or "", hours_display])

    if export_format == "XLSX":
        output = make_xlsx([columns] + data, _("Time Tracking Export"))
        filename = f"time-tracking-export-{start_date}-{end_date}.xlsx"
        frappe.response["filename"] = filename
        frappe.response["filecontent"] = output
        frappe.response["type"] = "binary"
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    writer.writerows(data)
    content = buffer.getvalue()

    filename = f"time-tracking-export-{start_date}-{end_date}.csv"
    frappe.response["filename"] = filename
    frappe.response["filecontent"] = content
    frappe.response["type"] = "binary"
