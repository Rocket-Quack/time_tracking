#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Complete Frappe setup wizard for a site (idempotent).

Usage:
  scripts/complete_setup_wizard.sh [options]

Options:
  --site <name>        Site name (default: test_site)
  --bench-root <path>  Bench root path (default: current directory)
  -h, --help           Show this help
EOF
}

SITE_NAME="test_site"
BENCH_ROOT="$(pwd)"

while [[ $# -gt 0 ]]; do
	case "$1" in
		--site)
			SITE_NAME="$2"
			shift 2
			;;
		--bench-root)
			BENCH_ROOT="$2"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
	esac
done

if [[ ! -d "${BENCH_ROOT}/sites" ]] || [[ ! -d "${BENCH_ROOT}/apps" ]]; then
	echo "Bench root not valid: ${BENCH_ROOT}" >&2
	echo "Hint: pass --bench-root <path-to-frappe-bench>" >&2
	exit 1
fi

if [[ ! -d "${BENCH_ROOT}/sites/${SITE_NAME}" ]]; then
	echo "Site does not exist: ${SITE_NAME}" >&2
	exit 1
fi

cd "${BENCH_ROOT}"

echo "Completing setup wizard for site: ${SITE_NAME}"
bench --site "${SITE_NAME}" execute frappe.utils.install.complete_setup_wizard
bench --site "${SITE_NAME}" clear-cache

echo "Setup wizard completion done for ${SITE_NAME}"
