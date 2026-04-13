import frappe


def execute():
	frappe.db.sql(
		"""
		update `tabTime Booking`
		set bill_type = 'Billable'
		where ifnull(bill_type, '') = ''
		"""
	)
