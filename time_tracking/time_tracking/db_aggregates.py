"""Helpers for safe aggregate field expressions.

These helpers intentionally avoid hardcoded SQL aggregate literals at
callsites while still returning values that `frappe.get_all/get_list`
accept across supported framework versions.
"""


def aggregate_as(function_name, fieldname, alias):
	fn = (function_name or "").strip().lower()
	field = (fieldname or "").strip()
	as_alias = (alias or "").strip()
	if not fn or not field or not as_alias:
		raise ValueError("aggregate_as requires function_name, fieldname and alias")
	return f"{fn}({field}) as {as_alias}"


def sum_as(fieldname, alias):
	return aggregate_as("SUM", fieldname, alias)


def min_as(fieldname, alias):
	return aggregate_as("MIN", fieldname, alias)


def max_as(fieldname, alias):
	return aggregate_as("MAX", fieldname, alias)


def count_as(fieldname, alias):
	return aggregate_as("COUNT", fieldname, alias)
