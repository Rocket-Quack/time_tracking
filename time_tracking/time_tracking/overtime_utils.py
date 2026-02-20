import calendar

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

from time_tracking.time_tracking.db_aggregates import max_as, min_as, sum_as
from time_tracking.time_tracking.vacation_utils import (
    WEEKS_PER_MONTH,
    get_expected_holiday_list_name,
    get_holidays_enabled,
    get_hours_per_vacation_day,
    get_sickness_project,
    get_vacation_project,
)

ENTRY_TYPE_PERIOD = "Period"
ENTRY_TYPE_OPENING = "Opening Balance"
ENTRY_TYPE_YEAR_END = "Year End Adjustment"

PERIOD_WEEKLY = "Weekly"
PERIOD_MONTHLY = "Monthly"

YEAR_END_POLICY_CARRYOVER = "Carryover"
YEAR_END_POLICY_CAP = "Cap"
YEAR_END_POLICY_RESET = "Reset"


def _get_settings():
    return frappe.get_cached_doc("Time Tracking Settings")


def _resolve_period_type(profile, settings):
    period = (settings.overtime_calculation_period or PERIOD_WEEKLY).strip()
    if period not in (PERIOD_WEEKLY, PERIOD_MONTHLY):
        period = PERIOD_WEEKLY

    if cint(settings.allow_target_period_override):
        target_period = (profile.target_period or "").strip()
        if target_period in (PERIOD_WEEKLY, PERIOD_MONTHLY):
            period = target_period

    return period


def _get_year_end_policy(settings):
    policy = (settings.overtime_year_end_policy or YEAR_END_POLICY_CAP).strip()
    if policy not in (YEAR_END_POLICY_CARRYOVER, YEAR_END_POLICY_CAP, YEAR_END_POLICY_RESET):
        return YEAR_END_POLICY_CAP
    return policy


def _get_week_range(date):
    start = getdate(date)
    start = add_days(start, -start.weekday())
    end = add_days(start, 6)
    return start, end


def _get_month_range(date):
    current = getdate(date)
    start = current.replace(day=1)
    last_day = calendar.monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day)
    return start, end


def _get_period_range(period_type, date):
    if period_type == PERIOD_MONTHLY:
        return _get_month_range(date)
    return _get_week_range(date)


def _get_target_hours(profile, period_type):
    if period_type == PERIOD_WEEKLY:
        if profile.target_period == PERIOD_WEEKLY:
            return flt(profile.weekly_target_hours)
        return flt(profile.monthly_target_hours) / WEEKS_PER_MONTH

    if profile.target_period == PERIOD_MONTHLY:
        return flt(profile.monthly_target_hours)
    return flt(profile.weekly_target_hours) * WEEKS_PER_MONTH


def _get_time_booking_totals(profile_name, start_date, end_date):
    totals = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        fields=["project", sum_as("duration_minutes", "total_minutes")],
        group_by="project",
    )
    totals_by_project = {}
    total_minutes = 0
    for row in totals:
        minutes = flt(row.total_minutes)
        totals_by_project[row.project] = minutes
        total_minutes += minutes
    return totals_by_project, total_minutes


def _get_ledger_balance_until(user, end_date):
    totals = frappe.get_all(
        "Time Tracking Overtime Ledger",
        filters={
            "user": user,
            "period_start": ["<=", end_date],
        },
        fields=[sum_as("delta_minutes", "total")],
    )
    if totals and totals[0].total is not None:
        return flt(totals[0].total)
    return 0


def get_overtime_carryover_minutes(profile, year, settings=None):
    if not profile or not year:
        return 0

    if not settings:
        settings = _get_settings()

    year = cint(year)
    previous_year = year - 1
    if previous_year <= 0:
        return 0

    allow_negative = cint(settings.allow_negative_overtime_balance)
    end_date = getdate(f"{previous_year}-12-31")
    balance_minutes = _get_ledger_balance_until(profile.user, end_date)
    if not allow_negative:
        balance_minutes = max(balance_minutes, 0)

    policy = _get_year_end_policy(settings)
    if policy == YEAR_END_POLICY_RESET:
        return 0

    if policy == YEAR_END_POLICY_CAP:
        cap_hours = flt(settings.carryover_limit_hours)
        cap_minutes = max(cap_hours * 60, 0)
        if balance_minutes < 0 and allow_negative:
            return balance_minutes
        return min(balance_minutes, cap_minutes)

    return balance_minutes


