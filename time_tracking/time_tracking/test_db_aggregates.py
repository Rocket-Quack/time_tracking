import frappe
from frappe.tests.utils import FrappeTestCase

from time_tracking.time_tracking.db_aggregates import max_as, min_as, sum_as


class TestDbAggregates(FrappeTestCase):
	def test_helpers_return_frappe_function_dicts(self):
		self.assertEqual(sum_as("enabled", "total_enabled"), {"SUM": "enabled", "as": "total_enabled"})
		self.assertEqual(min_as("creation", "first_created"), {"MIN": "creation", "as": "first_created"})
		self.assertEqual(max_as("creation", "last_created"), {"MAX": "creation", "as": "last_created"})

	def test_helpers_work_with_get_all_fields(self):
		rows = frappe.get_all(
			"User",
			filters={"enabled": ["in", [0, 1]]},
			fields=[sum_as("enabled", "total_enabled")],
			limit=1,
		)

		self.assertTrue(rows)
		self.assertTrue(hasattr(rows[0], "total_enabled"))
