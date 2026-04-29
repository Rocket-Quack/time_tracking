import frappe

DEFAULT_WORKSPACE = "Time Tracking"
DEFAULT_WORKSPACE_ROUTE = "/desk/time-tracking"


def ensure_default_workspace(login_manager=None):
	user = frappe.session.user
	if user in ("Guest",):
		return

	user_type = frappe.db.get_value("User", user, "user_type")
	if user_type != "System User":
		return

	if not frappe.db.exists("Workspace", DEFAULT_WORKSPACE):
		return

	default_workspace = frappe.db.get_value("User", user, "default_workspace")
	if default_workspace and default_workspace != DEFAULT_WORKSPACE:
		return

	# Work around Frappe's login redirect using `workspace.lower()` instead of a slug.
	frappe.local.flags.home_page = DEFAULT_WORKSPACE_ROUTE
