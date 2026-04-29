import frappe


def execute():
	if not _has_bill_type_column():
		return

	frappe.db.sql(
		"""
		update `tabTime Booking`
		set bill_type = 'Billable'
		where ifnull(bill_type, '') = ''
		"""
	)


def _has_bill_type_column():
	return bool(
		frappe.db.sql(
			"""
			select 1
			from information_schema.columns
			where table_schema = database()
				and table_name = 'tabTime Booking'
				and column_name = 'bill_type'
			limit 1
			"""
		)
	)
