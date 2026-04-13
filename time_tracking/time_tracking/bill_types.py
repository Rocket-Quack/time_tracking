from frappe import _

BILL_TYPE_BILLABLE = "Billable"
BILL_TYPE_UNBILLABLE = "Unbillable"
BILL_TYPES = {BILL_TYPE_BILLABLE, BILL_TYPE_UNBILLABLE}


def normalize_bill_type(value):
	if value == BILL_TYPE_UNBILLABLE:
		return BILL_TYPE_UNBILLABLE
	return BILL_TYPE_BILLABLE


def get_bill_type_options():
	return "\n".join([BILL_TYPE_BILLABLE, BILL_TYPE_UNBILLABLE])


def get_bill_type_label(value):
	return _(normalize_bill_type(value))
