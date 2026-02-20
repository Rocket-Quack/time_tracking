import csv
import io

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
	format_map = {
		"DD.MM.YYYY": "%d.%m.%Y",
		"YYYY-MM-DD": "%Y-%m-%d",
		"DDMMYYYY": "%d%m%Y",
		"YYYYMMDD": "%Y%m%d",
	}
	return format_map.get(fmt, "%d.%m.%Y")


def _format_decimal(value, separator):
	hours = f"{value:.2f}"
	if separator == ",":
		return hours.replace(".", ",")
	return hours


def _get_duration_format(duration_format):
	raw = (duration_format or "Decimal Hours").strip()
	fmt = raw.split("(", 1)[0].strip().upper()
	if fmt in {"HH:MMH", "HH:MM"}:
		return "HH:MMH"
	if fmt in {"MINUTES", "MINUTES (TOTAL)"}:
		return "MINUTES"
	return "DECIMAL_HOURS"


def _get_duration_column_label(duration_format):
	if duration_format == "HH:MMH":
		return _("Duration (HH:MM)")
	if duration_format == "MINUTES":
		return _("Duration (Minutes)")
	return _("Hours")


def _format_duration(duration_minutes, duration_format, export_format, separator):
	total_minutes = int(round(duration_minutes or 0))

	if duration_format == "MINUTES":
		return total_minutes

	if duration_format == "HH:MMH":
		sign = "-" if total_minutes < 0 else ""
		absolute_minutes = abs(total_minutes)
		hours = absolute_minutes // 60
		minutes = absolute_minutes % 60
		return f"{sign}{hours}:{minutes:02d}"

	hours_value = total_minutes / 60
	if export_format == "XLSX" and separator == ".":
		return round(hours_value, 2)
	return _format_decimal(hours_value, separator)


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
	duration_format="Decimal Hours",
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
	duration_format_key = _get_duration_format(duration_format)

	columns = [
		_("Date"),
		_("Employee"),
		_("Project"),
		_("Comment"),
		_get_duration_column_label(duration_format_key),
	]
	data = []

	for row in rows:
		date_value = row.date.strftime(date_fmt) if row.date else ""
		employee = row.employee_name or row.user or ""
		project_label = project_paths.get(row.project, row.project or "")
		hours_display = _format_duration(row.duration_minutes, duration_format_key, export_format, separator)

		data.append([date_value, employee, project_label, row.note or "", hours_display])

	if export_format == "XLSX":
		output = make_xlsx([columns, *data], _("Time Tracking Export"))
		content = output.getvalue() if hasattr(output, "getvalue") else output
		if isinstance(content, str):
			content = content.encode("utf-8")
		filename = f"time-tracking-export-{start_date}-{end_date}.xlsx"
		frappe.response["filename"] = filename
		frappe.response["filecontent"] = content
		frappe.response["type"] = "binary"
		return

	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(columns)
	writer.writerows(data)
	content = buffer.getvalue().encode("utf-8")

	filename = f"time-tracking-export-{start_date}-{end_date}.csv"
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content
	frappe.response["type"] = "binary"
