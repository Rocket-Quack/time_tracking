frappe.query_reports["Project Budget Overview"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["All", "Over Budget", "On Budget", "Under Budget", "No Budget"].join("\n"),
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
	formatter: function (value, row, column, data, default_formatter) {
		if (column.fieldname === "project" && data && data.project) {
			const label = data.project_label || data.project_name || data.project;
			return frappe.utils.get_form_link(
				"Time Tracking Project",
				data.project,
				true,
				frappe.utils.escape_html(String(label))
			);
		}
		return default_formatter(value, row, column, data);
	},
};
