import frappe
from frappe.utils import add_days, formatdate, getdate


def _get_week_range(start_year, end_year):
	start_date = getdate(f"{start_year}-01-01")
	end_date = getdate(f"{end_year}-12-31")

	start_monday = add_days(start_date, -start_date.weekday())
	end_monday = add_days(end_date, -end_date.weekday())

	current = start_monday
	week_starts = []
	while current <= end_monday:
		week_starts.append(current)
		current = add_days(current, 7)

	return week_starts


def _build_week_fields(week_start_date):
	week_end_date = add_days(week_start_date, 6)
	iso_year, calendar_week, _ = week_start_date.isocalendar()
	period_label = (
		f"{formatdate(week_start_date, 'dd.MM.yyyy')} - "
		f"{formatdate(week_end_date, 'dd.MM.yyyy')}"
	)

	return {
		"week_end_date": week_end_date,
		"calendar_week": calendar_week,
		"calendar_year": iso_year,
		"period_label": period_label,
	}


def ensure_weekly_booking_documents():
	"""Create weekly booking docs for the current and next year for all profiles."""
	today = getdate()
	start_year = today.year
	end_year = today.year + 1

	week_starts = _get_week_range(start_year, end_year)
	if not week_starts:
		return

	profiles = frappe.get_all(
		"Time Tracking Profile",
		fields=["user"],
		filters={"user": ["!=", ""]},
	)

	if not profiles:
		return

	range_start = week_starts[0].strftime("%Y-%m-%d")
	range_end = add_days(week_starts[-1], 6).strftime("%Y-%m-%d")

	for profile in profiles:
		user = profile.user
		if not user:
			continue

		existing = set(
			frappe.get_all(
				"Weekly Booking Data",
				filters={
					"user": user,
					"week_start_date": ["between", [range_start, range_end]],
				},
				pluck="week_start_date",
			)
		)

		for week_start in week_starts:
			week_start_str = week_start.strftime("%Y-%m-%d")
			if week_start_str in existing:
				continue

			doc = frappe.new_doc("Weekly Booking Data")
			doc.update(
				{
					"user": user,
					"week_start_date": week_start,
					**_build_week_fields(week_start),
				}
			)
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
