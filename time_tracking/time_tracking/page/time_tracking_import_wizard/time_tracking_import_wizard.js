frappe.pages["time-tracking-import-wizard"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Time Tracking Import Wizard"),
        single_column: true,
    });

    const $main = $(wrapper).find(".layout-main-section");
    $main.addClass("time-tracking-import-wizard");

    const $intro = $(`
        <div class="mb-4">
            <p class="text-muted mb-2">
                ${__(
                    "Prepare and validate imports before writing data to the system."
                )}
            </p>
            <div class="text-muted small">
                ${__("Steps")}: 1) ${__("Upload")} 2) ${__(
        "Map Fields"
    )} 3) ${__("Validate")} 4) ${__("Import")}
            </div>
        </div>
    `);

    const $fields = $('<div class="row"></div>');
    const $left = $('<div class="col-md-6"></div>');
    const $right = $('<div class="col-md-6"></div>');

    $fields.append($left, $right);
    $main.append($intro, $fields);

    const controls = {};
    [
        {
            fieldtype: "Select",
            fieldname: "import_type",
            label: __("Import Type"),
            options: ["", "Time Tracking Profile", "Time Tracking Project", "Time Booking"].join(
                "\n"
            ),
            description: __("More templates will be added later."),
        },
        {
            fieldtype: "Attach",
            fieldname: "source_file",
            label: __("Source File"),
            description: __("Upload a CSV or Excel file to continue."),
        },
    ].forEach((df) => {
        const parent = df.fieldname === "source_file" ? $right : $left;
        const wrapper = $('<div class="mb-3"></div>').appendTo(parent);
        const control = frappe.ui.form.make_control({
            df,
            parent: wrapper,
            render_input: true,
        });
        control.refresh();
        controls[df.fieldname] = control;
    });

    page.set_primary_action(__("Start Import"), () => {
        frappe.msgprint({
            title: __("Import Wizard"),
            message: __(
                "Import execution is not configured yet. This wizard is a placeholder for the upcoming workflow."
            ),
            indicator: "blue",
        });
    });
};
