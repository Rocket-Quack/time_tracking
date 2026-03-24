"""Helpers for Frappe aggregate field expressions.

Frappe v16 no longer accepts SQL function strings like
``sum(duration_minutes) as total`` in ``fields=[...]``. These helpers
return the dict form expected by the query engine instead.
"""


def aggregate_as(function_name, fieldname, alias):
	fn = (function_name or "").strip().lower()
	field = (fieldname or "").strip()
	as_alias = (alias or "").strip()
	if not fn or not field or not as_alias:
		raise ValueError("aggregate_as requires function_name, fieldname and alias")
	return {fn.upper(): field, "as": as_alias}


def sum_as(fieldname, alias):
	return aggregate_as("SUM", fieldname, alias)


def min_as(fieldname, alias):
	return aggregate_as("MIN", fieldname, alias)


def max_as(fieldname, alias):
	return aggregate_as("MAX", fieldname, alias)


def count_as(fieldname, alias):
	return aggregate_as("COUNT", fieldname, alias)
