import calendar

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

WEEKS_PER_MONTH = 52 / 12
HOLIDAY_LIST_SUFFIX = "Holiday-List"

ENTRY_TYPE_OPENING = "Opening Balance"
ENTRY_TYPE_YEAR_END = "Year End Carryover"


def get_vacation_project():
    return frappe.db.get_single_value("Time Tracking Settings", "vacation_booking_project")


def get_sickness_project():
    return frappe.db.get_single_value("Time Tracking Settings", "sickness_booking_project")


def get_holidays_enabled():
    return cint(
        frappe.db.get_single_value("Time Tracking Settings", "enable_holiday_list")
        or 0
    )


def get_allow_negative_vacation_balance():
    return cint(
        frappe.db.get_single_value(
            "Time Tracking Settings", "allow_negative_vacation_balance"
        )
        or 0
    )


def get_default_workdays_per_week():
    value = flt(
        frappe.db.get_single_value("Time Tracking Settings", "default_workdays_per_week")
        or 0
    )
    return value if value > 0 else 5


def _get_vacation_year_end_policy():
    return (
        frappe.db.get_single_value("Time Tracking Settings", "vacation_year_end_policy")
        or "Cap"
    )


def _get_vacation_carryover_limit():
    return flt(
        frappe.db.get_single_value(
            "Time Tracking Settings", "vacation_carryover_limit_days"
        )
        or 0
    )

def _get_opening_balance_days_for_year(profile, year):
    if not profile or not year:
        return 0

    start_date = getdate(f"{cint(year)}-01-01")
    end_date = getdate(f"{cint(year)}-12-31")
    totals = frappe.get_all(
        "Time Tracking Vacation Ledger",
        filters={
            "user": profile.user,
            "entry_type": ENTRY_TYPE_OPENING,
            "period_start": ["between", [start_date, end_date]],
        },
        fields=["sum(delta_days) as total"],
    )
    if totals and totals[0].total is not None:
        return flt(totals[0].total)
    return 0


def _compute_vacation_carryover_days(profile, year):
    if not profile or not year:
        return 0

    hours_per_day = get_hours_per_vacation_day(profile)
    if hours_per_day <= 0:
        return 0

    policy = _get_vacation_year_end_policy()
    if policy not in ("Carryover", "Cap", "Reset"):
        policy = "Carryover"

    allow_negative = get_allow_negative_vacation_balance()
    year = cint(year)
    previous_year = year - 1
    if previous_year <= 0:
        return 0

    creation_year = getdate(profile.creation or nowdate()).year
    if previous_year < creation_year:
        return 0

    allowance_days = flt(profile.vacation_days_per_year)
    carryover_days = 0
    if previous_year > creation_year:
        carryover_days = get_vacation_carryover_days(profile, previous_year)
    opening_days = _get_opening_balance_days_for_year(profile, previous_year)
    allowance_days += flt(carryover_days) + flt(opening_days)

    used_minutes = get_vacation_used_minutes(
        profile.name, getdate(f"{previous_year}-12-31")
    )
    used_days = used_minutes / (hours_per_day * 60)
    remaining_days = allowance_days - used_days
    if not allow_negative:
        remaining_days = max(remaining_days, 0)

    if policy == "Reset":
        return 0
    if policy == "Cap":
        cap_days = _get_vacation_carryover_limit()
        if remaining_days < 0 and allow_negative:
            return remaining_days
        if cap_days <= 0:
            return 0
        return min(remaining_days, cap_days)

    return remaining_days


def _upsert_vacation_ledger_entry(values):
    filters = {
        "user": values.get("user"),
        "entry_type": values.get("entry_type"),
        "period_start": values.get("period_start"),
    }
    existing_name = frappe.db.get_value(
        "Time Tracking Vacation Ledger", filters, "name"
    )
    if existing_name:
        frappe.db.set_value(
            "Time Tracking Vacation Ledger",
            existing_name,
            values,
            update_modified=True,
        )
        return existing_name

    doc = frappe.new_doc("Time Tracking Vacation Ledger")
    doc.update(values)
    doc.insert(ignore_permissions=True)
    return doc.name


