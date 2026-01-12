function isTargetAdmin() {
    return (
        frappe.user.has_role("System Manager") || frappe.user.has_role("Time Tracking Admin")
    );
}

function applyRateSettings(frm) {
    if (!frm.fields_dict.hourly_rate) {
        return;
    }

    if (!isTargetAdmin()) {
        frm.set_df_property("hourly_rate", "read_only", true);
        return;
    }

    frappe.db
        .get_single_value("Time Tracking Settings", "allow_profile_rate_override")
        .then((r) => {
            const allowOverride = Number(r) === 1;
            const readOnly = !(allowOverride && isTargetAdmin());
            frm.set_df_property("hourly_rate", "read_only", readOnly);
    });
}

const DEFAULT_WEEKS_PER_MONTH = 52 / 12;
const SETTINGS_DOCTYPE = "Time Tracking Settings";
const TRACK_TARGET_ADJUSTMENTS_FIELD = "track_target_adjustments";
const REQUIRE_PROJECT_ASSIGNMENT_FIELD = "require_project_assignment";

function getTrackTargetAdjustmentsSetting(frm) {
    return frappe.db
        .get_single_value(SETTINGS_DOCTYPE, TRACK_TARGET_ADJUSTMENTS_FIELD)
        .then((value) => {
            return Number(value) === 1;
        });
}

function applyTargetAdjustmentVisibility(frm) {
    if (!frm.fields_dict.target_adjustments) {
        return;
    }

    getTrackTargetAdjustmentsSetting(frm).then((enabled) => {
        frm.set_df_property("target_adjustments_section", "hidden", !enabled);
        frm.set_df_property("target_adjustments", "hidden", !enabled);
        frm.refresh_field("target_adjustments");
    });
}

function getRequireProjectAssignmentSetting() {
    return frappe.db
        .get_single_value(SETTINGS_DOCTYPE, REQUIRE_PROJECT_ASSIGNMENT_FIELD)
        .then((value) => {
            return Number(value) === 1;
        });
}

function applyProjectAssignmentVisibility(frm) {
    if (!frm.fields_dict.project_assignments) {
        return;
    }

    getRequireProjectAssignmentSetting().then((enabled) => {
        const isAdmin = isTargetAdmin();
        const readOnly = enabled && !isAdmin;
        const grid = frm.fields_dict.project_assignments.grid;
        if (grid) {
            grid.cannot_add_rows = readOnly;
            grid.cannot_delete_rows = readOnly;
            grid.only_sortable = readOnly;
            grid.toggle_enable(!readOnly);
        }
        frm.set_df_property("project_assignments", "read_only", readOnly);
        frm.refresh_field("project_assignments");
    });
}

function buildConversionPreviewHtml(baseValue, weeksPerMonth, suggestedValue, targetPeriod) {
    const weekLabel = __("Weeks per Month");
    const baseLabel =
        targetPeriod === "Monthly" ? __("Weekly Target") : __("Monthly Target");
    const newLabel = targetPeriod === "Monthly" ? __("Monthly Target") : __("Weekly Target");
    const baseDisplay = Math.round(Number(baseValue) * 100) / 100;
    const formula =
        targetPeriod === "Monthly"
            ? `${baseDisplay} * ${weeksPerMonth} = ${suggestedValue}`
            : `${baseDisplay} / ${weeksPerMonth} = ${suggestedValue}`;

    return `
        <div class="mb-2">
            <div class="text-muted">${baseLabel} -> ${newLabel}</div>
            <div><strong>${__("Formula")}</strong>: ${formula}</div>
            <div class="text-muted">${weekLabel}: ${weeksPerMonth}</div>
        </div>
    `;
}

function openTargetSwitchDialog(frm, newPeriod) {
    if (frm.is_new()) {
        return;
    }

    const currentPeriod = frm.doc.target_period;
    if (!currentPeriod) {
        frappe.msgprint({
            title: __("Missing Value"),
            message: __("Target period is required."),
            indicator: "red",
        });
        return;
    }

    if (currentPeriod === newPeriod) {
        frappe.msgprint({
            title: __("Nothing to Change"),
            message: __("Target period is already set to {0}.", [newPeriod]),
            indicator: "blue",
        });
        return;
    }

    const baseValue =
        newPeriod === "Monthly"
            ? frm.doc.weekly_target_hours
            : frm.doc.monthly_target_hours;

    if (!baseValue || Number(baseValue) <= 0) {
        frappe.msgprint({
            title: __("Missing Value"),
            message: __("Current target hours are required before switching."),
            indicator: "red",
        });
        return;
    }

    const dialogTitle =
        newPeriod === "Monthly" ? __("Switch to Monthly Target") : __("Switch to Weekly Target");

    getTrackTargetAdjustmentsSetting(frm).then((trackAdjustments) => {
        const fields = [
            {
                fieldtype: "HTML",
                fieldname: "conversion_preview",
            },
            {
                fieldtype: "Float",
                fieldname: "weeks_per_month",
                label: __("Weeks per Month"),
                reqd: 1,
                default: DEFAULT_WEEKS_PER_MONTH,
            },
            {
                fieldtype: "Float",
                fieldname: "suggested_target_hours",
                label: __("Suggested Target Hours"),
                read_only: 1,
            },
            {
                fieldtype: "Float",
                fieldname: "new_target_hours",
                label: __("New Target Hours"),
                reqd: 1,
            },
        ];

        if (trackAdjustments) {
            fields.push({
                fieldname: "reason",
                fieldtype: "Small Text",
                label: __("Reason"),
                reqd: 1,
            });
        }

        const dialog = new frappe.ui.Dialog({
            title: dialogTitle,
            fields,
            primary_action_label: __("Switch"),
            primary_action(values) {
                if (!values) {
                    return;
                }
                const reason = trackAdjustments ? (values.reason || "").trim() : "";
                frappe.call({
                    method:
                        "time_tracking.time_tracking.doctype.time_tracking_profile.time_tracking_profile.switch_target_period",
                    args: {
                        profile_name: frm.doc.name,
                        new_period: newPeriod,
                        new_value: values.new_target_hours,
                        reason: reason || undefined,
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            dialog.hide();
                            frm.reload_doc();
                        }
                    },
                });
            },
        });

        let manualOverride = false;

        function updateSuggestion() {
            const weeks = Number(dialog.get_value("weeks_per_month")) || DEFAULT_WEEKS_PER_MONTH;
            const suggested =
                newPeriod === "Monthly"
                    ? Number(baseValue) * weeks
                    : Number(baseValue) / weeks;
            const rounded = Math.round(suggested * 100) / 100;
            const roundedWeeks = Math.round(weeks * 100) / 100;

            dialog.set_value("suggested_target_hours", rounded);
            if (!manualOverride) {
                dialog.set_value("new_target_hours", rounded);
            }

            dialog.fields_dict.conversion_preview.$wrapper.html(
                buildConversionPreviewHtml(baseValue, roundedWeeks, rounded, newPeriod)
            );
        }

        dialog.show();
        updateSuggestion();

        dialog.get_field("weeks_per_month").$input.on("input", function () {
            manualOverride = false;
            updateSuggestion();
        });

        dialog.get_field("new_target_hours").$input.on("input", function () {
            manualOverride = true;
        });
    });
}

