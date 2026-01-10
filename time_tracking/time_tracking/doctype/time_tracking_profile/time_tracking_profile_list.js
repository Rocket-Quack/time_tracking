frappe.listview_settings["Time Tracking Profile"] = {
    onload(listview) {
        if (
            frappe.user.has_role("System Manager") ||
            frappe.user.has_role("Time Tracking Admin")
        ) {
            return;
        }

        frappe.db
            .get_value("Time Tracking Profile", { user: frappe.session.user }, "name")
            .then((r) => {
                const name = r.message && r.message.name;
                if (name) {
                    frappe.set_route("Form", "Time Tracking Profile", name);
                } else {
                    frappe.msgprint(__("Time Tracking Profile is required."));
                }
            });
    },
};
