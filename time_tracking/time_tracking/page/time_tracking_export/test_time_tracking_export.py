import frappe
from frappe.tests.utils import FrappeTestCase

from time_tracking.time_tracking.page.time_tracking_export.time_tracking_export import (
	_get_project_names,
)


class TestTimeTrackingExport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def _make_project(self, name, parent=None, is_group=0):
		return (
			frappe.get_doc(
				{
					"doctype": "Time Tracking Project",
					"project_name": name,
					"parent_time_tracking_project": parent,
					"is_group": is_group,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def test_group_project_filter_keeps_group_without_children(self):
		group = self._make_project(f"ExportGroup-{frappe.generate_hash(length=6)}", is_group=1)
		child = self._make_project(
			f"ExportChild-{frappe.generate_hash(length=6)}",
			parent=group,
			is_group=0,
		)

		self.assertEqual(_get_project_names(group, include_children=0), [group])
		self.assertEqual(_get_project_names(group, include_children=1), [group, child])