def _sync_vacation_year_end_carryover(profile, year, carryover_days, source=None):
    if not profile or not year:
        return 0

    year = cint(year)
    if year <= 0:
        return 0

    start_date = getdate(f"{year}-01-01")
    filters = {
        "user": profile.user,
        "entry_type": ENTRY_TYPE_YEAR_END,
        "period_start": start_date,
    }
    existing = frappe.db.get_value(
        "Time Tracking Vacation Ledger", filters, ["name", "delta_days"], as_dict=True
    )

    if not carryover_days:
        if existing:
            frappe.db.delete("Time Tracking Vacation Ledger", filters)
        return 0

    if existing and flt(existing.delta_days) == flt(carryover_days):
        return carryover_days

    values = {
        "user": profile.user,
        "time_tracking_profile": profile.name,
        "entry_type": ENTRY_TYPE_YEAR_END,
        "period_start": start_date,
        "delta_days": carryover_days,
        "calculation_source": source or "policy",
        "calculated_on": now_datetime(),
    }
    _upsert_vacation_ledger_entry(values)
    return carryover_days


def get_vacation_carryover_days(profile, year):
    carryover_days = _compute_vacation_carryover_days(profile, year)
    _sync_vacation_year_end_carryover(profile, year, carryover_days, source="policy")
    return carryover_days


def sync_vacation_opening_balance(profile):
    if not profile:
        return None

    opening_days = flt(profile.vacation_opening_balance_days)
    period_start = getdate(profile.creation or nowdate())
    values = {
        "user": profile.user,
        "time_tracking_profile": profile.name,
        "entry_type": ENTRY_TYPE_OPENING,
        "period_start": period_start,
        "delta_days": opening_days,
        "calculation_source": "opening_balance",
        "calculated_on": now_datetime(),
    }
    _upsert_vacation_ledger_entry(values)

    year = period_start.year
    _sync_vacation_year_end_carryover(
        profile,
        year + 1,
        _compute_vacation_carryover_days(profile, year + 1),
        source="opening_balance",
    )
    return opening_days


def get_expected_holiday_list_name(year):
    year = cint(year)
    if not year:
        return None
    return f"{year}-{HOLIDAY_LIST_SUFFIX}"


def get_holiday_list_for_range(start_date, end_date):
    year = getdate(start_date).year
    expected_name = get_expected_holiday_list_name(year)
    if not expected_name:
        return None
    exists = frappe.db.exists(
        "Time Tracking Holiday List",
        {"name": expected_name, "year": year},
    )
    return expected_name if exists else None


def get_holiday_list_for_date(date):
    if not date:
        return None
    booking_date = getdate(date)
    return get_holiday_list_for_range(booking_date, booking_date)


def validate_holiday_list_for_date(date):
    if not get_holidays_enabled():
        return None

    holiday_list = get_holiday_list_for_date(date)
    if not holiday_list:
        year = getdate(date).year
        expected_name = get_expected_holiday_list_name(year)
        frappe.throw(
            _("Holiday List for {0} must be named {1}.").format(year, expected_name)
        )
    return holiday_list


def get_hours_per_vacation_day(profile):
    workdays = flt(profile.workdays_per_week) or get_default_workdays_per_week()
    if not workdays:
        return 0

    if profile.target_period == "Weekly":
        weekly_hours = flt(profile.weekly_target_hours)
    elif profile.target_period == "Monthly":
        weekly_hours = flt(profile.monthly_target_hours) / WEEKS_PER_MONTH
    else:
        weekly_hours = 0

    if weekly_hours <= 0:
        return 0

    return weekly_hours / workdays


def _get_year_range(date):
    booking_date = getdate(date)
    year = booking_date.year
    start = booking_date.replace(month=1, day=1)
    last_day = calendar.monthrange(year, 12)[1]
    end = booking_date.replace(month=12, day=last_day)
    return start, end


def get_vacation_used_minutes(profile_name, date, exclude_booking_name=None):
    vacation_project = get_vacation_project()
    if not vacation_project or not profile_name or not date:
        return 0

    start, end = _get_year_range(date)
    filters = {
        "time_tracking_profile": profile_name,
        "project": vacation_project,
        "date": ["between", [start, end]],
    }
    if exclude_booking_name:
        filters["name"] = ["!=", exclude_booking_name]

    totals = frappe.get_all(
        "Time Booking", filters=filters, fields=["sum(duration_minutes) as total"]
    )
    if totals and totals[0].total is not None:
        return flt(totals[0].total)
    return 0


