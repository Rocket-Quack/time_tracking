import frappe

ROLE_EMPLOYEE = "Time Tracking Employee"
ROLE_MANAGER = "Time Tracking Manager"
ROLE_ADMIN = "Time Tracking Admin"


def _get_missing_hierarchy_roles(role_names):
	missing_roles = set()
	if ROLE_ADMIN in role_names:
		missing_roles.update({ROLE_MANAGER, ROLE_EMPLOYEE} - role_names)
	if ROLE_MANAGER in role_names:
		missing_roles.update({ROLE_EMPLOYEE} - role_names)
	return sorted(missing_roles)


def _ensure_hierarchy_on_user_doc(user_doc):
	role_names = {row.role for row in (user_doc.roles or []) if row.role}
	missing_roles = _get_missing_hierarchy_roles(role_names)
	if not missing_roles:
		return False

	for role in missing_roles:
		user_doc.append("roles", {"role": role})
	return True


def enforce_role_hierarchy_on_user(doc, method=None):
	if not doc or doc.name in {"Guest"}:
		return
	_ensure_hierarchy_on_user_doc(doc)


def backfill_time_tracking_role_hierarchy():
	user_names = frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["not in", ["Guest"]]},
		pluck="name",
	)
	updated = 0
	for user_name in user_names:
		user_doc = frappe.get_doc("User", user_name)
		if not _ensure_hierarchy_on_user_doc(user_doc):
			continue
		user_doc.save(ignore_permissions=True)
		updated += 1
	return updated
