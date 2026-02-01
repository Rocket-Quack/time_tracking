frappe.query_reports["Service Report"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Time Tracking Project",
		},
		{
			fieldname: "include_child_projects",
			label: __("Include Child Projects"),
			fieldtype: "Check",
			default: 1,
			depends_on: "eval:doc.project",
		},
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: ["Day", "Week", "Month", "Range"].join("\n"),
			default: "Month",
			reqd: 1,
		},
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			depends_on: "eval:doc.period !== 'Range'",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			depends_on: "eval:doc.period === 'Range'",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			depends_on: "eval:doc.period === 'Range'",
			reqd: 1,
		},
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
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
