frappe.ui.form.on("Time Booking", {
	setup(frm) {
		if (frm.is_new() && !frm.doc.time_tracking_profile) {
			frm.set_value("time_tracking_profile", frappe.session.user);
		}
		if (frm.is_new() && !frm.doc.bill_type) {
			frm.set_value("bill_type", "Billable");
		}
	},
});