function openTargetAdjustmentDialog(frm, targetPeriod, labelSuffix, direction) {
    const actionLabel =
        direction > 0
            ? __("Increase {0}", [labelSuffix])
            : __("Decrease {0}", [labelSuffix]);

    getTrackTargetAdjustmentsSetting(frm).then((trackAdjustments) => {
        const fields = [
            {
                fieldname: "hours",
                fieldtype: "Float",
                label: __("Hours"),
                reqd: 1,
                default: 1,
            },
        ];

        if (trackAdjustments) {
            fields.push({
                fieldname: "reason",
                fieldtype: "Small Text",
                label: __("Reason"),
                reqd: 1,
            });
        }

        frappe.prompt(
            fields,
            (values) => {
                const hours = Math.abs(values.hours || 0);
                if (!hours) {
                    frappe.msgprint({
                        title: __("Missing Value"),
                        message: __("Please enter a positive hour value."),
                        indicator: "red",
                    });
                    return;
                }

                const reason = trackAdjustments ? (values.reason || "").trim() : "";

                frappe.call({
                    method:
                        "time_tracking.time_tracking.doctype.time_tracking_profile.time_tracking_profile.adjust_target",
                    args: {
                        profile_name: frm.doc.name,
                        target_period: targetPeriod,
                        delta_hours: direction * hours,
                        reason: reason || undefined,
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frm.reload_doc();
                        }
                    },
                });
            },
            actionLabel,
            __("Update")
        );
    });
}

function addTargetButtons(frm) {
    if (!isTargetAdmin() || frm.is_new()) {
        return;
    }

    const targetPeriod = frm.doc.target_period;
    if (!targetPeriod) {
        return;
    }

    const labelSuffix =
        targetPeriod === "Weekly" ? __("Weekly Target") : __("Monthly Target");

    const groupLabel = __("Targets");
    frm.add_custom_button(
        __("Increase {0}", [labelSuffix]),
        () => openTargetAdjustmentDialog(frm, targetPeriod, labelSuffix, 1),
        groupLabel
    );
    frm.add_custom_button(
        __("Decrease {0}", [labelSuffix]),
        () => openTargetAdjustmentDialog(frm, targetPeriod, labelSuffix, -1),
        groupLabel
    );

    if (targetPeriod === "Weekly") {
        frm.add_custom_button(
            __("Switch to Monthly Target"),
            () => openTargetSwitchDialog(frm, "Monthly"),
            groupLabel
        );
    } else if (targetPeriod === "Monthly") {
        frm.add_custom_button(
            __("Switch to Weekly Target"),
            () => openTargetSwitchDialog(frm, "Weekly"),
            groupLabel
        );
    }
}

function openUserProfile(frm) {
    if (!frm.doc.user) {
        return;
    }
    const url = `/app/user/${encodeURIComponent(frm.doc.user)}`;
    window.open(url, "_blank");
}

function addProfileLinks(frm) {
    if (!frm.doc.user) {
        return;
    }

    frm.add_custom_button(__("Open User Profile"), () => openUserProfile(frm), __("Links"));
}

frappe.ui.form.on("Time Tracking Profile", {
    setup(frm) {
        if (frm.fields_dict.project_assignments) {
            frm.fields_dict.project_assignments.grid.get_field("project").get_query = function () {
                return {
                    filters: {
                        is_group: 0,
                        not_bookable: 0,
                    },
                };
            };
        }
    },
    refresh(frm) {
        frm.clear_custom_buttons();
        addTargetButtons(frm);
        addProfileLinks(frm);
        applyRateSettings(frm);
        applyTargetAdjustmentVisibility(frm);
        applyProjectAssignmentVisibility(frm);
    },
});
