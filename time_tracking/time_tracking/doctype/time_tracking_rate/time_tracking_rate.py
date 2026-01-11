import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

RATE_TYPE_ROLE = "Role"
RATE_TYPE_USER = "User"
RATE_TYPES = {RATE_TYPE_ROLE, RATE_TYPE_USER}


class TimeTrackingRate(Document):
	def validate(self):
		self._validate_rate_type()
		self._validate_rate_reference()
		self._validate_hourly_rate()
		self._validate_unique_reference()

	def _validate_rate_type(self):
		if self.rate_type not in RATE_TYPES:
			frappe.throw(_("Rate type must be Role or User."))

		settings_rate_type = (
			frappe.db.get_single_value("Time Tracking Settings", "rate_basis") or RATE_TYPE_ROLE
		)
		if settings_rate_type in RATE_TYPES and self.rate_type != settings_rate_type:
			frappe.throw(
				_("Rate type must be {0} based on settings.").format(settings_rate_type)
			)

	def _validate_rate_reference(self):
		if self.rate_type == RATE_TYPE_ROLE:
			if not self.role:
				frappe.throw(_("Role is required for role-based rates."))
			self.user = ""
		elif self.rate_type == RATE_TYPE_USER:
			if not self.user:
				frappe.throw(_("User is required for user-based rates."))
			self.role = ""

	def _validate_hourly_rate(self):
		if flt(self.hourly_rate) <= 0:
			frappe.throw(_("Hourly rate must be greater than 0."))

	def _validate_unique_reference(self):
		filters = {"rate_type": self.rate_type}
		if self.rate_type == RATE_TYPE_ROLE:
			filters["role"] = self.role
		else:
			filters["user"] = self.user

		existing = frappe.db.get_value(
			"Time Tracking Rate",
			{**filters, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			ref = self.role if self.rate_type == RATE_TYPE_ROLE else self.user
			frappe.throw(_("A rate already exists for {0}.").format(ref))
