frappe.ui.form.on("Time Tracking Profile", {
    setup(frm) {
        if (frm.fields_dict.project_assignments) {
            frm.fields_dict.project_assignments.grid.get_field("project").get_query = function () {
                return {
                    filters: {
                        is_group: 0,
                    },
                };
            };
        }
    },
});
