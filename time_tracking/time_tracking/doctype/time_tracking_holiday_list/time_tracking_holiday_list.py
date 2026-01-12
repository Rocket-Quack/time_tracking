import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate


class TimeTrackingHolidayList(Document):
    def autoname(self):
        self._apply_expected_name(set_docname=True)

    def validate(self):
        self._set_date_range()
        self._validate_unique_year()
        self._apply_expected_name(set_docname=self.is_new())
        self._validate_holidays()

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
            return
        seen = set()
        for row in self.holidays or []:
            if not row.holiday_date:
                continue
            holiday_date = getdate(row.holiday_date)
            if holiday_date.year != year:
                frappe.throw(
                    _("Holiday date {0} must be within year {1}.").format(
                        holiday_date, year
                    )
                )
            if holiday_date in seen:
                frappe.throw(_("Holiday date {0} is duplicated.").format(holiday_date))
            seen.add(holiday_date)
