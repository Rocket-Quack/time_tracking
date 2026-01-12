import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

RATE_TYPE_ROLE = "Role"
RATE_TYPE_USER = "User"

BUDGET_STATUS_UNDER = "Under Budget"
BUDGET_STATUS_ON = "On Budget"
BUDGET_STATUS_OVER = "Over Budget"

class TimeTrackingProject(Document):
    def validate(self):
        self._set_budget_metrics()

    def _set_budget_metrics(self):
        metrics = _calculate_project_metrics(self)
        for field, value in metrics.items():
            self.set(field, value)

    def on_update(self):
        previous = self.get_doc_before_save()
        update_project_and_ancestors(self.name)

        if (
            previous
            and previous.parent_time_tracking_project != self.parent_time_tracking_project
        ):
            update_project_and_ancestors(previous.parent_time_tracking_project)

    def on_trash(self):
        self.flags._previous_parent = self.parent_time_tracking_project

    def after_delete(self):
        update_project_and_ancestors(getattr(self.flags, "_previous_parent", None))

    def get_indicator(self):
        status = (self.budget_status or "").strip()
        if not status:
            return

        if status == BUDGET_STATUS_OVER:
            color = "red"
        elif status == BUDGET_STATUS_ON:
            color = "green"
        else:
            color = "blue"

        return _(status), color, f"budget_status,=,{status}"


def handle_time_booking_insert(doc, method=None):
    update_project_and_ancestors(doc.project)


def handle_time_booking_update(doc, method=None):
    previous = doc.get_doc_before_save()
    project_names = {doc.project}
    if previous and previous.project and previous.project != doc.project:
        project_names.add(previous.project)
    for project_name in project_names:
        update_project_and_ancestors(project_name)


def handle_time_booking_trash(doc, method=None):
    update_project_and_ancestors(doc.project)


def update_project_and_ancestors(project_name):
    if not project_name:
        return

    update_project_metrics(project_name)
    for ancestor in _get_ancestor_names(project_name):
        update_project_metrics(ancestor)


def update_project_metrics(project_name):
    if not project_name:
        return

    doc = frappe.get_doc("Time Tracking Project", project_name)
    metrics = _calculate_project_metrics(doc)
    frappe.db.set_value(
        "Time Tracking Project",
        project_name,
        metrics,
        update_modified=False,
    )


def _calculate_project_metrics(doc):
    if doc.is_group:
        totals = _get_group_totals(doc.name)
        total_budget_hours = totals.get("total_budget_hours")
        total_budget_amount = totals.get("total_budget_amount")
        actual_hours = totals.get("actual_hours")
        actual_amount = totals.get("actual_amount")
    else:
        total_budget_hours = flt(doc.budget_hours)
        total_budget_amount = flt(doc.budget_amount)
        actual_hours, actual_amount = _get_leaf_actuals(doc.name)

    budget_hours_percent = _calculate_percent(actual_hours, total_budget_hours)
    budget_amount_percent = _calculate_percent(actual_amount, total_budget_amount)
    budget_status = _resolve_budget_status(
        [budget_hours_percent, budget_amount_percent],
        total_budget_hours,
        total_budget_amount,
    )

    return {
        "total_budget_hours": total_budget_hours,
        "total_budget_amount": total_budget_amount,
        "actual_hours": actual_hours,
        "actual_amount": actual_amount,
        "budget_hours_percent": budget_hours_percent,
        "budget_amount_percent": budget_amount_percent,
        "budget_status": budget_status,
    }


def _get_group_totals(project_name):
    totals = {
        "total_budget_hours": 0,
        "total_budget_amount": 0,
        "actual_hours": 0,
        "actual_amount": 0,
    }

    children = frappe.get_all(
        "Time Tracking Project",
        filters={"parent_time_tracking_project": project_name},
        fields=[
            "total_budget_hours",
            "total_budget_amount",
            "actual_hours",
            "actual_amount",
        ],
    )
    for child in children:
        totals["total_budget_hours"] += flt(child.total_budget_hours)
        totals["total_budget_amount"] += flt(child.total_budget_amount)
        totals["actual_hours"] += flt(child.actual_hours)
        totals["actual_amount"] += flt(child.actual_amount)

    return totals


