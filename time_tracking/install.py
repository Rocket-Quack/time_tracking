import json
from pathlib import Path

import frappe


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


def _load_fixture_docs(filename):
	path = FIXTURE_ROOT / filename
	if not path.exists():
		frappe.log_error(f"Fixture file missing: {path}", "Time Tracking Fixture Sync")
		return []

	try:
		docs = json.loads(path.read_text(encoding="utf-8"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Time Tracking Fixture Sync")
		return []

	return docs if isinstance(docs, list) else []


def _upsert_fixture_doc(doctype, name, fixture_doc):
	meta_fields = {"creation", "modified", "modified_by", "owner", "idx", "docstatus"}
	payload = {k: v for k, v in fixture_doc.items() if k not in meta_fields}

	# Frappe v16 setups may not ship with a "Modules" workspace anymore.
	if doctype == "Workspace":
		parent_page = payload.get("parent_page")
		if parent_page and not frappe.db.exists("Workspace", parent_page):
			payload["parent_page"] = ""

	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		doc.update(payload)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(payload).insert(ignore_permissions=True)


def _sync_primary_workspace_fixtures():
	targets = [
		("custom_html_block.json", "Custom HTML Block", "Time Tracking Summary"),
		("workspace.json", "Workspace", "Time Tracking"),
	]

	for filename, doctype, name in targets:
		docs = _load_fixture_docs(filename)
		fixture_doc = next(
			(doc for doc in docs if doc.get("doctype") == doctype and doc.get("name") == name),
			None,
		)
		if not fixture_doc:
			frappe.log_error(
				f"{doctype} '{name}' not found in fixture {filename}",
				"Time Tracking Fixture Sync",
			)
			continue

		_upsert_fixture_doc(doctype, name, fixture_doc)


def after_install():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	_sync_primary_workspace_fixtures()
	backfill_time_tracking_role_hierarchy()


def after_migrate():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	_sync_primary_workspace_fixtures()
	backfill_time_tracking_role_hierarchy()
