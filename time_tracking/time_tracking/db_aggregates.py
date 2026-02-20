"""Helpers for Frappe aggregate field dictionaries.

Frappe no longer allows SQL functions as raw strings in `fields`, e.g.
`"sum(duration_minutes) as total"`. Use these helpers to build the
allowed dict syntax consistently across the codebase.
"""


def aggregate_as(function_name, fieldname, alias):
	return {function_name.upper(): fieldname, "as": alias}


def sum_as(fieldname, alias):
	return aggregate_as("SUM", fieldname, alias)


def min_as(fieldname, alias):
	return aggregate_as("MIN", fieldname, alias)


def max_as(fieldname, alias):
	return aggregate_as("MAX", fieldname, alias)


def count_as(fieldname, alias):
	return aggregate_as("COUNT", fieldname, alias)
