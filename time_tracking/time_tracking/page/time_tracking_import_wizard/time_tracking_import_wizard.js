frappe.pages["time-tracking-import-wizard"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Time Tracking Import Wizard"),
        single_column: true,
    });

    const $main = $(wrapper).find(".layout-main-section");
    $main.addClass("time-tracking-import-wizard");

    if (!document.getElementById("time-tracking-admin-page-styles")) {
        $(
            `<style id="time-tracking-admin-page-styles">
                body[data-route="time-tracking-export"] .page-body,
                body[data-route="time-tracking-import-wizard"] .page-body {
                    padding-left: 12px;
                    padding-right: 12px;
                }
                .layout-main-section.time-tracking-export,
                .layout-main-section.time-tracking-import-wizard {
                    width: 100%;
                    max-width: 1180px;
                    margin: 0 auto;
                    padding: 14px 8px 28px;
                }
                .tt-admin-page-shell { width: 100%; }
                .tt-admin-page-card {
                    background: var(--card-bg, var(--fg-color, #ffffff));
                    color: var(--text-color, inherit);
                    border: 1px solid var(--border-color, #d1d8dd);
                    border-radius: 14px;
                    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                    padding: 18px 20px 12px;
                }
                .tt-admin-page-card .text-muted {
                    color: var(--text-muted, #6c757d) !important;
                }
                .tt-admin-page-intro { margin-bottom: 12px; }
                .tt-admin-page-grid { margin-left: -10px; margin-right: -10px; }
                .tt-admin-page-grid > [class*="col-"] {
                    padding-left: 10px;
                    padding-right: 10px;
                }
                .tt-admin-page-card .form-group { margin-bottom: 14px; }
                body[data-theme="dark"] .tt-admin-page-card {
                    background: var(--card-bg, var(--fg-color, #1f2731));
                    border-color: var(--border-color, #3a4758);
                    box-shadow: none;
                }
                @media (max-width: 991px) {
                    .layout-main-section.time-tracking-export,
                    .layout-main-section.time-tracking-import-wizard {
                        padding-left: 4px;
                        padding-right: 4px;
                    }
                    .tt-admin-page-card {
                        padding: 14px 14px 8px;
                        border-radius: 12px;
                    }
                }
            </style>`
        ).appendTo(document.head);
    }

    const $shell = $('<div class="tt-admin-page-shell"></div>');
    const $card = $('<div class="tt-admin-page-card"></div>');

    const $intro = $(`
        <div class="tt-admin-page-intro">
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

    const $fields = $('<div class="row tt-admin-page-grid"></div>');
    const $left = $('<div class="col-md-6"></div>');
    const $right = $('<div class="col-md-6"></div>');

    $fields.append($left, $right);
    $card.append($intro, $fields);
    $shell.append($card);
    $main.empty().append($shell);

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