def _get_leaf_actuals(project_name):
    rows = frappe.get_all(
        "Time Booking",
        filters={"project": project_name},
        fields=["time_tracking_profile", "sum(duration_minutes) as total_minutes"],
        group_by="time_tracking_profile",
    )

    settings = _get_rate_settings()
    rate_cache = {}
    total_minutes = 0
    total_amount = 0

    for row in rows:
        minutes = flt(row.total_minutes)
        total_minutes += minutes
        hourly_rate = _get_hourly_rate(row.time_tracking_profile, settings, rate_cache)
        total_amount += (minutes / 60) * hourly_rate

    return total_minutes / 60, total_amount


def _get_rate_settings():
    return {
        "rate_basis": frappe.db.get_single_value("Time Tracking Settings", "rate_basis")
        or RATE_TYPE_ROLE,
        "allow_profile_rate_override": cint(
            frappe.db.get_single_value(
                "Time Tracking Settings", "allow_profile_rate_override"
            )
            or 0
        ),
    }


def _get_hourly_rate(profile_name, settings, cache):
    if profile_name in cache:
        return cache[profile_name]

    profile = frappe.db.get_value(
        "Time Tracking Profile",
        profile_name,
        ["user", "hourly_rate"],
        as_dict=True,
    )
    if not profile:
        cache[profile_name] = 0
        return 0

    rate = 0
    if settings.get("allow_profile_rate_override") and flt(profile.hourly_rate) > 0:
        rate = flt(profile.hourly_rate)
    elif settings.get("rate_basis") == RATE_TYPE_USER:
        rate = flt(
            frappe.db.get_value(
                "Time Tracking Rate",
                {"rate_type": RATE_TYPE_USER, "user": profile.user},
                "hourly_rate",
            )
            or 0
        )
    else:
        roles = frappe.get_roles(profile.user)
        if roles:
            rates = frappe.get_all(
                "Time Tracking Rate",
                filters={"rate_type": RATE_TYPE_ROLE, "role": ["in", roles]},
                pluck="hourly_rate",
            )
            rate = max((flt(value) for value in rates), default=0)

    cache[profile_name] = rate
    return rate


def _calculate_percent(actual, budget):
    budget_value = flt(budget)
    if budget_value <= 0:
        return 0
    return flt((flt(actual) / budget_value) * 100, 2)


def _resolve_budget_status(percent_values, total_budget_hours, total_budget_amount):
    candidates = []
    if flt(total_budget_hours) > 0:
        candidates.append(flt(percent_values[0]))
    if flt(total_budget_amount) > 0:
        candidates.append(flt(percent_values[1]))

    if not candidates:
        return ""

    max_percent = max(candidates)
    if max_percent > 100:
        return BUDGET_STATUS_OVER
    if max_percent >= 100:
        return BUDGET_STATUS_ON
    return BUDGET_STATUS_UNDER


def _get_ancestor_names(project_name):
    node = frappe.db.get_value(
        "Time Tracking Project",
        project_name,
        ["lft", "rgt"],
        as_dict=True,
    )
    if not node:
        return []

    return frappe.get_all(
        "Time Tracking Project",
        filters={"lft": ["<", node.lft], "rgt": [">", node.rgt]},
        pluck="name",
        order_by="lft desc",
    )


@frappe.whitelist()
def recalculate_all_project_metrics():
    projects = frappe.get_all(
        "Time Tracking Project",
        fields=["name"],
        order_by="lft desc",
    )
    for project in projects:
        update_project_metrics(project.name)


@frappe.whitelist()
def get_project_tree_nodes(doctype, parent="", **filters):
    parent_field = "parent_" + frappe.scrub(doctype)
    tree_filters = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]

    return frappe.get_list(
        doctype,
        fields=[
            "name as value",
            "project_name as title",
            "is_group as expandable",
            "budget_hours",
            "budget_amount",
            "budget_status",
            "budget_hours_percent",
            "budget_amount_percent",
            "total_budget_hours",
            "total_budget_amount",
        ],
        filters=tree_filters,
        order_by="name",
    )
