frappe.ui.form.on("Time Tracking Holiday List", {
    setup(frm) {
        set_year_options(frm);
    },
    onload(frm) {
        set_year_options(frm);
    },
    refresh(frm) {
        set_year_options(frm);
        set_holiday_list_name(frm);
        add_fetch_holidays_button(frm);
    },
    year(frm) {
        set_holiday_list_name(frm);
    },
});

function set_year_options(frm) {
    const current_year = new Date().getFullYear();
    const start_year = current_year - 1;
    const end_year = current_year + 5;
    const options = [];
    for (let year = start_year; year <= end_year; year += 1) {
        options.push(String(year));
    }
    frm.set_df_property("year", "options", options.join("\n"));
    if (frm.fields_dict.year) {
        frm.refresh_field("year");
    }
    if (!frm.doc.year || !options.includes(String(frm.doc.year))) {
        frm.set_value("year", String(current_year));
    }
}

function add_fetch_holidays_button(frm) {
    frm.add_custom_button(__("Fetch Holidays"), () => open_fetch_dialog(frm));
}

function set_holiday_list_name(frm) {
    if (!frm.doc.year) {
        frm.set_value("holiday_list_name", "");
        return;
    }
    const expected_name = `${frm.doc.year}-Holiday-List`;
    if (frm.doc.holiday_list_name !== expected_name) {
        frm.set_value("holiday_list_name", expected_name);
    }
}

function open_fetch_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __("Fetch Holidays"),
        fields: [
            {
                fieldtype: "Select",
                fieldname: "continent",
                label: __("Continent"),
                options: ["Europe", "Americas", "Asia", "Africa", "Oceania"],
                reqd: 1,
            },
            {
                fieldtype: "Select",
                fieldname: "country",
                label: __("Country"),
                reqd: 1,
            },
            {
                fieldtype: "Check",
                fieldname: "replace_existing",
                label: __("Replace existing holidays"),
                default: 1,
            },
        ],
        primary_action_label: __("Fetch"),
        primary_action(values) {
            if (!values) {
                return;
            }

            const country_code = (values.country || "").split(" - ")[0].trim();
            if (!country_code) {
                frappe.msgprint(__("Country is required."));
                return;
            }
            const selected_year = frm.doc.year;
            if (!selected_year) {
                frappe.msgprint(__("Year is required."));
                return;
            }
            frappe.call({
                method:
                    "time_tracking.time_tracking.doctype.time_tracking_holiday_list.time_tracking_holiday_list.fetch_open_holidays",
                args: {
                    country_code,
                    year: selected_year,
                },
                freeze: true,
                freeze_message: __("Fetching holidays..."),
                callback: (response) => {
                    const holidays = response.message || [];
                    if (!holidays.length) {
                        frappe.msgprint(
                            __("No holidays found for {0} in {1}.").format(
                                country_code,
                                selected_year
                            )
                        );
                        return;
                    }

                    if (values.replace_existing) {
                        frm.clear_table("holidays");
                    }

                    const existing_rows = {};
                    (frm.doc.holidays || []).forEach((row) => {
                        if (row.holiday_date && !existing_rows[row.holiday_date]) {
                            existing_rows[row.holiday_date] = row;
                        }
                    });

                    holidays.forEach((holiday) => {
                        const existing_row = existing_rows[holiday.date];
                        if (existing_row) {
                            existing_row.description = holiday.name || existing_row.description;
                            return;
                        }
                        const row = frm.add_child("holidays");
                        row.holiday_date = holiday.date;
                        row.description = holiday.name || "";
                        existing_rows[holiday.date] = row;
                    });

                    frm.refresh_field("holidays");
                    frappe.show_alert({
                        message: __(
                            "Fetched {0} holidays. Please save to apply changes."
                        ).format(holidays.length),
                        indicator: "green",
                    });
                    dialog.hide();
                },
            });
        },
    });

    dialog.set_value("continent", "Europe");
    load_holiday_countries(dialog, "Europe");
    dialog.fields_dict.continent.$input.on("change", () => {
        const continent = dialog.get_value("continent");
        load_holiday_countries(dialog, continent);
    });
    dialog.show();
}

let open_holiday_country_cache = null;
let open_holiday_country_request = null;

function load_holiday_countries(dialog, continent) {
    if (open_holiday_country_cache) {
        update_country_options(dialog, continent, open_holiday_country_cache);
        return;
    }

    if (!open_holiday_country_request) {
        open_holiday_country_request = frappe.call({
            method:
                "time_tracking.time_tracking.doctype.time_tracking_holiday_list.time_tracking_holiday_list.get_open_holiday_countries",
            freeze: true,
            freeze_message: __("Fetching countries..."),
        });
    }

    open_holiday_country_request.then((response) => {
        open_holiday_country_cache = response.message || {};
        update_country_options(dialog, continent, open_holiday_country_cache);
    }).catch(() => {
        open_holiday_country_request = null;
        frappe.msgprint(__("No countries available for selection."));
    });
}

function update_country_options(dialog, continent, data) {
    const countries = data[continent] || [];
    const options = countries.map((country) => {
        return `${country.code} - ${country.name}`;
    });

    dialog.set_df_property("country", "options", options.join("\n"));
    if (options.length) {
        dialog.set_value("country", options[0]);
    } else {
        dialog.set_value("country", "");
        frappe.msgprint(__("No countries available for the selected continent."));
    }
}
