import frappe

DEFAULT_WORKSPACE = "Time Tracking"


def ensure_default_workspace(login_manager=None):
	user = frappe.session.user
	if user in ("Guest",):
		return

	user_type = frappe.db.get_value("User", user, "user_type")
	if user_type != "System User":
		return

	if frappe.db.get_value("User", user, "default_workspace"):
		return

	if not frappe.db.exists("Workspace", DEFAULT_WORKSPACE):
		return

	frappe.db.set_value("User", user, "default_workspace", DEFAULT_WORKSPACE)
