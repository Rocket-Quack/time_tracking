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
            .weekly-booking .wb-day-holiday-label {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.4px;
                color: #6c757d;
                margin-bottom: 2px;
            }
            .weekly-booking .wb-day-holiday-col {
                background: #f3f5f7;
                box-shadow: inset 0 0 0 9999px rgba(0, 0, 0, 0.02);
            }
            .weekly-booking .wb-day-holiday-col .form-control {
                background: #f3f5f7;
            }
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
            .weekly-booking .wb-row-suggested td { background: #e7f1ff; }
            .weekly-booking .wb-row-suggested td:first-child { box-shadow: inset 3px 0 0 #2f80ed; }
            .weekly-booking .wb-row-suggested:hover td { background: #dbeaff; }
            .weekly-booking .wb-day-highlight {
                background: #cfe2ff !important;
                transition: background-color 0.6s ease;
            }
            .weekly-booking .wb-col-week { padding-right: 6px; }
            .weekly-booking .wb-col-today { padding-left: 6px; padding-right: 6px; }
            .weekly-booking .wb-col-calendar { padding-left: 6px; }
            .weekly-booking .wb-actions-col { min-width: 48px; width: 48px; }
            .weekly-booking .wb-actions-cell { text-align: center; }
            .weekly-booking .wb-row-delete {
                width: 30px;
                height: 30px;
                line-height: 1;
                padding: 0;
            }
            .weekly-booking .wb-divider-row td {
                padding: 0 !important;
                height: 8px;
                border: none !important;
                background: transparent !important;
            }
            .weekly-booking .wb-divider-row:hover td { background: transparent !important; }
            .weekly-booking .wb-section-divider td { height: 8px; }
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
            .weekly-booking .weekly-booking-legend {
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 8px;
                font-size: 12px;
                color: #6c757d;
            }
            .weekly-booking .wb-legend-item {
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            .weekly-booking .wb-legend-swatch {
                width: 16px;
                height: 10px;
                border-radius: 3px;
                border-left: 3px solid transparent;
            }
            .weekly-booking .wb-legend-saved {
                background: #e8f6ef;
                border-left-color: #28a745;
            }
            .weekly-booking .wb-legend-unsaved {
                background: #fff4e5;
                border-left-color: #f0ad4e;
            }
            .weekly-booking .wb-legend-suggested {
                background: #e7f1ff;
                border-left-color: #2f80ed;
            }
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
        target_period: null,
        month_total_minutes: 0,
        loaded_week_total_minutes: 0,
        overtime_balance_minutes: 0,
        weekly_forecast_minutes: 0,
        holiday_dates: [],
        holiday_minutes_by_day: {},
        holiday_hours_per_day: 0,
        saved_row_counts: new Map(),
    };

    const $user = $container.find("#weekly-booking-user");
    const $weekStart = $container.find("#weekly-booking-week-start");
    const $calendarWeek = $container.find("#weekly-booking-calendar-week");
    const $table = $container.find("#weekly-booking-table");
    const $summary = $container.find("#weekly-booking-summary");
    const $todayButton = $container.find("#weekly-booking-today");
    let weekStartPicker = null;
    let isSyncingWeekStart = false;
    let pendingScrollDayIndex = null;
    let highlightTimer = null;

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
                        <th class="wb-actions-col"></th>
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
                        <td></td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <div class="mt-2">
            <button class="btn btn-default" id="weekly-booking-add-row">+ ${__("Add Row")}</button>
        </div>
        <div class="weekly-booking-legend">
            <span><strong>${__("Legend")}</strong></span>
            <span class="wb-legend-item">
                <span class="wb-legend-swatch wb-legend-saved"></span>${__("Saved rows")}
            </span>
            <span class="wb-legend-item">
                <span class="wb-legend-swatch wb-legend-unsaved"></span>${__("Unsaved rows")}
            </span>
            <span class="wb-legend-item">
                <span class="wb-legend-swatch wb-legend-suggested"></span>${__(
                    "Suggested from last week"
                )}
            </span>
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
                    <div class="card-title text-muted">${__("Forecast")}</div>
                    <div class="wb-summary-value" id="weekly-booking-week-forecast">0:00</div>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <div class="card-title text-muted">${__("Hours Balance")}</div>
                    <div class="wb-summary-value" id="weekly-booking-hours-balance">0:00</div>
                </div>
            </div>
            <div class="card" id="weekly-booking-vacation-card" style="display: none;">
                <div class="card-body">
                    <div class="card-title text-muted">${__("Vacation Remaining")}</div>
                    <div class="wb-summary-value" id="weekly-booking-vacation-remaining">0</div>
                    <div class="wb-summary-status" id="weekly-booking-vacation-status"></div>
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
    const $weekForecast = $summary.find("#weekly-booking-week-forecast");
    const $hoursBalance = $summary.find("#weekly-booking-hours-balance");
    const $vacationCard = $summary.find("#weekly-booking-vacation-card");
    const $vacationRemaining = $summary.find("#weekly-booking-vacation-remaining");
    const $vacationStatus = $summary.find("#weekly-booking-vacation-status");

    const dividerColspan = 2 + 7 + 1;
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
            const rawLabel = project.project_name || project.name;
            const label = escape(rawLabel || "");
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

    function buildSuggestionKey(row) {
        return `${row.project || ""}||${(row.note || "").trim()}`;
    }

    function buildSuggestionRows(previousRows, currentRows) {
        const currentKeys = new Set();
        (currentRows || []).forEach((row) => {
            if (row.project || row.note) {
                currentKeys.add(buildSuggestionKey(row));
            }
        });

        const seen = new Set();
        const suggestions = [];
        (previousRows || []).forEach((row) => {
            const project = row.project || "";
            const note = (row.note || "").trim();
            if (!project && !note) {
                return;
            }
            const key = `${project}||${note}`;
            if (currentKeys.has(key) || seen.has(key)) {
                return;
            }
            seen.add(key);
            suggestions.push({ project, note });
        });
        return suggestions;
    }

    function rowHasHours($row) {
        let hasHours = false;
        $row.find(".wb-hours").each(function () {
            if (parseMinutes($(this).val()) > 0) {
                hasHours = true;
                return false;
            }
        });
        return hasHours;
    }

    function rowHasProjectAndNote($row) {
        const project = $row.find(".wb-project").val();
        const note = ($row.find(".wb-note").val() || "").trim();
        return Boolean(project && note);
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
            if ($row.hasClass("wb-row-suggested")) {
                if (!rowHasHours($row)) {
                    $row.removeClass("wb-row-saved wb-row-unsaved");
                    return;
                }
                $row.removeClass("wb-row-suggested");
            }
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

    function addSectionDividerRow() {
        $rows.append(
            `<tr class="wb-divider-row wb-section-divider" data-row-type="divider"><td colspan="${dividerColspan}"></td></tr>`
        );
    }

    function getDataRows() {
        return $rows.find("tr").not(".wb-divider-row");
    }

    const increaseLabel = __("Increase time");
    const decreaseLabel = __("Decrease time");
    const removeRowLabel = __("Remove row");
    const maxCellMinutes = 24 * 60;

    function getWeekStartValue() {
        return $weekStart.data("weekStart");
    }

    function formatWeekRange(dateStr) {
        const start = moment(dateStr, "YYYY-MM-DD", true);
        if (!start.isValid()) {
            return dateStr || "";
        }
        const end = start.clone().add(6, "days");
        return `${start.format("DD.MM.YYYY")} - ${end.format("DD.MM.YYYY")}`;
    }

    function scrollToDayColumn(dayIndex) {
        if (dayIndex === null || dayIndex === undefined) {
            return;
        }
        const $wrap = $table.find(".weekly-booking-tableWrap");
        const $header = $table.find(`.wb-day-header[data-day="${dayIndex}"]`);
        if (!$wrap.length || !$header.length) {
            return;
        }
        const headerLeft =
            $header.offset().left - $wrap.offset().left + $wrap.scrollLeft();
        const padding = 12;
        $wrap.animate({ scrollLeft: Math.max(0, headerLeft - padding) }, 150);
    }

    function highlightDayColumn(dayIndex) {
        if (dayIndex === null || dayIndex === undefined) {
            return;
        }
        if (highlightTimer) {
            clearTimeout(highlightTimer);
            highlightTimer = null;
        }
        const dayColumnIndex = dayIndex + 3;
        $table.find(".wb-day-highlight").removeClass("wb-day-highlight");
        const $header = $table.find(`.wb-day-header[data-day="${dayIndex}"]`);
        const $bodyCells = $rows.find(
            `tr:not(.wb-divider-row) td:nth-child(${dayColumnIndex})`
        );
        const $footerCells = $table.find(`tfoot td:nth-child(${dayColumnIndex})`);
        $header.addClass("wb-day-highlight");
        $bodyCells.addClass("wb-day-highlight");
        $footerCells.addClass("wb-day-highlight");
        highlightTimer = setTimeout(() => {
            $header.removeClass("wb-day-highlight");
            $bodyCells.removeClass("wb-day-highlight");
            $footerCells.removeClass("wb-day-highlight");
            highlightTimer = null;
        }, 900);
    }

    function initWeekStartPicker() {
        if (!$.fn.datepicker) {
            return;
        }
        let lang = (frappe.boot.user && frappe.boot.user.language) || "en";
        if (!$.fn.datepicker.language[lang]) {
            lang = "en";
        }
        $weekStart.datepicker({
            language: lang,
            autoClose: true,
            dateFormat: "yyyy-mm-dd",
            firstDay: frappe.datetime.get_first_day_of_the_week_index(),
            onSelect: function (formattedDate, date) {
                if (isSyncingWeekStart || !date) {
                    return;
                }
                const selected = moment(date);
                const start = selected.clone().startOf("isoWeek");
                pendingScrollDayIndex = selected.diff(start, "days");
                setWeekStart(start.format("YYYY-MM-DD"));
            },
        });
        weekStartPicker = $weekStart.data("datepicker");
        $weekStart.on("click", function () {
            if (weekStartPicker) {
                weekStartPicker.show();
            }
        });
    }

    function syncWeekStartPicker(dateStr) {
        if (!weekStartPicker || !dateStr) {
            return;
        }
        const date = moment(dateStr, "YYYY-MM-DD", true);
        if (!date.isValid()) {
            return;
        }
        isSyncingWeekStart = true;
        weekStartPicker.selectDate(date.toDate());
        isSyncingWeekStart = false;
    }

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
    function addRow(row = {}, options = {}) {
        const { skipTotals = false, rowType = "data" } = options;
        const deleteCellHtml =
            rowType === "suggestion"
                ? ""
                : `<button type="button" class="btn btn-default btn-sm wb-row-delete" title="${removeRowLabel}" aria-label="${removeRowLabel}">
                        <i class="fa fa-trash"></i>
                    </button>`;
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
                <td class="wb-actions-col wb-actions-cell">
                    ${deleteCellHtml}
                </td>
            </tr>`
        );

        if (rowType) {
            $row.attr("data-row-type", rowType);
        }
        if (rowType === "suggestion") {
            $row.addClass("wb-row-suggested");
        }

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
        updateHolidayMarkers();
    }

    function renderRows(rows, suggestedRows) {
        const suggestions = suggestedRows || [];
        const hasRows = rows && rows.length;
        const hasSuggestions = suggestions.length > 0;
        $rows.empty();
        if (hasRows) {
            rows.forEach((row) => addRow(row, { skipTotals: true }));
        }

        if (hasRows && hasSuggestions) {
            addSectionDividerRow();
        } else if (hasRows) {
            addDividerRow();
        }

        if (hasSuggestions) {
            suggestions.forEach((row) => addRow(row, { skipTotals: true, rowType: "suggestion" }));
            addDividerRow();
        }

        const emptyRows = 3;
        for (let i = 0; i < emptyRows; i++) {
            addRow({}, { skipTotals: true });
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
        const weekStart = getWeekStartValue();
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
        updateHolidayMarkers();
    }

    function setHolidayData(dates, hoursPerDay) {
        state.holiday_dates = Array.isArray(dates) ? dates : [];
        const hours = Number(hoursPerDay);
        state.holiday_hours_per_day = Number.isFinite(hours) ? hours : 0;
    }

    function updateHolidayMarkers() {
        const weekStart = getWeekStartValue();
        const start = weekStart ? moment(weekStart, "YYYY-MM-DD") : null;
        const holidaySet = new Set(state.holiday_dates || []);
        state.holiday_minutes_by_day = {};

        $table.find(".wb-day-holiday-label").remove();
        $table.find(".wb-day-holiday-col").removeClass("wb-day-holiday-col");
        $table.find(".wb-hours").prop("readonly", false);
        $table.find(".wb-step").prop("disabled", false);

        $table.find(".wb-day-header").each(function () {
            const $header = $(this);
            const offset = Number.parseInt($header.data("day"), 10) || 0;
            if (!start || !start.isValid()) {
                return;
            }
            const dateStr = start.clone().add(offset, "days").format("YYYY-MM-DD");
            if (holidaySet.has(dateStr)) {
                const columnIndex = offset + 3;
                const holidayMinutes = Math.round(state.holiday_hours_per_day * 60);
                const holidayLabel = holidayMinutes
                    ? `${__("Feiertag")} ${formatMinutes(holidayMinutes)}`
                    : __("Feiertag");
                $header.prepend(
                    `<div class="wb-day-holiday-label">${holidayLabel}</div>`
                );
                state.holiday_minutes_by_day[offset] = Math.round(
                    state.holiday_hours_per_day * 60
                );
                $table
                    .find(`thead th:nth-child(${columnIndex})`)
                    .addClass("wb-day-holiday-col");
                const $bodyCells = $table
                    .find(`tbody td:nth-child(${columnIndex})`)
                    .addClass("wb-day-holiday-col");
                $bodyCells.find(".wb-hours").prop("readonly", true);
                $bodyCells.find(".wb-step").prop("disabled", true);
                $table
                    .find(`tfoot td:nth-child(${columnIndex})`)
                    .addClass("wb-day-holiday-col");
            } else {
                $header.find(".wb-day-holiday-label").remove();
            }
        });
    }

    function loadWeek() {
        const weekStart = getWeekStartValue();
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
                state.target_period = message.target_period || null;
                state.month_total_minutes = Math.round(Number(message.monthly_total_hours || 0) * 60);
                state.overtime_balance_minutes = Math.round(
                    Number(message.overtime_balance_hours || 0) * 60
                );
                if (message.calendar_week && message.calendar_year) {
                    $calendarWeek.val(`${message.calendar_week} / ${message.calendar_year}`);
                } else {
                    $calendarWeek.val(message.calendar_week || "");
                }
                $weekStart.val(message.period_label || formatWeekRange(weekStart));
                setHolidayData(message.holiday_dates, message.holiday_hours_per_day);
                updateDayHeaders();

                const rows = message.rows || [];
                const suggestions = buildSuggestionRows(message.previous_week_rows || [], rows);
                state.loaded_week_total_minutes = calculateWeekMinutes(rows);
                state.saved_row_counts = buildSavedRowCounts(rows);
                if (!state.projects_loaded) {
                    loadProjects(() => renderRows(rows, suggestions));
                } else {
                    renderRows(rows, suggestions);
                }

                if (message.warning) {
                    frappe.msgprint({
                        title: __("Notice"),
                        message: message.warning,
                        indicator: "orange",
                    });
                }

                updateHoursBalance();
                updateVacationSummary(message.vacation);
                if (pendingScrollDayIndex !== null) {
                    scrollToDayColumn(pendingScrollDayIndex);
                    highlightDayColumn(pendingScrollDayIndex);
                    pendingScrollDayIndex = null;
                }
            },
        });
    }

    function collectRows() {
        const rows = [];
        getDataRows().each(function () {
            const $row = $(this);
            const isSuggested = $row.hasClass("wb-row-suggested");
            const hasHours = rowHasHours($row);
            if (isSuggested && !hasHours) {
                return;
            }
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
        total += getHolidayWeekMinutes();
        return total;
    }

    function getHolidayWeekMinutes() {
        return Object.values(state.holiday_minutes_by_day || {}).reduce(
            (sum, value) => sum + value,
            0
        );
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

        const holidayMinutesByDay = state.holiday_minutes_by_day || {};
        let weekTotal = 0;
        let forecastTotal = 0;
        hourFields.forEach((field, index) => {
            const baseTotal = totals[field.field];
            const holidayMinutes = holidayMinutesByDay[index] || 0;
            const total = baseTotal + holidayMinutes;
            weekTotal += total;

            const isWeekday = index < 5;
            if (isWeekday) {
                if (holidayMinutes || baseTotal) {
                    forecastTotal += total;
                } else {
                    forecastTotal += total + state.holiday_hours_per_day * 60;
                }
            } else {
                forecastTotal += total;
            }

            $table
                .find(`.weekly-booking-total[data-field="${field.field}"]`)
                .text(formatMinutes(total));
        });

        state.weekly_forecast_minutes = Math.round(forecastTotal);
        $weekTotal.text(formatMinutes(weekTotal));
        $weekForecast.text(formatMinutes(state.weekly_forecast_minutes));
        updateWeeklyStatus(weekTotal);
        updateMonthlyStatus(weekTotal);
    }

    function updateMonthlyStatus(weekTotalMinutes) {
        const adjustedMonthTotal =
            state.month_total_minutes + (weekTotalMinutes - state.loaded_week_total_minutes);
        $monthTotal.text(formatMinutes(adjustedMonthTotal));

        if (state.target_period === "Weekly") {
            $monthStatus.text("").hide();
            return;
        }

        $monthStatus.show();
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
        if (state.target_period === "Monthly") {
            $weekStatus.text("").hide();
            return;
        }

        $weekStatus.show();
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

    function formatVacationDays(value) {
        const rounded = Math.round(Number(value || 0) * 100) / 100;
        return Number.isFinite(rounded) ? rounded.toString() : "0";
    }

    function updateHoursBalance() {
        $hoursBalance.text(formatSignedMinutes(state.overtime_balance_minutes));
    }

    function updateVacationSummary(vacation) {
        if (!vacation || !vacation.enabled) {
            $vacationCard.hide();
            return;
        }

        $vacationCard.show();
        if (!vacation.valid) {
            $vacationRemaining.text("--");
            $vacationStatus
                .text(vacation.error || __("Vacation balance is unavailable."))
                .css("color", "#dc3545");
            return;
        }

        const remaining = Number(vacation.remaining_days || 0);
        const used = Number(vacation.used_days || 0);
        const allowance = Number(vacation.allowance_days || 0);

        $vacationRemaining.text(formatVacationDays(remaining));
        $vacationStatus
            .text(
                __("Used {0} of {1} days.", [
                    formatVacationDays(used),
                    formatVacationDays(allowance),
                ])
            )
            .css("color", remaining < 0 ? "#dc3545" : "#6c757d");
    }

    function saveWeek() {
        const weekStart = getWeekStartValue();
        if (!weekStart) {
            frappe.msgprint({
                title: __("Missing Value"),
                message: __("Week start is required."),
                indicator: "red",
            });
            return;
        }

        let hasMissingHours = false;
        getDataRows().each(function () {
            const $row = $(this);
            if ($row.hasClass("wb-row-suggested") && !rowHasHours($row)) {
                return;
            }
            if (rowHasProjectAndNote($row) && !rowHasHours($row)) {
                hasMissingHours = true;
                return false;
            }
        });
        if (hasMissingHours) {
            frappe.msgprint({
                title: __("Missing Value"),
                message: __(
                    "Please enter time for rows that have a project and note."
                ),
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
                if (message.holiday_dates) {
                    setHolidayData(message.holiday_dates, message.holiday_hours_per_day);
                    updateDayHeaders();
                }
                const weekMinutes = calculateWeekMinutes(collectRows());
                state.loaded_week_total_minutes = weekMinutes;
                if (message.monthly_total_hours !== undefined) {
                    state.month_total_minutes = Math.round(
                        Number(message.monthly_total_hours || 0) * 60
                    );
                }
                if (message.overtime_balance_hours !== undefined) {
                    state.overtime_balance_minutes = Math.round(
                        Number(message.overtime_balance_hours || 0) * 60
                    );
                    updateHoursBalance();
                }
                updateTotals();
                state.saved_row_counts = buildSavedRowCounts(collectRows());
                applyRowHighlights();
                if (message.vacation) {
                    updateVacationSummary(message.vacation);
                }

                frappe.show_alert({
                    message: __("Weekly booking saved."),
                    indicator: "green",
                });

                if (message.warning) {
                    frappe.show_alert({
                        message: message.warning,
                        indicator: "orange",
                    });
                }
            },
        });
    }

    function setWeekStart(dateStr) {
        $weekStart.data("weekStart", dateStr);
        $weekStart.val(formatWeekRange(dateStr));
        syncWeekStartPicker(dateStr);
        loadWeek();
    }

    function shiftWeek(days) {
        const current = getWeekStartValue() || frappe.datetime.get_today();
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
    $todayButton.on("click", function () {
        const today = moment(frappe.datetime.get_today());
        const start = today.clone().startOf("isoWeek");
        pendingScrollDayIndex = today.diff(start, "days");
        setWeekStart(start.format("YYYY-MM-DD"));
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
    $rows.on("click", ".wb-row-delete", function () {
        $(this).closest("tr").remove();
        updateTotals();
        applyRowHighlights();
    });
    $rows.on("input change", ".wb-hours", function () {
        applyRowHighlights();
        updateTotals();
    });

    $addRowButton.prop("disabled", true);
    loadProjects();
    renderRows([]);
    initWeekStartPicker();

    const currentWeekStart = moment(frappe.datetime.get_today())
        .startOf("isoWeek")
        .format("YYYY-MM-DD");
    setWeekStart(currentWeekStart);
};
