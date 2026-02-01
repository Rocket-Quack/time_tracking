import frappe
from frappe import _
from frappe.utils import cint, flt

from time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project import (
	build_project_path_labels,
)

STATUS_ALL = "All"
STATUS_NO_BUDGET = "No Budget"


def _get_columns():
	return [
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Time Tracking Project",
			"width": 220,
		},
		{
			"label": _("Group Project"),
			"fieldname": "is_group",
			"fieldtype": "Check",
			"width": 90,
		},
		{
			"label": _("Internal"),
			"fieldname": "is_internal",
			"fieldtype": "Check",
			"width": 80,
		},
		{
			"label": _("Budget Hours"),
			"fieldname": "budget_hours",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Budget Amount"),
			"fieldname": "budget_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Actual Hours"),
			"fieldname": "actual_hours",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Actual Amount"),
			"fieldname": "actual_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Actual Pay Amount"),
			"fieldname": "actual_pay_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Profit Amount"),
			"fieldname": "profit_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Profit Margin (%)"),
			"fieldname": "profit_percent",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Hours Used (%)"),
			"fieldname": "hours_used_percent",
			"fieldtype": "Percent",
			"width": 120,
		},
		{
			"label": _("Amount Used (%)"),
			"fieldname": "amount_used_percent",
			"fieldtype": "Percent",
			"width": 120,
		},
		{
			"label": _("Hours Delta"),
			"fieldname": "hours_delta",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Amount Delta"),
			"fieldname": "amount_delta",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"label": _("Budget Status"),
			"fieldname": "budget_status",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def _get_projects(filters):
	filters = filters or {}
	project_filters = {}

	if not cint(filters.get("include_groups")):
		project_filters["is_group"] = 0

	internal_filter = (filters.get("internal_filter") or "All").strip()
	if internal_filter == "Only Internal":
		project_filters["is_internal"] = 1
	elif internal_filter == "Exclude Internal":
		project_filters["is_internal"] = 0

	return frappe.get_all(
		"Time Tracking Project",
		filters=project_filters,
		fields=[
			"name",
			"project_name",
			"is_group",
			"is_internal",
			"budget_hours",
			"budget_amount",
			"total_budget_hours",
			"total_budget_amount",
			"actual_hours",
			"actual_amount",
			"actual_pay_amount",
			"profit_amount",
			"profit_percent",
			"budget_status",
			"budget_hours_percent",
			"budget_amount_percent",
		],
		order_by="project_name",
	)


def _resolve_budget_values(project):
	if cint(project.is_group):
		budget_hours = flt(project.total_budget_hours)
		budget_amount = flt(project.total_budget_amount)
	else:
		budget_hours = flt(project.budget_hours)
		budget_amount = flt(project.budget_amount)
	return budget_hours, budget_amount


def execute(filters=None):
	filters = filters or {}
	status_filter = (filters.get("status") or STATUS_ALL).strip()

	rows = []
	projects = _get_projects(filters)
	path_labels = build_project_path_labels([project.name for project in projects])
	for project in projects:
		budget_hours, budget_amount = _resolve_budget_values(project)
		actual_hours = flt(project.actual_hours)
		actual_amount = flt(project.actual_amount)

		if status_filter != STATUS_ALL:
			if status_filter == STATUS_NO_BUDGET:
				if budget_hours > 0 or budget_amount > 0:
					continue
			elif project.budget_status != status_filter:
				continue

		hours_delta = None
		if budget_hours > 0:
			hours_delta = flt(actual_hours - budget_hours, 2)

		amount_delta = None
		if budget_amount > 0:
			amount_delta = flt(actual_amount - budget_amount, 2)

		rows.append(
			{
				"project": project.name,
				"project_label": path_labels.get(project.name, project.project_name or project.name),
				"is_group": cint(project.is_group),
				"is_internal": cint(project.is_internal),
				"budget_hours": flt(budget_hours, 2),
				"budget_amount": flt(budget_amount, 2),
				"actual_hours": flt(actual_hours, 2),
				"actual_amount": flt(actual_amount, 2),
				"actual_pay_amount": flt(project.actual_pay_amount, 2),
				"profit_amount": flt(project.profit_amount, 2),
				"profit_percent": flt(project.profit_percent, 2),
				"hours_used_percent": flt(project.budget_hours_percent, 2),
				"amount_used_percent": flt(project.budget_amount_percent, 2),
				"hours_delta": hours_delta,
				"amount_delta": amount_delta,
				"budget_status": project.budget_status or "",
			}
		)

	return _get_columns(), rows
