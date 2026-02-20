import frappe
from frappe import _
from frappe.integrations.utils import make_get_request
from frappe.model.document import Document
from frappe.utils import cint, getdate


class TimeTrackingHolidayList(Document):
	def autoname(self):
		self._apply_expected_name(set_docname=True)

	def validate(self):
		self._set_date_range()
		self._validate_unique_year()
		self._apply_expected_name(set_docname=self.is_new())
		self.holiday_count = self._validate_holidays()

	def _set_date_range(self):
		year = cint(self.year)
		if not year:
			return
		self.from_date = getdate(f"{year}-01-01")
		self.to_date = getdate(f"{year}-12-31")

	def _apply_expected_name(self, set_docname=False):
		year = cint(self.year)
		if not year:
			return
		expected_name = f"{year}-Holiday-List"
		if set_docname:
			self.name = expected_name
		if self.name and self.name != expected_name:
			frappe.throw(_("Holiday List name must be {0}.").format(expected_name))
		self.holiday_list_name = expected_name

	def _validate_unique_year(self):
		year = cint(self.year)
		if not year:
			return
		filters = {"year": year}
		if self.name:
			filters["name"] = ["!=", self.name]
		if frappe.db.exists("Time Tracking Holiday List", filters):
			frappe.throw(_("Holiday List for {0} already exists.").format(year))

	def _validate_holidays(self):
		year = cint(self.year)
		if not year:
			return 0
		seen = set()
		for row in self.holidays or []:
			if not row.holiday_date:
				continue
			holiday_date = getdate(row.holiday_date)
			if holiday_date.year != year:
				frappe.throw(_("Holiday date {0} must be within year {1}.").format(holiday_date, year))
			if holiday_date in seen:
				frappe.throw(_("Holiday date {0} is duplicated.").format(holiday_date))
			seen.add(holiday_date)
		return len(seen)


@frappe.whitelist()
def fetch_open_holidays(country_code, year):
	year = cint(year)
	if not year:
		frappe.throw(_("Year is required."))

	country_code = (country_code or "").upper()
	if not country_code:
		frappe.throw(_("Country is required."))

	valid_from = f"{year}-01-01"
	valid_to = f"{year}-12-31"
	params = {
		"countryIsoCode": country_code,
		"languageIsoCode": "DE",
		"validFrom": valid_from,
		"validTo": valid_to,
	}

	data = make_get_request(
		"https://openholidaysapi.org/PublicHolidays",
		params=params,
	)

	if isinstance(data, dict):
		data = data.get("publicHolidays") or data.get("holidays") or []
	if not isinstance(data, list):
		frappe.throw(_("Unexpected response from holiday provider."))

	holidays_by_date = {}
	for item in data:
		if not isinstance(item, dict):
			continue
		if item.get("nationwide") is False:
			continue
		holiday_date = _extract_holiday_date(item)
		if not holiday_date or holiday_date.year != year:
			continue
		name = _extract_holiday_name(item) or _("Holiday")
		holidays_by_date[holiday_date] = name

	results = [{"date": str(date), "name": name} for date, name in sorted(holidays_by_date.items())]
	return results


@frappe.whitelist()
def get_open_holiday_countries():
	continent_map = _get_continent_map()
	code_to_name = _get_country_code_to_name()
	if not continent_map or not code_to_name:
		frappe.throw(_("No countries available for selection."))

	results = {continent: [] for continent in continent_map.keys()}
	for continent, members in continent_map.items():
		for code in sorted(members):
			if code not in code_to_name:
				continue
			name = _get_localized_country_name(code, code_to_name.get(code, code))
			results[continent].append({"code": code, "name": name})

	for continent in results:
		results[continent] = sorted(results[continent], key=lambda entry: entry["name"])

	return results


_CONTINENT_MAP = None


