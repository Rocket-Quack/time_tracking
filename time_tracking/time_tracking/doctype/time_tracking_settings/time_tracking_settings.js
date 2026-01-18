frappe.ui.form.on("Time Tracking Settings", {
    refresh(frm) {
        const helpContent = {
            booking_help_html: {
                title: __("Booking Rules"),
                body: [
                    __(
                        "Controls time entry and validation (date format, rounding increment)."
                    ),
                    __(
                        "Example: Use a 15-minute increment to align all bookings to quarter-hour slots."
                    ),
                ].join(" "),
            },
            team_help_html: {
                title: __("Project Access"),
                body: [
                    __(
                        "Defines who can assign projects to profiles and manage access."
                    ),
                    __(
                        "Example: Enable assignment restriction so only admins can add projects."
                    ),
                ].join(" "),
            },
            billing_help_html: {
                title: __("Billing Rates"),
                body: [
                    __(
                        "Rates determine the budget amount calculations on projects."
                    ),
                    __(
                        "Example: Choose Role-based rates to use the highest rate from the user's roles."
                    ),
                ].join(" "),
            },
            targets_help_html: {
                title: __("Targets"),
                body: [
                    __(
                        "Target hours influence overtime calculations and forecasting."
                    ),
                    __(
                        "Example: Set Weekly = 40h to calculate overtime each week."
                    ),
                ].join(" "),
            },
            overtime_help_html: {
                title: __("Overtime"),
                body: [
                    __(
                        "Calculated per period; year-end rules define carryover, cap, or reset."
                    ),
                    __(
                        "Example: Cap at 10h keeps only 10 hours when a year closes."
                    ),
                ].join(" "),
            },
            vacation_help_html: {
                title: __("Vacation"),
                body: [
                    __(
                        "Vacation project, workdays per week, and year-end rules define balances."
                    ),
                    __(
                        "Example: Carryover keeps unused days into the next year."
                    ),
                ].join(" "),
            },
            holiday_help_html: {
                title: __("Holidays"),
                body: [
                    __(
                        "Holiday lists are used for monthly calculations and overtime."
                    ),
                    __(
                        "Example: Holidays count as planned hours in monthly totals."
                    ),
                ].join(" "),
            },
            sickness_help_html: {
                title: __("Sickness"),
                body: [
                    __(
                        "Sickness bookings can optionally be included in overtime."
                    ),
                    __(
                        "Example: Enable to avoid negative overtime during sick leave."
                    ),
                ].join(" "),
            },
            notifications_help_html: {
                title: __("Booking Reminders"),
                body: (() => {
                    const triggerItems = [
                        __(
                            "Month End: Remind on the last day of the month if any workdays are missing."
                        ),
                        __(
                            "Monthly: Remind on the configured day of the month (e.g. 25)."
                        ),
                        __(
                            "Weekly: Remind on the selected weekday for the current week."
                        ),
                        __(
                            "Inactivity: Remind after X days without any booking."
                        ),
                        __(
                            "Missing Days Threshold: Remind when missing booking days reach a threshold."
                        ),
                    ];
                    const examples = [
                        __(
                            "Example A: Trigger = Month End, user has 2 missing workdays -> email is sent on the last day."
                        ),
                        __(
                            "Example B: Trigger = Weekly (Friday), missing days in this week -> email on Friday."
                        ),
                        __(
                            "Example C: Trigger = Inactivity (5), no bookings for 5 days -> email on day 5."
                        ),
                    ];
                    const listItems = triggerItems
                        .map((item) => `<li>${item}</li>`)
                        .join("");
                    const exampleItems = examples
                        .map((item) => `<li>${item}</li>`)
                        .join("");

                    return [
                        __(
                            "Reminders are sent when bookings are missing based on the selected trigger."
                        ),
                        `<br><span class="text-muted">${__(
                            "Trigger options:"
                        )}</span>`,
                        `<ul class="mb-2">${listItems}</ul>`,
                        `<span class="text-muted">${__(
                            "Examples"
                        )}:</span>`,
                        `<ul class="mb-0">${exampleItems}</ul>`,
                    ].join("");
                })(),
            },
        };

        Object.keys(helpContent).forEach((fieldname) => {
            const entry = helpContent[fieldname];
            if (!entry) {
                return;
            }
            const html = `<div class="small text-muted"><p><strong>${entry.title}</strong><br>${entry.body}</p></div>`;
            frm.set_df_property(fieldname, "options", html);
        });

        if (
            !frappe.user.has_role("System Manager") &&
            !frappe.user.has_role("Time Tracking Admin")
        ) {
            return;
        }

        frm.add_custom_button(
            __("Recalculate Ledgers"),
            () => {
                const dialog = new frappe.ui.Dialog({
                    title: __("Recalculate Ledgers"),
                    fields: [
                        {
                            fieldtype: "Section Break",
                            label: __("Scope"),
                        },
                        {
                            fieldname: "profile_name",
                            fieldtype: "Link",
                            label: __("Profile"),
                            options: "Time Tracking Profile",
                            description: __(
                                "Leave empty to include all profiles."
                            ),
                        },
                        {
                            fieldtype: "Section Break",
                            label: __("Overtime"),
                        },
                        {
                            fieldname: "start_date",
                            fieldtype: "Date",
                            label: __("Start Date"),
                            description: __(
                                "Leave empty to use the first booking date."
                            ),
                        },
                        {
                            fieldname: "end_date",
                            fieldtype: "Date",
                            label: __("End Date"),
                            description: __(
                                "Leave empty to use the last booking date."
                            ),
                        },
                        {
                            fieldtype: "Section Break",
                            label: __("Vacation"),
                        },
                        {
                            fieldname: "start_year",
                            fieldtype: "Int",
                            label: __("Start Year"),
                            default: moment().year(),
                        },
                        {
                            fieldname: "end_year",
                            fieldtype: "Int",
                            label: __("End Year"),
                            default: moment().year(),
                        },
                    ],
                    primary_action_label: __("Recalculate"),
                    primary_action(values) {
                        if (!values) {
                            return;
                        }
                        frappe.call({
                            method:
                                "time_tracking.time_tracking.overtime_utils.recalculate_time_tracking_ledgers",
                            args: values,
                            freeze: true,
                            freeze_message: __(
                                "Recalculating ledgers..."
                            ),
                        }).then((result) => {
                            const data = result.message || {};
                            const overtime = data.overtime || {};
                            const vacation = data.vacation || {};
                            const message = [
                                __(
                                    "Overtime: {0} profiles, {1} period entries updated, {2} period entries deleted.",
                                    [
                                        overtime.profiles_processed || 0,
                                        overtime.period_entries_updated || 0,
                                        overtime.period_entries_deleted || 0,
                                    ]
                                ),
                                __(
                                    "Vacation: {0} profiles, {1} carryover entries updated, {2} carryover entries deleted.",
                                    [
                                        vacation.profiles_processed || 0,
                                        vacation.carryover_entries_updated || 0,
                                        vacation.carryover_entries_deleted || 0,
                                    ]
                                ),
                            ].join("<br>");

                            frappe.msgprint({
                                title: __("Recalculate Ledgers"),
                                message,
                                indicator: "green",
                            });
                            dialog.hide();
                        });
                    },
                });
                dialog.show();
            },
            __("Actions")
        );
    },
});
