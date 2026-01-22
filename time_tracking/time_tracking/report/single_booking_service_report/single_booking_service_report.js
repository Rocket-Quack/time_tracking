frappe.query_reports["Single Booking Service Report"] = {
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
            label: __("Employee"),
            fieldtype: "Link",
            options: "User",
        },
    ],
    onload: function (report) {
        if (frappe.ui.__single_booking_print_default_patched) {
            return;
        }

        const original = frappe.ui.get_print_settings;
        frappe.ui.get_print_settings = function (
            pdf,
            callback,
            letter_head,
            pick_columns,
            has_filters = false
        ) {
            const dialog = original(pdf, callback, letter_head, pick_columns, has_filters);
            if (
                frappe.query_report &&
                frappe.query_report.report_name === "Single Booking Service Report"
            ) {
                dialog.set_value("report", "Single Booking Service Report");
                dialog.set_value("orientation", "Portrait");
                dialog.set_value("with_letter_head", 0);
                dialog.set_value("letter_head", null);
            }
            return dialog;
        };

        frappe.ui.__single_booking_print_default_patched = true;

        if (report && !report.__single_booking_print_wrapped) {
            const original_print = report.print_report.bind(report);
            report.print_report = function (print_settings) {
                print_settings = print_settings || {};
                print_settings.report = "Single Booking Service Report";
                print_settings.orientation = "Portrait";
                return original_print(print_settings);
            };

            const original_pdf = report.pdf_report.bind(report);
            report.pdf_report = function (print_settings) {
                print_settings = print_settings || {};
                print_settings.report = "Single Booking Service Report";
                print_settings.orientation = "Portrait";
                return original_pdf(print_settings);
            };

            report.__single_booking_print_wrapped = true;
        }
    },
};