def ensure_overtime_year_end_adjustment(profile, year, settings=None):
    if not profile or not year:
        return None

    if not settings:
        settings = _get_settings()

    policy = _get_year_end_policy(settings)
    year = cint(year)
    start_date = getdate(f"{year}-01-01")
    filters = {
        "user": profile.user,
        "entry_type": ENTRY_TYPE_YEAR_END,
        "period_start": start_date,
    }
    existing = frappe.db.get_value("Time Tracking Overtime Ledger", filters, "name")

    if policy == YEAR_END_POLICY_CARRYOVER:
        if existing:
            frappe.db.delete("Time Tracking Overtime Ledger", filters)
        return None

    current_balance = _get_ledger_balance_until(profile.user, getdate(f"{year - 1}-12-31"))
    if not cint(settings.allow_negative_overtime_balance):
        current_balance = max(current_balance, 0)

    carryover_minutes = get_overtime_carryover_minutes(profile, year, settings=settings)
    adjustment_minutes = int(round(carryover_minutes - current_balance))
    if not adjustment_minutes:
        if existing:
            frappe.db.delete("Time Tracking Overtime Ledger", filters)
        return None

    values = {
        "user": profile.user,
        "time_tracking_profile": profile.name,
        "entry_type": ENTRY_TYPE_YEAR_END,
        "period_type": "",
        "period_start": start_date,
        "period_end": None,
        "target_minutes": 0,
        "actual_minutes": 0,
        "holiday_minutes": 0,
        "vacation_minutes": 0,
        "sickness_minutes": 0,
        "delta_minutes": adjustment_minutes,
        "calculation_source": "year_end_policy",
        "calculated_on": now_datetime(),
    }
    return _upsert_ledger_entry(values)


def _get_booking_minutes_by_date(
    profile_name, start_date, end_date, include_vacation, include_sickness
):
    rows = frappe.get_all(
        "Time Booking",
        filters={
            "time_tracking_profile": profile_name,
            "date": ["between", [start_date, end_date]],
        },
        fields=["date", "project", "duration_minutes"],
    )
    vacation_project = get_vacation_project()
    sickness_project = get_sickness_project()
    minutes_by_date = {}
    for row in rows:
        project = row.project
        if project == vacation_project and not include_vacation:
            continue
        if project == sickness_project and not include_sickness:
            continue
        date_key = str(getdate(row.date))
        minutes_by_date[date_key] = minutes_by_date.get(date_key, 0) + int(
            flt(row.duration_minutes)
        )
    return minutes_by_date


def _get_holiday_dates(start_date, end_date):
    if not get_holidays_enabled():
        return set()

    start = getdate(start_date)
    end = getdate(end_date)
    years = range(start.year, end.year + 1)
    dates = set()

    for year in years:
        expected_name = get_expected_holiday_list_name(year)
        if not expected_name:
            continue

        exists = frappe.db.exists(
            "Time Tracking Holiday List", {"name": expected_name, "year": year}
        )
        if not exists:
            frappe.throw(
                _("Holiday List for {0} must be named {1}.").format(year, expected_name)
            )

        holidays = frappe.get_all(
            "Time Tracking Holiday",
            filters={
                "parent": expected_name,
                "parenttype": "Time Tracking Holiday List",
                "parentfield": "holidays",
                "holiday_date": ["between", [start_date, end_date]],
            },
            fields=["holiday_date"],
        )
        for row in holidays:
            holiday_date = getdate(row.holiday_date)
            if holiday_date.weekday() >= 5:
                continue
            dates.add(holiday_date)

    return dates


def get_holiday_dates_for_range(start_date, end_date):
    return _get_holiday_dates(start_date, end_date)


