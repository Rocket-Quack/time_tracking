function addTimeTrackingProfileLink(frm, profileName) {
	if (frm.__time_tracking_profile_link_added) {
		return;
	}

	frm.add_custom_button(
		__("Open Time Tracking Profile"),
		() => {
			frappe.set_route("Form", "Time Tracking Profile", profileName);
		},
		__("Links")
	);
	frm.__time_tracking_profile_link_added = true;
}

frappe.ui.form.on("User", {
	refresh(frm) {
		frm.__time_tracking_profile_link_added = false;
		if (frm.is_new() || !frm.doc.name) {
			return;
		}

		frappe.db.get_value("Time Tracking Profile", { user: frm.doc.name }, "name").then((r) => {
			const profileName = r && r.message && r.message.name;
			if (profileName) {
				addTimeTrackingProfileLink(frm, profileName);
			}
		});
	},
});
