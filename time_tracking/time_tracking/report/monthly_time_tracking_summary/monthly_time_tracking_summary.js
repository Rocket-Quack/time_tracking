frappe.query_reports["Monthly Time Tracking Summary"] = {
    filters: (() => {
        const monthOptions = moment.months();
        const filters = [
            {
                fieldname: "month",
                label: __("Month"),
                fieldtype: "Select",
                options: monthOptions.join("\n"),
                default: monthOptions[moment().month()],
                reqd: 1,
            },
            {
                fieldname: "year",
                label: __("Year"),
                fieldtype: "Int",
                default: moment().year(),
                reqd: 1,
            },
        ];

        const isAdmin =
            frappe.user.has_role("System Manager") ||
            frappe.user.has_role("Time Tracking Admin");

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