def calculate_period_overtime(profile, start_date, end_date, period_type, settings):
    totals_by_project, total_minutes = _get_time_booking_totals(
        profile.name, start_date, end_date
    )

    vacation_minutes = flt(totals_by_project.get(get_vacation_project(), 0))
    sickness_minutes = flt(totals_by_project.get(get_sickness_project(), 0))

    actual_minutes = flt(total_minutes)
    if not cint(settings.include_vacation_in_overtime):
        actual_minutes -= vacation_minutes
    if not cint(settings.include_sickness_in_overtime):
        actual_minutes -= sickness_minutes

    hours_per_day = flt(get_hours_per_vacation_day(profile))
    holiday_dates = _get_holiday_dates(start_date, end_date)
    holiday_minutes = len(holiday_dates) * hours_per_day * 60 if hours_per_day > 0 else 0
    actual_minutes += holiday_minutes

    target_minutes = flt(_get_target_hours(profile, period_type) * 60)
    delta_minutes = actual_minutes - target_minutes

    return {
        "target_minutes": int(round(target_minutes)),
        "actual_minutes": int(round(actual_minutes)),
        "holiday_minutes": int(round(holiday_minutes)),
        "vacation_minutes": int(round(vacation_minutes)),
        "sickness_minutes": int(round(sickness_minutes)),
        "delta_minutes": int(round(delta_minutes)),
    }


def _upsert_ledger_entry(values):
    filters = {
        "user": values.get("user"),
        "entry_type": values.get("entry_type"),
        "period_type": values.get("period_type") or "",
        "period_start": values.get("period_start"),
    }
    existing_name = frappe.db.get_value(
        "Time Tracking Overtime Ledger", filters, "name"
    )
    if existing_name:
        frappe.db.set_value(
            "Time Tracking Overtime Ledger",
            existing_name,
            values,
            update_modified=True,
        )
        return existing_name

    doc = frappe.new_doc("Time Tracking Overtime Ledger")
    doc.update(values)
    doc.insert(ignore_permissions=True)
    return doc.name


def _get_profile(user):
    profile_name = frappe.db.get_value("Time Tracking Profile", {"user": user}, "name")
    if not profile_name:
        return None
    return frappe.get_doc("Time Tracking Profile", profile_name)

def _get_profiles_for_recalc(profile_name=None):
    if profile_name:
        return [frappe.get_doc("Time Tracking Profile", profile_name)]
    profile_names = frappe.get_all("Time Tracking Profile", pluck="name")
    return [frappe.get_doc("Time Tracking Profile", name) for name in profile_names]


def _get_booking_date_range(profile_name):
    if not profile_name:
        return None, None

    rows = frappe.get_all(
        "Time Booking",
        filters={"time_tracking_profile": profile_name},
        fields=[
            min_as("date", "start_date"),
            max_as("date", "end_date"),
        ],
    )
    if not rows or not rows[0].start_date:
        return None, None

    return getdate(rows[0].start_date), getdate(rows[0].end_date)