def _get_continent_map():
	global _CONTINENT_MAP
	if _CONTINENT_MAP is not None:
		return _CONTINENT_MAP

	_CONTINENT_MAP = {
		"Europe": {
			"AD",
			"AL",
			"AT",
			"AX",
			"BA",
			"BE",
			"BG",
			"BY",
			"CH",
			"CY",
			"CZ",
			"DE",
			"DK",
			"EE",
			"ES",
			"FI",
			"FO",
			"FR",
			"GB",
			"GG",
			"GI",
			"GR",
			"HR",
			"HU",
			"IE",
			"IM",
			"IS",
			"IT",
			"JE",
			"LI",
			"LT",
			"LU",
			"LV",
			"MC",
			"MD",
			"ME",
			"MK",
			"MT",
			"NL",
			"NO",
			"PL",
			"PT",
			"RO",
			"RS",
			"RU",
			"SE",
			"SI",
			"SJ",
			"SK",
			"SM",
			"TR",
			"UA",
			"VA",
			"XK",
		},
		"Americas": {
			"AG",
			"AI",
			"AR",
			"AW",
			"BB",
			"BL",
			"BM",
			"BO",
			"BQ",
			"BR",
			"BS",
			"BZ",
			"CA",
			"CL",
			"CO",
			"CR",
			"CU",
			"CW",
			"DM",
			"DO",
			"EC",
			"FK",
			"GD",
			"GF",
			"GL",
			"GP",
			"GS",
			"GT",
			"GY",
			"HN",
			"HT",
			"JM",
			"KN",
			"KY",
			"LC",
			"MF",
			"MQ",
			"MS",
			"MX",
			"NI",
			"PA",
			"PE",
			"PM",
			"PR",
			"PY",
			"SR",
			"SV",
			"SX",
			"TC",
			"TT",
			"US",
			"UY",
			"VC",
			"VE",
			"VG",
			"VI",
		},
		"Asia": {
			"AE",
			"AF",
			"AM",
			"AZ",
			"BD",
			"BH",
			"BN",
			"BT",
			"CN",
			"GE",
			"HK",
			"ID",
			"IL",
			"IN",
			"IQ",
			"IR",
			"JO",
			"JP",
			"KG",
			"KH",
			"KP",
			"KR",
			"KW",
			"KZ",
			"LA",
			"LB",
			"LK",
			"MM",
			"MN",
			"MO",
			"MV",
			"MY",
			"NP",
			"OM",
			"PH",
			"PK",
			"PS",
			"QA",
			"SA",
			"SG",
			"SY",
			"TH",
			"TJ",
			"TL",
			"TW",
			"UZ",
			"VN",
			"YE",
		},
		"Africa": {
			"AO",
			"BF",
			"BI",
			"BJ",
			"BW",
			"CD",
			"CF",
			"CG",
			"CI",
			"CM",
			"CV",
			"DJ",
			"DZ",
			"EG",
			"EH",
			"ER",
			"ET",
			"GA",
			"GH",
			"GM",
			"GN",
			"GQ",
			"GW",
			"IO",
			"KE",
			"KM",
			"LR",
			"LS",
			"LY",
			"MA",
			"MG",
			"ML",
			"MR",
			"MU",
			"MW",
			"MZ",
			"NA",
			"NE",
			"NG",
			"RE",
			"RW",
			"SC",
			"SD",
			"SH",
			"SL",
			"SN",
			"SO",
			"SS",
			"ST",
			"SZ",
			"TD",
			"TG",
			"TN",
			"TZ",
			"UG",
			"YT",
			"ZA",
			"ZM",
			"ZW",
		},
		"Oceania": {
			"AS",
			"AU",
			"CC",
			"CK",
			"CX",
			"FJ",
			"FM",
			"GU",
			"KI",
			"MH",
			"MP",
			"NC",
			"NF",
			"NR",
			"NU",
			"NZ",
			"PF",
			"PG",
			"PN",
			"PW",
			"SB",
			"TK",
			"TO",
			"TV",
			"UM",
			"VU",
			"WF",
			"WS",
		},
	}
	return _CONTINENT_MAP


def _get_country_code_to_name():
	try:
		from frappe.geo.country_info import get_all as get_country_info
	except Exception:
		return {}

	data = get_country_info() or {}
	code_to_name = {}
	for name, info in data.items():
		if not isinstance(info, dict):
			continue
		code = (info.get("code") or "").upper()
		if not code:
			continue
		code_to_name[code] = name
	return code_to_name


def _get_localized_country_name(code, fallback):
	try:
		from babel.core import Locale
	except Exception:
		return fallback

	lang = frappe.local.lang or frappe.get_lang()
	try:
		locale = Locale.parse(lang)
	except Exception:
		locale = Locale.parse("en")
	return locale.territories.get(code, fallback)


def _extract_holiday_date(item):
	for key in ("startDate", "date", "start_date"):
		value = item.get(key)
		if value:
			return getdate(value)
	if isinstance(item.get("startDate"), dict):
		value = item.get("startDate", {}).get("date")
		if value:
			return getdate(value)
	return None


def _extract_holiday_name(item):
	name = item.get("name")
	if isinstance(name, list):
		for entry in name:
			if not isinstance(entry, dict):
				continue
			language = (entry.get("language") or entry.get("languageIsoCode") or "").lower()
			if language in {"de", "de-de", "de-at"}:
				return entry.get("text") or entry.get("name")
		if name:
			entry = name[0]
			if isinstance(entry, dict):
				return entry.get("text") or entry.get("name")
	elif isinstance(name, dict):
		return name.get("text") or name.get("name")
	elif isinstance(name, str):
		return name

	for key in ("localName", "englishName", "shortName"):
		value = item.get(key)
		if value:
			return value
	return None
