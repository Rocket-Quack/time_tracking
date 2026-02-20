frappe.pages["time-tracking-export"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Time Tracking Export"),
		single_column: true,
	});

	const $main = $(wrapper).find(".layout-main-section");
	$main.addClass("time-tracking-export");

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

	const $intro = $(
		`<div class="tt-admin-page-intro">
            <p class="text-muted mb-2">
                ${__("Export time bookings with linked project and user data.")}
            </p>
        </div>`
	);

	const $fields = $('<div class="row tt-admin-page-grid"></div>');
	const $left = $('<div class="col-md-6"></div>');
	const $right = $('<div class="col-md-6"></div>');
	$fields.append($left, $right);
	$card.append($intro, $fields);
	$shell.append($card);
	$main.empty().append($shell);

	const controls = {};
	const fieldDefs = [
		{
			fieldtype: "Select",
			fieldname: "export_format",
			label: __("Export Format"),
			options: ["CSV", "XLSX"].join("\n"),
			default: "CSV",
			reqd: 1,
		},
		{
			fieldtype: "Select",
			fieldname: "date_format",
			label: __("Date Format"),
			options: ["DD.MM.YYYY", "YYYY-MM-DD", "DDMMYYYY", "YYYYMMDD"].join("\n"),
			default: "DD.MM.YYYY",
			reqd: 1,
		},
		{
			fieldtype: "Select",
			fieldname: "duration_format",
			label: __("Duration Format"),
			options: ["Decimal Hours (e.g. 1.25)", "HH:MM (e.g. 1:15)", "Minutes (e.g. 75)"].join(
				"\n"
			),
			default: "Decimal Hours (e.g. 1.25)",
			reqd: 1,
		},
		{
			fieldtype: "Select",
			fieldname: "decimal_separator",
			label: __("Decimal Separator"),
			options: [".", ","].join("\n"),
			default: ".",
			reqd: 1,
		},
		{
			fieldtype: "Date",
			fieldname: "from_date",
			label: __("From Date"),
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldtype: "Date",
			fieldname: "to_date",
			label: __("To Date"),
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldtype: "Link",
			fieldname: "project",
			label: __("Project"),
			options: "Time Tracking Project",
		},
		{
			fieldtype: "Check",
			fieldname: "include_child_projects",
			label: __("Include Child Projects"),
			default: 1,
			depends_on: "eval:doc.project",
		},
		{
			fieldtype: "Link",
			fieldname: "user",
			label: __("Employee"),
			options: "User",
		},
	];

	fieldDefs.forEach((df) => {
		const parent = [
			"export_format",
			"date_format",
			"duration_format",
			"decimal_separator",
			"from_date",
		].includes(df.fieldname)
			? $left
			: $right;
		const wrapper = $('<div class="mb-3"></div>').appendTo(parent);
		const control = frappe.ui.form.make_control({
			df,
			parent: wrapper,
			render_input: true,
		});
		control.refresh();
		controls[df.fieldname] = control;
	});

	const updateDurationControls = () => {
		if (!controls.duration_format || !controls.decimal_separator) {
			return;
		}
		const selectedFormat = controls.duration_format.get_value() || "";
		const isDecimal = selectedFormat.startsWith("Decimal Hours");
		$(controls.decimal_separator.wrapper).toggle(isDecimal);
	};

	if (controls.duration_format && controls.duration_format.$input) {
		controls.duration_format.$input.on("change", updateDurationControls);
	}
	updateDurationControls();

	if (controls.project) {
		controls.project.get_query = function () {
			return {
				query: "time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project.project_link_query",
				filters: {
					is_group: 0,
				},
			};
		};
	}

	page.set_primary_action(__("Export"), () => {
		const args = {
			export_format: controls.export_format.get_value(),
			date_format: controls.date_format.get_value(),
			duration_format: controls.duration_format.get_value(),
			decimal_separator: controls.decimal_separator.get_value(),
			from_date: controls.from_date.get_value(),
			to_date: controls.to_date.get_value(),
			project: controls.project.get_value(),
			include_child_projects: controls.include_child_projects.get_value() ? 1 : 0,
			user: controls.user.get_value(),
		};

		if (typeof open_url_post === "function") {
			open_url_post(
				"/api/method/time_tracking.time_tracking.page.time_tracking_export.time_tracking_export.export_bookings",
				args
			);
			return;
		}

		frappe.call({
			method: "time_tracking.time_tracking.page.time_tracking_export.time_tracking_export.export_bookings",
			args,
		});
	});
};