def _is_admin(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def update_overtime_balance(profile, settings=None):
    if not profile:
        return
    if not settings:
        settings = _get_settings()

    totals = frappe.get_all(
        "Time Tracking Overtime Ledger",
        filters={"user": profile.user},
        fields=[sum_as("delta_minutes", "total")],
    )
    total_minutes = flt(totals[0].total) if totals and totals[0].total is not None else 0

    if not cint(settings.allow_negative_overtime_balance):
        total_minutes = max(total_minutes, 0)

    frappe.db.set_value(
        "Time Tracking Profile",
        profile.name,
        "overtime_balance_hours",
        flt(total_minutes / 60, 2),
        update_modified=False,
    )


def recalculate_overtime_for_date(user, date, source=None):
    profile = _get_profile(user)
    if not profile:
        return None

    settings = _get_settings()
    period_type = _resolve_period_type(profile, settings)
    start_date, end_date = _get_period_range(period_type, date)
    totals = calculate_period_overtime(profile, start_date, end_date, period_type, settings)

    values = {
        "user": profile.user,
        "time_tracking_profile": profile.name,
        "entry_type": ENTRY_TYPE_PERIOD,
        "period_type": period_type,
        "period_start": start_date,
        "period_end": end_date,
        "calculation_source": source or "time_booking",
        "calculated_on": now_datetime(),
        **totals,
    }
    _upsert_ledger_entry(values)
    ensure_overtime_year_end_adjustment(profile, getdate(date).year, settings=settings)
    update_overtime_balance(profile, settings=settings)
    return totals


def sync_opening_balance(profile):
    if not profile:
        return None

    opening_hours = flt(profile.overtime_opening_balance_hours)
    opening_minutes = int(round(opening_hours * 60))
    values = {
        "user": profile.user,
        "time_tracking_profile": profile.name,
        "entry_type": ENTRY_TYPE_OPENING,
        "period_type": "",
        "period_start": getdate(profile.creation or nowdate()),
        "period_end": None,
        "target_minutes": 0,
        "actual_minutes": 0,
        "holiday_minutes": 0,
        "vacation_minutes": 0,
        "sickness_minutes": 0,
        "delta_minutes": opening_minutes,
        "calculation_source": "opening_balance",
        "calculated_on": now_datetime(),
    }
    _upsert_ledger_entry(values)
    update_overtime_balance(profile)
    return opening_minutes


def get_weekly_forecast(profile, week_start_date):
    settings = _get_settings()
    include_vacation = cint(settings.include_vacation_in_overtime)
    include_sickness = cint(settings.include_sickness_in_overtime)

    week_start, week_end = _get_week_range(week_start_date)
    hours_per_day = flt(get_hours_per_vacation_day(profile))
    holiday_dates = _get_holiday_dates(week_start, week_end)

    minutes_by_date = _get_booking_minutes_by_date(
        profile.name, week_start, week_end, include_vacation, include_sickness
    )

    actual_minutes = sum(minutes_by_date.values())
    holiday_minutes = len(holiday_dates) * hours_per_day * 60 if hours_per_day > 0 else 0
    actual_minutes += holiday_minutes

    forecast_minutes = actual_minutes
    current = week_start
    while current <= week_end:
        if current.weekday() < 5:
            date_key = str(current)
            if current in holiday_dates:
                current = add_days(current, 1)
                continue
            if minutes_by_date.get(date_key):
                current = add_days(current, 1)
                continue
            forecast_minutes += hours_per_day * 60
        current = add_days(current, 1)

    return {
        "actual_minutes": int(round(actual_minutes)),
        "forecast_minutes": int(round(forecast_minutes)),
        "holiday_dates": [str(date) for date in sorted(holiday_dates)],
    }


def get_overtime_balance_minutes(user):
    profile = _get_profile(user)
    if not profile:
        return 0
    return int(round(flt(profile.overtime_balance_hours) * 60))


def get_overtime_forecast_balance(user, date=None):
    profile = _get_profile(user)
    if not profile:
        return 0

    settings = _get_settings()
    period_type = _resolve_period_type(profile, settings)
    if not date:
        date = nowdate()
    start_date, end_date = _get_period_range(period_type, date)

    hours_per_day = flt(get_hours_per_vacation_day(profile))
    holiday_dates = _get_holiday_dates(start_date, end_date)
    holiday_minutes = len(holiday_dates) * hours_per_day * 60 if hours_per_day > 0 else 0

    include_vacation = cint(settings.include_vacation_in_overtime)
    include_sickness = cint(settings.include_sickness_in_overtime)
    minutes_by_date = _get_booking_minutes_by_date(
        profile.name, start_date, end_date, include_vacation, include_sickness
    )
    actual_minutes = sum(minutes_by_date.values()) + holiday_minutes

    forecast_minutes = actual_minutes
    current = getdate(date)
    while current <= end_date:
        if current.weekday() < 5:
            date_key = str(current)
            if current in holiday_dates:
                current = add_days(current, 1)
                continue
            if minutes_by_date.get(date_key):
                current = add_days(current, 1)
                continue
            forecast_minutes += hours_per_day * 60
        current = add_days(current, 1)

    target_minutes = flt(_get_target_hours(profile, period_type) * 60)
    forecast_delta = forecast_minutes - target_minutes

    current_entry_delta = 0
    current_entry = frappe.db.get_value(
        "Time Tracking Overtime Ledger",
        {
            "user": profile.user,
            "entry_type": ENTRY_TYPE_PERIOD,
            "period_type": period_type,
            "period_start": start_date,
        },
        "delta_minutes",
    )
    if current_entry is not None:
        current_entry_delta = flt(current_entry)

    totals = frappe.get_all(
        "Time Tracking Overtime Ledger",
        filters={"user": profile.user},
        fields=[sum_as("delta_minutes", "total")],
    )
    balance_minutes = flt(totals[0].total) if totals and totals[0].total is not None else 0
    forecast_balance = balance_minutes - current_entry_delta + forecast_delta

    if not cint(settings.allow_negative_overtime_balance):
        forecast_balance = max(forecast_balance, 0)

    return int(round(forecast_balance))


def handle_time_booking_change(doc, method=None):
    if getattr(frappe.flags, "skip_overtime_recalc", False):
        return
    if not doc or not doc.date:
        return
    profile_name = getattr(doc, "time_tracking_profile", None)
    if not profile_name:
        return
    user = frappe.db.get_value("Time Tracking Profile", profile_name, "user")
    if not user:
        return
    recalculate_overtime_for_date(user, doc.date, source="time_booking")


def _recalculate_overtime_periods(profile, start_date, end_date, settings):
    if not start_date or not end_date:
        return 0, 0

    period_type = _resolve_period_type(profile, settings)
    current = getdate(start_date)
    updated = 0
    deleted = 0

    while current <= end_date:
        period_start, period_end = _get_period_range(period_type, current)
        totals_by_project, total_minutes = _get_time_booking_totals(
            profile.name, period_start, period_end
        )
        totals = calculate_period_overtime(profile, period_start, period_end, period_type, settings)

        filters = {
            "user": profile.user,
            "entry_type": ENTRY_TYPE_PERIOD,
            "period_type": period_type,
            "period_start": period_start,
        }
        if total_minutes or totals.get("holiday_minutes"):
            values = {
                "user": profile.user,
                "time_tracking_profile": profile.name,
                "entry_type": ENTRY_TYPE_PERIOD,
                "period_type": period_type,
                "period_start": period_start,
                "period_end": period_end,
                "calculation_source": "recalc_job",
                "calculated_on": now_datetime(),
                **totals,
            }
            _upsert_ledger_entry(values)
            updated += 1
        else:
            if frappe.db.get_value("Time Tracking Overtime Ledger", filters, "name"):
                frappe.db.delete("Time Tracking Overtime Ledger", filters)
                deleted += 1

        current = add_days(period_end, 1)

    return updated, deleted


@frappe.whitelist()
def recalculate_overtime_ledger(profile_name=None, start_date=None, end_date=None):
    if not _is_admin():
        frappe.throw(_("Only administrators can recalculate overtime balances."))

    settings = _get_settings()
    profiles = _get_profiles_for_recalc(profile_name)
    total_updated = 0
    total_deleted = 0

    for profile in profiles:
        sync_opening_balance(profile)
        booking_start, booking_end = _get_booking_date_range(profile.name)

        range_start = getdate(start_date) if start_date else booking_start
        range_end = getdate(end_date) if end_date else booking_end
        updated, deleted = _recalculate_overtime_periods(
            profile, range_start, range_end, settings
        )
        total_updated += updated
        total_deleted += deleted

        year_start = (range_start or booking_start or getdate(profile.creation or nowdate())).year
        year_end = (range_end or booking_end or getdate(profile.creation or nowdate())).year
        for year in range(year_start, year_end + 2):
            ensure_overtime_year_end_adjustment(profile, year, settings=settings)

        update_overtime_balance(profile, settings=settings)

    return {
        "profiles_processed": len(profiles),
        "period_entries_updated": total_updated,
        "period_entries_deleted": total_deleted,
    }


@frappe.whitelist()
def recalculate_time_tracking_ledgers(
    profile_name=None, start_date=None, end_date=None, start_year=None, end_year=None
):
    if not _is_admin():
        frappe.throw(_("Only administrators can recalculate ledgers."))

    from time_tracking.time_tracking.vacation_utils import recalculate_vacation_ledger

    overtime_result = recalculate_overtime_ledger(
        profile_name=profile_name, start_date=start_date, end_date=end_date
    )
    vacation_result = recalculate_vacation_ledger(
        profile_name=profile_name, start_year=start_year, end_year=end_year
    )
    return {
        "overtime": overtime_result,
        "vacation": vacation_result,
    }
