frappe.pages["weekly-booking"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Weekly Booking"),
        single_column: true,
    });

    const $container = $(frappe.render_template("weekly_booking"));
    $container.appendTo(page.body);

    const styles = `
        <style>
            body[data-route="weekly-booking"] .layout-main-section { max-width: none; min-width: 0; }
            body[data-route="weekly-booking"] .page-body { padding-left: 12px; padding-right: 12px; }
            .weekly-booking-page { width: 100%; min-width: 0; }
            .weekly-booking .weekly-booking-tableWrap {
                width: 100%;
                max-width: 100%;
                overflow-x: auto;
                overflow-y: visible;
                -webkit-overflow-scrolling: touch;
                padding-bottom: 4px;
            }
            .weekly-booking .weekly-booking-table {
                min-width: 100%;
                width: max-content;
                table-layout: auto;
                border-collapse: collapse;
            }
            .weekly-booking .weekly-booking-table th,
            .weekly-booking .weekly-booking-table td {
                vertical-align: middle;
                padding: 4px 6px;
                white-space: nowrap;
            }
            .weekly-booking .weekly-booking-table td { overflow: visible; }
            .weekly-booking .wb-project-col { min-width: 240px; }
            .weekly-booking .wb-note-col { min-width: 240px; }
            .weekly-booking .wb-day-header { text-align: center; min-width: 140px; }
            .weekly-booking .wb-day-name { font-weight: 600; }
            .weekly-booking .wb-day-date { font-size: 11px; color: #6c757d; }
            .weekly-booking .form-control { height: 32px; padding: 2px 6px; }
            .weekly-booking .input-group-sm .form-control { height: 32px; }
            .weekly-booking .weekly-booking-timeCell { min-width: 140px; }
            .weekly-booking .weekly-booking-timeInput {
                min-width: 80px;
                width: 80px;
                text-align: center;
                font-variant-numeric: tabular-nums;
            }
            .weekly-booking .wb-row-saved td { background: #e8f6ef; }
            .weekly-booking .wb-row-saved td:first-child { box-shadow: inset 3px 0 0 #28a745; }
            .weekly-booking .wb-row-saved:hover td { background: #e0f2e9; }
            .weekly-booking .wb-row-unsaved td { background: #fff4e5; }
            .weekly-booking .wb-row-unsaved td:first-child { box-shadow: inset 3px 0 0 #f0ad4e; }
            .weekly-booking .wb-row-unsaved:hover td { background: #ffe9cc; }
            .weekly-booking .wb-divider-row td {
                padding: 0 !important;
                height: 8px;
                border: none !important;
                background: transparent !important;
            }
            .weekly-booking .wb-divider-row:hover td { background: transparent !important; }
            .weekly-booking .weekly-booking-stepperBtn {
                width: 32px;
                height: 32px;
                flex: 0 0 32px;
                padding: 0;
            }
            .weekly-booking .weekly-booking-summary {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 12px;
            }
            .weekly-booking .weekly-booking-summary .card {
                min-width: 260px;
            }
            .weekly-booking .weekly-booking-summary .wb-summary-value {
                font-size: 26px;
                font-weight: 600;
            }
            .weekly-booking .weekly-booking-summary .wb-summary-status {
                font-size: 12px;
                color: #6c757d;
            }
            .weekly-booking tfoot td { background: #f8f9fa; }
            .weekly-booking .wb-week-total { text-align: right; }
            .weekly-booking .wb-note { min-width: 220px; }
            .weekly-booking .wb-project { min-width: 220px; }
        </style>
    `;
    $(styles).appendTo(page.body);

    const state = {
        projects_loaded: false,
        projects: [],
        increment_minutes: 15,
        day_label_format: "DD.MM.YYYY",
        weekly_target_hours: null,
        monthly_target_hours: null,
        month_total_minutes: 0,
        loaded_week_total_minutes: 0,
        overtime_balance_minutes: 0,
        saved_row_counts: new Map(),
    };

    const $user = $container.find("#weekly-booking-user");
    const $weekStart = $container.find("#weekly-booking-week-start");
    const $calendarWeek = $container.find("#weekly-booking-calendar-week");
    const $periodLabel = $container.find("#weekly-booking-period-label");
    const $table = $container.find("#weekly-booking-table");
    const $summary = $container.find("#weekly-booking-summary");

    $user.val(frappe.session.user);

    const tableHtml = `
        <div class="weekly-booking-tableWrap">
            <table class="table table-bordered table-sm table-hover weekly-booking-table">
                <thead>
                    <tr>
                        <th class="wb-project-col">${__("Project")}</th>
                        <th class="wb-note-col">${__("Note")}</th>
                        <th class="wb-day-header" data-day="0">
                            <div class="wb-day-name">${__("Mon")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="1">
                            <div class="wb-day-name">${__("Tue")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="2">
                            <div class="wb-day-name">${__("Wed")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="3">
                            <div class="wb-day-name">${__("Thu")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="4">
                            <div class="wb-day-name">${__("Fri")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="5">
                            <div class="wb-day-name">${__("Sat")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                        <th class="wb-day-header" data-day="6">
                            <div class="wb-day-name">${__("Sun")}</div>
                            <div class="wb-day-date"></div>
                        </th>
                    </tr>
                </thead>
                <tbody id="weekly-booking-rows"></tbody>
                <tfoot>
                    <tr>
                        <td><strong>${__("Total")}</strong></td>
                        <td></td>
                        <td class="weekly-booking-total" data-field="monday_hours">0</td>
                        <td class="weekly-booking-total" data-field="tuesday_hours">0</td>
                        <td class="weekly-booking-total" data-field="wednesday_hours">0</td>
                        <td class="weekly-booking-total" data-field="thursday_hours">0</td>
                        <td class="weekly-booking-total" data-field="friday_hours">0</td>
                        <td class="weekly-booking-total" data-field="saturday_hours">0</td>
                        <td class="weekly-booking-total" data-field="sunday_hours">0</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <div class="mt-2">
            <button class="btn btn-default" id="weekly-booking-add-row">+ ${__("Add Row")}</button>
        </div>
    `;

    $table.html(tableHtml);

    const summaryHtml = `
        <div class="weekly-booking-summary">
            <div class="card">
                <div class="card-body">
                    <div class="card-title text-muted">${__("Week Total")}</div>
                    <div class="wb-summary-value" id="weekly-booking-week-total">0:00</div>
                    <div class="wb-summary-status" id="weekly-booking-week-status"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="card-title text-muted">${__("Month Total")}</div>
                    <div class="wb-summary-value" id="weekly-booking-month-total">0:00</div>
                    <div class="wb-summary-status" id="weekly-booking-month-status"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="card-title text-muted">${__("Hours Balance")}</div>
                    <div class="wb-summary-value" id="weekly-booking-hours-balance">0:00</div>
                </div>
            </div>
        </div>
    `;
    $summary.html(summaryHtml);

    const $rows = $table.find("#weekly-booking-rows");
    const $addRowButton = $table.find("#weekly-booking-add-row");
    const $weekTotal = $summary.find("#weekly-booking-week-total");
    const $weekStatus = $summary.find("#weekly-booking-week-status");
    const $monthTotal = $summary.find("#weekly-booking-month-total");
    const $monthStatus = $summary.find("#weekly-booking-month-status");
    const $hoursBalance = $summary.find("#weekly-booking-hours-balance");

    const dividerColspan = 2 + 7;
    const hourFields = [
        { field: "monday_hours", class: "wb-mon" },
        { field: "tuesday_hours", class: "wb-tue" },
        { field: "wednesday_hours", class: "wb-wed" },
        { field: "thursday_hours", class: "wb-thu" },
        { field: "friday_hours", class: "wb-fri" },
        { field: "saturday_hours", class: "wb-sat" },
        { field: "sunday_hours", class: "wb-sun" },
    ];

    function buildProjectOptions(selected) {
        const escape = frappe.utils.escape_html;
        const options = [`<option value=""></option>`];
        let selectedFound = false;

        state.projects.forEach((project) => {
            const value = escape(project.name);
            const label = escape(project.project_name || project.name);
            const selectedAttr = project.name === selected ? " selected" : "";
            if (selectedAttr) {
                selectedFound = true;
            }
            options.push(`<option value="${value}"${selectedAttr}>${label}</option>`);
        });

        if (selected && !selectedFound) {
            const value = escape(selected);
            options.push(`<option value="${value}" selected>${value}</option>`);
        }

        return options.join("");
    }

    function isRowFilled($row) {
        const project = $row.find(".wb-project").val();
        if (project) {
            return true;
        }
        const note = ($row.find(".wb-note").val() || "").trim();
        if (note) {
            return true;
        }
        let hasHours = false;
        $row.find(".wb-hours").each(function () {
            if (parseMinutes($(this).val()) > 0) {
                hasHours = true;
                return false;
            }
        });
        return hasHours;
    }

    function buildRowSignature(project, note, minutesByField) {
        const parts = [project || "", note || ""];
        hourFields.forEach((field) => {
            parts.push(String(minutesByField[field.field] || 0));
        });
        return parts.join("||");
    }

    function buildSignatureFromRow($row) {
        const minutesByField = {};
        hourFields.forEach((field) => {
            minutesByField[field.field] = parseMinutes($row.find(`.${field.class}`).val());
        });
        const project = $row.find(".wb-project").val() || "";
        const note = ($row.find(".wb-note").val() || "").trim();
        return buildRowSignature(project, note, minutesByField);
    }

    function buildSignatureFromData(row) {
        const minutesByField = {};
        hourFields.forEach((field) => {
            minutesByField[field.field] = Math.round(Number(row[field.field] || 0) * 60);
        });
        const project = row.project || "";
        const note = (row.note || "").trim();
        return buildRowSignature(project, note, minutesByField);
    }

    function isRowDataEmpty(row) {
        if (row.project) {
            return false;
        }
        const note = (row.note || "").trim();
        if (note) {
            return false;
        }
        return !hourFields.some((field) => Number(row[field.field] || 0) > 0);
    }

    function buildSavedRowCounts(rows) {
        const counts = new Map();
        (rows || []).forEach((row) => {
            if (isRowDataEmpty(row)) {
                return;
            }
            const signature = buildSignatureFromData(row);
            counts.set(signature, (counts.get(signature) || 0) + 1);
        });
        return counts;
    }

    function applyRowHighlights() {
        const remaining = new Map();
        if (state.saved_row_counts) {
            state.saved_row_counts.forEach((count, key) => {
                remaining.set(key, count);
            });
        }

        getDataRows().each(function () {
            const $row = $(this);
            if (!isRowFilled($row)) {
                $row.removeClass("wb-row-saved wb-row-unsaved");
                return;
            }

            const signature = buildSignatureFromRow($row);
            const count = remaining.get(signature) || 0;
            if (count > 0) {
                $row.addClass("wb-row-saved").removeClass("wb-row-unsaved");
                remaining.set(signature, count - 1);
            } else {
                $row.addClass("wb-row-unsaved").removeClass("wb-row-saved");
            }
        });
    }

    function addDividerRow() {
        $rows.append(
            `<tr class="wb-divider-row" data-row-type="divider"><td colspan="${dividerColspan}"></td></tr>`
        );
    }

    function getDataRows() {
        return $rows.find("tr").not(".wb-divider-row");
    }

    const increaseLabel = __("Increase time");
    const decreaseLabel = __("Decrease time");
    const maxCellMinutes = 24 * 60;

    function buildTimeCell(className) {
        return `
            <div class="input-group input-group-sm wb-time-cell weekly-booking-timeCell">
                <input type="text" class="form-control wb-hours ${className} weekly-booking-timeInput" inputmode="numeric" placeholder="0:00">
                <div class="input-group-append">
                    <button type="button" class="btn btn-default wb-step weekly-booking-stepperBtn" data-direction="down" aria-label="${decreaseLabel}">-</button>
                    <button type="button" class="btn btn-default wb-step weekly-booking-stepperBtn" data-direction="up" aria-label="${increaseLabel}">+</button>
                </div>
            </div>
        `;
    }
    function addRow(row = {}, skipTotals = false) {
        const $row = $(
            `<tr>
                <td class="wb-project-col"><select class="form-control wb-project"></select></td>
                <td class="wb-note-col"><input type="text" class="form-control wb-note"></td>
                <td>${buildTimeCell("wb-mon")}</td>
                <td>${buildTimeCell("wb-tue")}</td>
                <td>${buildTimeCell("wb-wed")}</td>
                <td>${buildTimeCell("wb-thu")}</td>
                <td>${buildTimeCell("wb-fri")}</td>
                <td>${buildTimeCell("wb-sat")}</td>
                <td>${buildTimeCell("wb-sun")}</td>
            </tr>`
        );

        $row.find(".wb-project").html(buildProjectOptions(row.project));
        $row.find(".wb-note").val(row.note || "");

        hourFields.forEach((field) => {
            const value = row[field.field];
            const $input = $row.find(`.${field.class}`);
            if (value && Number(value) > 0) {
                $input.val(formatMinutes(Math.round(Number(value) * 60)));
            } else {
                $input.val("");
            }
        });

        $rows.append($row);
        if (!skipTotals) {
            updateTotals();
        }
    }

    function renderRows(rows) {
        $rows.empty();
        if (rows && rows.length) {
            rows.forEach((row) => addRow(row, true));
        }

        if (rows && rows.length) {
            addDividerRow();
        }

        const emptyRows = 3;
        for (let i = 0; i < emptyRows; i++) {
            addRow({}, true);
        }
        updateTotals();
        applyRowHighlights();
    }

    function loadProjects(callback) {
        frappe.call({
            method: "time_tracking.time_tracking.page.weekly_booking.weekly_booking.get_assigned_projects",
            args: {
                user: $user.val(),
            },
            callback: function (r) {
                state.projects = r.message || [];
                state.projects_loaded = true;
                $addRowButton.prop("disabled", false);
                if (callback) {
                    callback();
                }
            },
        });
    }

    function setIncrementMinutes(value) {
        const increment = Number.parseInt(value, 10);
        state.increment_minutes = Number.isFinite(increment) && increment > 0 ? increment : 15;
    }

    function updateDayHeaders() {
        const weekStart = $weekStart.val();
        const format = state.day_label_format || "DD.MM.YYYY";
        const start = weekStart ? moment(weekStart, "YYYY-MM-DD") : null;

        $table.find(".wb-day-header").each(function () {
            const $header = $(this);
            const offset = Number.parseInt($header.data("day"), 10) || 0;
            const $date = $header.find(".wb-day-date");
            if (!start || !start.isValid()) {
                $date.text("");
                return;
            }
            $date.text(start.clone().add(offset, "days").format(format));
        });
    }

    function loadWeek() {
        const weekStart = $weekStart.val();
        if (!weekStart) {
            frappe.msgprint({
                title: __("Missing Value"),
                message: __("Week start is required."),
                indicator: "red",
            });
            return;
        }

        frappe.call({
            method: "time_tracking.time_tracking.page.weekly_booking.weekly_booking.get_weekly_booking",
            args: {
                user: $user.val(),
                week_start_date: weekStart,
            },
            callback: function (r) {
                const message = r.message || {};
                if (message.increment_minutes) {
                    setIncrementMinutes(message.increment_minutes);
                }
                if (message.day_label_date_format) {
                    state.day_label_format = message.day_label_date_format;
                }
                state.weekly_target_hours = message.weekly_target_hours || null;
                state.monthly_target_hours = message.monthly_target_hours || null;
                state.month_total_minutes = Math.round(Number(message.monthly_total_hours || 0) * 60);
                state.overtime_balance_minutes = Math.round(
                    Number(message.overtime_balance_hours || 0) * 60
                );
                if (message.calendar_week && message.calendar_year) {
                    $calendarWeek.val(`${message.calendar_week} / ${message.calendar_year}`);
                } else {
                    $calendarWeek.val(message.calendar_week || "");
                }
                $periodLabel.val(message.period_label || "");
                updateDayHeaders();

                const rows = message.rows || [];
                state.loaded_week_total_minutes = calculateWeekMinutes(rows);
                state.saved_row_counts = buildSavedRowCounts(rows);
                if (!state.projects_loaded) {
                    loadProjects(() => renderRows(rows));
                } else {
                    renderRows(rows);
                }

                if (message.warning) {
                    frappe.msgprint({
                        title: __("Notice"),
                        message: message.warning,
                        indicator: "orange",
                    });
                }

                updateHoursBalance();
            },
        });
    }

    function collectRows() {
        const rows = [];
        getDataRows().each(function () {
            const $row = $(this);
            const rowData = {
                project: $row.find(".wb-project").val(),
                note: $row.find(".wb-note").val(),
            };

            hourFields.forEach((field) => {
                rowData[field.field] = normalizeHours($row.find(`.${field.class}`).val());
            });

            rows.push(rowData);
        });

        return rows;
    }

    function parseMinutes(value) {
        if (value === null || value === undefined || value === "") {
            return 0;
        }

        if (typeof value === "string" && value.includes(":")) {
            const parts = value.split(":");
            const hours = Number.parseInt(parts[0], 10);
            const minutes = Number.parseInt(parts[1], 10);
            if (Number.isFinite(hours) && Number.isFinite(minutes)) {
                return hours * 60 + minutes;
            }
        }

        const parsed = parseFloat(value);
        return Number.isFinite(parsed) ? Math.round(parsed * 60) : 0;
    }

    function formatMinutes(totalMinutes) {
        const minutes = Math.max(0, Math.round(totalMinutes));
        const hours = Math.floor(minutes / 60);
        const remainder = minutes % 60;
        return `${hours}:${String(remainder).padStart(2, "0")}`;
    }

    function normalizeHours(value) {
        if (value === null || value === undefined || value === "") {
            return "";
        }
        const minutes = parseMinutes(value);
        return minutes / 60;
    }

    function setInputMinutes($input, minutes) {
        const total = Math.min(maxCellMinutes, Math.max(0, Math.round(minutes)));
        if (!total) {
            $input.val("");
            return;
        }
        $input.val(formatMinutes(total));
    }

    function getStepMinutes(event) {
        const base = state.increment_minutes || 15;
        return event && event.shiftKey ? base * 4 : base;
    }

    function adjustInputMinutes($input, deltaMinutes) {
        const current = parseMinutes($input.val());
        setInputMinutes($input, current + deltaMinutes);
        applyRowHighlights();
        updateTotals();
    }

    function calculateWeekMinutes(rows) {
        let total = 0;
        rows.forEach((row) => {
            hourFields.forEach((field) => {
                total += parseMinutes(row[field.field]);
            });
        });
        return total;
    }

    function updateTotals() {
        const totals = {
            monday_hours: 0,
            tuesday_hours: 0,
            wednesday_hours: 0,
            thursday_hours: 0,
            friday_hours: 0,
            saturday_hours: 0,
            sunday_hours: 0,
        };

        getDataRows().each(function () {
            const $row = $(this);
            hourFields.forEach((field) => {
                totals[field.field] += parseMinutes($row.find(`.${field.class}`).val());
            });
        });

        let weekTotal = 0;
        hourFields.forEach((field) => {
            const total = totals[field.field];
            weekTotal += total;
            $table
                .find(`.weekly-booking-total[data-field="${field.field}"]`)
                .text(formatMinutes(total));
        });

        $weekTotal.text(formatMinutes(weekTotal));
        updateWeeklyStatus(weekTotal);
        updateMonthlyStatus(weekTotal);
    }

    function updateMonthlyStatus(weekTotalMinutes) {
        const adjustedMonthTotal =
            state.month_total_minutes + (weekTotalMinutes - state.loaded_week_total_minutes);
        $monthTotal.text(formatMinutes(adjustedMonthTotal));

        const targetHours = state.monthly_target_hours;
        if (!targetHours) {
            $monthStatus.text(__("Monthly target not set."));
            $monthStatus.css("color", "#6c757d");
            return;
        }

        const targetMinutes = Math.round(Number(targetHours) * 60);
        const diff = adjustedMonthTotal - targetMinutes;
        if (diff >= 0) {
            $monthStatus
                .text(`${__("Over by")}: ${formatMinutes(diff)}`)
                .css("color", "#28a745");
        } else {
            $monthStatus
                .text(`${__("Remaining")}: ${formatMinutes(Math.abs(diff))}`)
                .css("color", "#dc3545");
        }
    }

    function updateWeeklyStatus(weekTotalMinutes) {
        const targetHours = state.weekly_target_hours;
        if (!targetHours) {
            $weekStatus.text(__("Weekly target not set."));
            $weekStatus.css("color", "#6c757d");
            return;
        }

        const targetMinutes = Math.round(Number(targetHours) * 60);
        const diff = weekTotalMinutes - targetMinutes;
        if (diff >= 0) {
            $weekStatus
                .text(`${__("Over by")}: ${formatMinutes(diff)}`)
                .css("color", "#28a745");
        } else {
            $weekStatus
                .text(`${__("Remaining")}: ${formatMinutes(Math.abs(diff))}`)
                .css("color", "#dc3545");
        }
    }

    function formatSignedMinutes(totalMinutes) {
        const sign = totalMinutes < 0 ? "-" : "";
        return `${sign}${formatMinutes(Math.abs(totalMinutes))}`;
    }

    function updateHoursBalance() {
        $hoursBalance.text(formatSignedMinutes(state.overtime_balance_minutes));
    }

    function saveWeek() {
        const weekStart = $weekStart.val();
        if (!weekStart) {
            frappe.msgprint({
                title: __("Missing Value"),
                message: __("Week start is required."),
                indicator: "red",
            });
            return;
        }

        const payload = {
            user: $user.val(),
            week_start_date: weekStart,
            rows: collectRows(),
        };

        frappe.call({
            method: "time_tracking.time_tracking.page.weekly_booking.weekly_booking.save_weekly_booking",
            args: {
                data: JSON.stringify(payload),
            },
            callback: function (r) {
                const message = r.message || {};
                const weekMinutes = calculateWeekMinutes(collectRows());
                state.loaded_week_total_minutes = weekMinutes;
                if (message.monthly_total_hours !== undefined) {
                    state.month_total_minutes = Math.round(
                        Number(message.monthly_total_hours || 0) * 60
                    );
                }
                updateTotals();
                state.saved_row_counts = buildSavedRowCounts(collectRows());
                applyRowHighlights();

                frappe.msgprint({
                    title: __("Saved"),
                    message: __("Weekly booking saved."),
                    indicator: "green",
                });

                if (message.warning) {
                    frappe.msgprint({
                        title: __("Notice"),
                        message: message.warning,
                        indicator: "orange",
                    });
                }
            },
        });
    }

    function setWeekStart(dateStr) {
        $weekStart.val(dateStr);
        loadWeek();
    }

    function shiftWeek(days) {
        const current = $weekStart.val() || frappe.datetime.get_today();
        const next = moment(current).add(days, "days").format("YYYY-MM-DD");
        setWeekStart(next);
    }

    page.set_primary_action(__("Save"), saveWeek);
    $container.find("#weekly-booking-prev").on("click", function () {
        shiftWeek(-7);
    });
    $container.find("#weekly-booking-next").on("click", function () {
        shiftWeek(7);
    });
    $addRowButton.on("click", function () {
        addRow({});
        applyRowHighlights();
    });
    $rows.on("change input", ".wb-project, .wb-note", function () {
        applyRowHighlights();
    });
    $rows.on("keydown", ".wb-hours", function (event) {
        if (event.key !== "ArrowUp" && event.key !== "ArrowDown") {
            return;
        }
        event.preventDefault();
        const direction = event.key === "ArrowUp" ? 1 : -1;
        const step = getStepMinutes(event);
        adjustInputMinutes($(this), direction * step);
    });
    $rows.on("blur", ".wb-hours", function () {
        const $input = $(this);
        const minutes = parseMinutes($input.val());
        setInputMinutes($input, minutes);
        applyRowHighlights();
        updateTotals();
    });
    $rows.on("click", ".wb-step", function (event) {
        const $step = $(this);
        const direction = $step.data("direction");
        const delta = direction === "up" ? getStepMinutes(event) : -getStepMinutes(event);
        const $input = $step.closest(".wb-time-cell").find(".wb-hours");
        adjustInputMinutes($input, delta);
    });
    $rows.on("input change", ".wb-hours", function () {
        applyRowHighlights();
        updateTotals();
    });

    $addRowButton.prop("disabled", true);
    loadProjects();
    renderRows([]);

    const currentWeekStart = moment(frappe.datetime.get_today())
        .startOf("isoWeek")
        .format("YYYY-MM-DD");
    setWeekStart(currentWeekStart);
};


