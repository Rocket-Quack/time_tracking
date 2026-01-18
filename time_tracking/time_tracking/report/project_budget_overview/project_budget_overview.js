frappe.query_reports["Project Budget Overview"] = {
    filters: [
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: ["All", "Over Budget", "On Budget", "Under Budget", "No Budget"].join(
                "\n"
            ),
            default: "All",
        },
        {
            fieldname: "include_groups",
            label: __("Include Group Projects"),
            fieldtype: "Check",
            default: 0,
        },
        {
            fieldname: "internal_filter",
            label: __("Internal Projects"),
            fieldtype: "Select",
            options: ["All", "Only Internal", "Exclude Internal"].join("\n"),
            default: "All",
        },
    ],
};
