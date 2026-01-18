frappe.ui.form.on("Time Tracking Settings", {
    refresh(frm) {
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
