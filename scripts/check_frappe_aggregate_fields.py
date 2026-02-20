#!/usr/bin/env python3
"""Fail on SQL function strings in Frappe `fields=[...]` clauses.

This guards against hardcoded patterns like:
`fields=["sum(duration_minutes) as total"]`
and keeps aggregate usage centralized via helper wrappers.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

AGGREGATE_FUNCTION_PATTERN = re.compile(r"\b(sum|min|max|count|avg)\s*\(", re.IGNORECASE)
TARGET_METHODS = {"get_all", "get_list"}


def _is_target_call(call: ast.Call) -> bool:
	func = call.func
	return isinstance(func, ast.Attribute) and func.attr in TARGET_METHODS


def _extract_string_value(node: ast.AST) -> str | None:
	if isinstance(node, ast.Constant) and isinstance(node.value, str):
		return node.value
	if isinstance(node, ast.JoinedStr):
		parts = []
		for value in node.values:
			if isinstance(value, ast.Constant) and isinstance(value.value, str):
				parts.append(value.value)
			else:
				parts.append("{...}")
		return "".join(parts)
	return None


def _iter_fields_literals(fields_node: ast.AST):
	if isinstance(fields_node, (ast.List, ast.Tuple)):
		for item in fields_node.elts:
			text = _extract_string_value(item)
			if text is not None:
				yield item, text
	elif isinstance(fields_node, (ast.Constant, ast.JoinedStr)):
		text = _extract_string_value(fields_node)
		if text is not None:
			yield fields_node, text


def _scan_file(path: Path) -> list[tuple[int, str]]:
	content = path.read_text(encoding="utf-8")
	tree = ast.parse(content, filename=str(path))
	violations = []

	for node in ast.walk(tree):
		if not isinstance(node, ast.Call) or not _is_target_call(node):
			continue
		for keyword in node.keywords or []:
			if keyword.arg != "fields":
				continue
			for item, text in _iter_fields_literals(keyword.value):
				if AGGREGATE_FUNCTION_PATTERN.search(text):
					violations.append((item.lineno, text.strip()))
	return violations


def _collect_files(args: list[str]) -> list[Path]:
	if args:
		return [Path(arg) for arg in args if arg.endswith(".py")]
	return sorted(Path("time_tracking").rglob("*.py"))


def main(argv: list[str]) -> int:
	python_files = [p for p in _collect_files(argv[1:]) if "__pycache__" not in str(p)]
	if not python_files:
		return 0

	errors = []
	for file_path in python_files:
		if not file_path.exists():
			continue
		try:
			violations = _scan_file(file_path)
		except SyntaxError:
			continue
		for line, text in violations:
			errors.append(
				f"{file_path}:{line}: SQL function string in `fields` is disallowed: {text}"
			)

	if errors:
		print("Found unsupported SQL function string literals in Frappe `fields` clauses:")
		for error in errors:
			print(f"  - {error}")
		print("Use helper wrappers instead, e.g. sum_as('duration_minutes', 'total').")
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv))
