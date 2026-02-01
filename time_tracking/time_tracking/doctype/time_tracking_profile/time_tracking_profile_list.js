function isTimeTrackingAdmin() {
	return frappe.user.has_role("System Manager") || frappe.user.has_role("Time Tracking Admin");
}

function showProfileMissingDialog() {
	const message = __("Time Tracking Profile is required.");
	const isAdmin = isTimeTrackingAdmin();
	const dialog = new frappe.ui.Dialog({
		title: __("Time Tracking Profile Required"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<p class="mb-0">${frappe.utils.escape_html(message)}</p>`,
			},
		],
		primary_action_label: isAdmin ? __("Create Time Tracking Profile") : __("Close"),
		primary_action: function () {
			dialog.hide();
			if (isAdmin) {
				frappe.route_options = { user: frappe.session.user };
				frappe.new_doc("Time Tracking Profile");
			}
		},
	});

	dialog.show();
}

frappe.listview_settings["Time Tracking Profile"] = {
	onload(listview) {
		if (isTimeTrackingAdmin()) {
			return;
		}

		frappe.db
			.get_value("Time Tracking Profile", { user: frappe.session.user }, "name")
			.then((r) => {
				const name = r.message && r.message.name;
				if (name) {
					frappe.set_route("Form", "Time Tracking Profile", name);
				} else {
					showProfileMissingDialog();
				}
			});
	},
};
