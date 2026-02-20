import json
from pathlib import Path

import frappe


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


def _get_sidebar_item_icon(label, link_type, link_to):
	label_key = (label or "").strip().lower()
	route_key = (link_to or "").strip().lower()
	type_key = (link_type or "").strip()

	by_label = {
		"home": "house",
		"weekly booking": "notebook-pen",
		"time booking": "clock-3",
		"my project access": "shield-check",
		"monthly time tracking summary": "chart-bar",
		"yearly time tracking summary": "chart-line",
		"project budget overview": "hand-coins",
		"single booking service report": "file-chart-column",
		"time tracking import wizard": "import",
		"time tracking export": "download",
		"time tracking project": "folder-open",
		"time tracking profile": "user-round-cog",
		"time tracking settings": "settings-2",
		"holiday list": "calendar-days",
	}
	if label_key in by_label:
		return by_label[label_key]

	by_route = {
		"weekly-booking": "notebook-pen",
		"time-tracking-import-wizard": "import",
		"time-tracking-export": "download",
	}
	if route_key in by_route:
		return by_route[route_key]

	return {
		"Workspace": "house",
		"Report": "file-text",
		"Page": "panel-top",
		"DocType": "table",
		"URL": "link",
	}.get(type_key, "list")


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


def _sync_time_tracking_sidebar():
	if not frappe.db.exists("Workspace", "Time Tracking"):
		return

	workspace = frappe.get_doc("Workspace", "Time Tracking")
	sidebar_name = workspace.title or workspace.name

	if frappe.db.exists("Workspace Sidebar", sidebar_name):
		sidebar = frappe.get_doc("Workspace Sidebar", sidebar_name)
	else:
		sidebar = frappe.new_doc("Workspace Sidebar")
		sidebar.title = sidebar_name

	sidebar.module = workspace.module
	sidebar.app = "time_tracking"
	sidebar.header_icon = workspace.icon or "clock"
	sidebar.set("items", [])
	items = [
		{
			"label": "Home",
			"link_to": workspace.name,
			"link_type": "Workspace",
			"type": "Link",
			"icon": _get_sidebar_item_icon("Home", "Workspace", workspace.name),
			"idx": 1,
		}
	]
	next_idx = 2

	ungrouped_links = []
	grouped_links = []
	current_group_label = None
	current_group_links = []

	for link in workspace.links:
		if link.type == "Card Break":
			if current_group_label and current_group_links:
				grouped_links.append((current_group_label, current_group_links))
			current_group_label = link.label
			current_group_links = []
			continue

		if link.type != "Link" or not link.link_to or not link.link_type:
			continue

		if current_group_label:
			current_group_links.append(link)
		else:
			ungrouped_links.append(link)

	if current_group_label and current_group_links:
		grouped_links.append((current_group_label, current_group_links))

	for link in ungrouped_links:
		items.append(
			{
				"label": link.label,
				"link_to": link.link_to,
				"link_type": link.link_type,
				"type": "Link",
				"icon": _get_sidebar_item_icon(link.label, link.link_type, link.link_to),
				"idx": next_idx,
			}
		)
		next_idx += 1

	for group_label, links in grouped_links:
		items.append(
			{
				"label": group_label,
				"type": "Section Break",
				"idx": next_idx,
			}
		)
		next_idx += 1
		for link in links:
			items.append(
				{
					"label": link.label,
					"link_to": link.link_to,
					"link_type": link.link_type,
					"type": "Link",
					"icon": _get_sidebar_item_icon(link.label, link.link_type, link.link_to),
					"child": 1,
					"idx": next_idx,
				}
			)
			next_idx += 1

	if len(items) == 1:
		for shortcut in workspace.shortcuts:
			items.append(
				{
					"label": shortcut.label,
					"link_to": shortcut.link_to,
					"link_type": shortcut.type,
					"type": "Link",
					"icon": _get_sidebar_item_icon(shortcut.label, shortcut.type, shortcut.link_to),
					"idx": next_idx,
				}
			)
			next_idx += 1

	for item in items:
		sidebar.append("items", item)

	sidebar.save(ignore_permissions=True)


def after_install():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	_sync_primary_workspace_fixtures()
	_sync_time_tracking_sidebar()
	backfill_time_tracking_role_hierarchy()


def after_migrate():
	from time_tracking.role_hierarchy import backfill_time_tracking_role_hierarchy

	_sync_primary_workspace_fixtures()
	_sync_time_tracking_sidebar()
	backfill_time_tracking_role_hierarchy()
