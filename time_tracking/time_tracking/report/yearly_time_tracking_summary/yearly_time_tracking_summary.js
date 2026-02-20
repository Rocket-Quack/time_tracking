frappe.query_reports["Yearly Time Tracking Summary"] = {
	filters: (() => {
		const filters = [
			{
				fieldname: "year",
				label: __("Year"),
				fieldtype: "Int",
				default: moment().year(),
				reqd: 1,
			},
		];

		const isAdmin =
			frappe.user.has_role("System Manager") || frappe.user.has_role("Time Tracking Admin");

		if (isAdmin) {
			filters.push({
				fieldname: "user",
				label: __("User"),
				fieldtype: "Link",
				options: "User",
			});
		}

		return filters;
	})(),
};