def get_vacation_balance(profile, date, exclude_booking_name=None):
    vacation_project = get_vacation_project()
    if not vacation_project or not profile or not date:
        return None

    hours_per_day = get_hours_per_vacation_day(profile)
    if hours_per_day <= 0:
        return {
            "enabled": True,
            "valid": False,
        }

    report_year = getdate(date).year
    carryover_days = get_vacation_carryover_days(profile, report_year)
    opening_days = _get_opening_balance_days_for_year(profile, report_year)
    allowance_minutes = (
        flt(profile.vacation_days_per_year)
        + flt(carryover_days)
        + flt(opening_days)
    ) * hours_per_day * 60
    used_minutes = get_vacation_used_minutes(
        profile.name, date, exclude_booking_name=exclude_booking_name
    )
    remaining_minutes = allowance_minutes - used_minutes

    allowance_days = allowance_minutes / (hours_per_day * 60)
    used_days = used_minutes / (hours_per_day * 60)
    remaining_days = remaining_minutes / (hours_per_day * 60)

    return {
        "enabled": True,
        "valid": True,
        "carryover_days": carryover_days,
        "opening_days": opening_days,
        "hours_per_day": hours_per_day,
        "allowance_minutes": allowance_minutes,
        "used_minutes": used_minutes,
        "remaining_minutes": remaining_minutes,
        "allowance_days": allowance_days,
        "used_days": used_days,
        "remaining_days": remaining_days,
    }


def _get_profile(profile_name):
    if not profile_name:
        return None
    return frappe.get_doc("Time Tracking Profile", profile_name)


def handle_vacation_booking_change(doc, method=None):
    if getattr(frappe.flags, "skip_vacation_recalc", False):
        return
    if not doc:
        return
    profile_name = getattr(doc, "time_tracking_profile", None)
    if not profile_name:
        return

    vacation_project = get_vacation_project()
    if not vacation_project:
        return

    years = set()

    def _maybe_add(date_value, project_value):
        if not date_value or project_value != vacation_project:
            return
        year = getdate(date_value).year + 1
        if year > 0:
            years.add(year)

    _maybe_add(getattr(doc, "date", None), getattr(doc, "project", None))

    previous = None
    if hasattr(doc, "get_doc_before_save"):
        previous = doc.get_doc_before_save()
    if previous:
        _maybe_add(getattr(previous, "date", None), getattr(previous, "project", None))

    if not years:
        return

    profile = _get_profile(profile_name)
    if not profile:
        return

    for year in sorted(years):
        carryover_days = _compute_vacation_carryover_days(profile, year)
        _sync_vacation_year_end_carryover(
            profile, year, carryover_days, source="time_booking"
        )


def _get_profiles_for_recalc(profile_name=None):
    if profile_name:
        return [frappe.get_doc("Time Tracking Profile", profile_name)]
    profile_names = frappe.get_all("Time Tracking Profile", pluck="name")
    return [frappe.get_doc("Time Tracking Profile", name) for name in profile_names]


def _is_admin(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


@frappe.whitelist()
def recalculate_vacation_ledger(profile_name=None, start_year=None, end_year=None):
    if not _is_admin():
        frappe.throw(_("Only administrators can recalculate vacation balances."))

    start_year = cint(start_year) if start_year else None
    end_year = cint(end_year) if end_year else None
    current_year = getdate(nowdate()).year

    if not start_year:
        start_year = current_year
    if not end_year:
        end_year = start_year
    if end_year < start_year:
        start_year, end_year = end_year, start_year

    profiles = _get_profiles_for_recalc(profile_name)
    total_updated = 0
    total_deleted = 0

    for profile in profiles:
        sync_vacation_opening_balance(profile)
        for year in range(start_year, end_year + 1):
            carryover_days = _compute_vacation_carryover_days(profile, year)
            before = frappe.db.get_value(
                "Time Tracking Vacation Ledger",
                {
                    "user": profile.user,
                    "entry_type": ENTRY_TYPE_YEAR_END,
                    "period_start": getdate(f"{year}-01-01"),
                },
                "name",
            )
            _sync_vacation_year_end_carryover(
                profile, year, carryover_days, source="recalc_job"
            )
            after = frappe.db.get_value(
                "Time Tracking Vacation Ledger",
                {
                    "user": profile.user,
                    "entry_type": ENTRY_TYPE_YEAR_END,
                    "period_start": getdate(f"{year}-01-01"),
                },
                "name",
            )
            if before and not after:
                total_deleted += 1
            elif after:
                total_updated += 1

    return {
        "profiles_processed": len(profiles),
        "carryover_entries_updated": total_updated,
        "carryover_entries_deleted": total_deleted,
    }
