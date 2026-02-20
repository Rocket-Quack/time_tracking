frappe.treeview_settings["Time Tracking Project"] = {
	get_tree_nodes:
		"time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project.get_project_tree_nodes",
	add_tree_node:
		"time_tracking.time_tracking.doctype.time_tracking_project.time_tracking_project.add_node",
	get_tree_root: false,
	onload: function (treeview) {
		treeview.root_label = __(treeview.doctype);
		treeview.root_value = "";
		treeview.make_tree();
	},
	get_label: function (node) {
		const data = node.data || {};
		const rawName = data.project_name || node.title || node.label || "";
		const name = frappe.utils.escape_html(rawName ? __(rawName) : "");
		const parts = [];

		const projectStatus = (data.project_status || "").trim() || "Active";
		const statusClass =
			projectStatus === "Inactive" ? "tt-status-inactive" : "tt-status-active";
		parts.push(
			`<span class="tt-status-badge ${statusClass}">${frappe.utils.escape_html(
				__(projectStatus)
			)}</span>`
		);

		const notBookable = Number(data.not_bookable) === 1;
		const bookingLabel = notBookable ? __("Not Bookable") : __("Bookable");
		const bookingClass = notBookable ? "tt-booking-off" : "tt-booking-on";
		parts.push(
			`<span class="tt-status-badge ${bookingClass}">${frappe.utils.escape_html(
				bookingLabel
			)}</span>`
		);

		if (
			frappe.user.has_role("System Manager") ||
			frappe.user.has_role("Time Tracking Admin") ||
			frappe.user.has_role("Time Tracking Manager")
		) {
			const hoursBudget = Number(data.total_budget_hours || data.budget_hours || 0);
			const amountBudget = Number(data.total_budget_amount || data.budget_amount || 0);
			const status =
				data.budget_status || getComputedStatus(data, hoursBudget, amountBudget);

			if (hoursBudget > 0) {
				parts.push(`${formatPercent(data.budget_hours_percent)}% h`);
			}

			if (amountBudget > 0) {
				parts.push(`${formatPercent(data.budget_amount_percent)}% EUR`);
			}

			if (status) {
				const statusClass = getStatusClass(status);
				parts.push(
					`<span class="${statusClass}">${frappe.utils.escape_html(__(status))}</span>`
				);
			}
		}

		if (!parts.length) {
			return name;
		}

		return `${name} <span class="tt-project-meta">• ${parts.join(" • ")}</span>`;
	},
	onrender: function () {
		if (document.getElementById("tt-project-tree-style")) {
			return;
		}
		frappe.dom.set_style(
			`:root {
                --tt-tree-muted: var(--text-muted, #6c757d);
                --tt-tree-status-under: #2f80ed;
                --tt-tree-status-on: #2f9e5f;
                --tt-tree-status-over: #d64545;
                --tt-tree-badge-active-text: #1f7d46;
                --tt-tree-badge-active-bg: #e8f6ef;
                --tt-tree-badge-active-border: #c6e9d8;
                --tt-tree-badge-inactive-text: #a94442;
                --tt-tree-badge-inactive-bg: #f8d7da;
                --tt-tree-badge-inactive-border: #ebccd1;
                --tt-tree-badge-booking-on-text: #1f6f2c;
                --tt-tree-badge-booking-on-bg: #e8f6ef;
                --tt-tree-badge-booking-on-border: #c6e9d8;
                --tt-tree-badge-booking-off-text: #a94442;
                --tt-tree-badge-booking-off-bg: #f2dede;
                --tt-tree-badge-booking-off-border: #ebccd1;
            }
            body[data-theme="dark"] {
                --tt-tree-muted: #9fb0c2;
                --tt-tree-status-under: #74b7ff;
                --tt-tree-status-on: #6fdaa0;
                --tt-tree-status-over: #ff8f8f;
                --tt-tree-badge-active-text: #6fdaa0;
                --tt-tree-badge-active-bg: #1f3b2e;
                --tt-tree-badge-active-border: #2d5843;
                --tt-tree-badge-inactive-text: #ff9c9c;
                --tt-tree-badge-inactive-bg: #4a2a2a;
                --tt-tree-badge-inactive-border: #704040;
                --tt-tree-badge-booking-on-text: #8fe3b6;
                --tt-tree-badge-booking-on-bg: #1f3b2e;
                --tt-tree-badge-booking-on-border: #2d5843;
                --tt-tree-badge-booking-off-text: #ffb3b3;
                --tt-tree-badge-booking-off-bg: #4a2a2a;
                --tt-tree-badge-booking-off-border: #704040;
            }
            .tree-link .tt-project-meta { margin-left: 6px; font-size: 11px; color: var(--tt-tree-muted); }
            .tree-link .tt-status-under { color: var(--tt-tree-status-under); }
            .tree-link .tt-status-on { color: var(--tt-tree-status-on); }
            .tree-link .tt-status-over { color: var(--tt-tree-status-over); }
            .tree-link .tt-status-badge {
                display: inline-block;
                padding: 1px 6px;
                border-radius: 10px;
                font-size: 10px;
                line-height: 1.4;
                border: 1px solid transparent;
            }
            .tree-link .tt-status-active {
                color: var(--tt-tree-badge-active-text);
                background: var(--tt-tree-badge-active-bg);
                border-color: var(--tt-tree-badge-active-border);
            }
            .tree-link .tt-status-inactive {
                color: var(--tt-tree-badge-inactive-text);
                background: var(--tt-tree-badge-inactive-bg);
                border-color: var(--tt-tree-badge-inactive-border);
            }
            .tree-link .tt-booking-on {
                color: var(--tt-tree-badge-booking-on-text);
                background: var(--tt-tree-badge-booking-on-bg);
                border-color: var(--tt-tree-badge-booking-on-border);
            }
            .tree-link .tt-booking-off {
                color: var(--tt-tree-badge-booking-off-text);
                background: var(--tt-tree-badge-booking-off-bg);
                border-color: var(--tt-tree-badge-booking-off-border);
            }`,
			"tt-project-tree-style"
		);
	},
};

function formatPercent(value) {
	const number = Number(value || 0);
	if (!Number.isFinite(number)) {
		return "0";
	}
	const rounded = Math.round(number * 10) / 10;
	return Number.isInteger(rounded) ? rounded.toString() : rounded.toFixed(1);
}

function getStatusClass(status) {
	if (status === "Over Budget") {
		return "tt-status-over";
	}
	if (status === "On Budget") {
		return "tt-status-on";
	}
	return "tt-status-under";
}

function getComputedStatus(data, hoursBudget, amountBudget) {
	if (!(hoursBudget > 0 || amountBudget > 0)) {
		return "";
	}

	const percents = [];
	if (hoursBudget > 0) {
		percents.push(Number(data.budget_hours_percent || 0));
	}
	if (amountBudget > 0) {
		percents.push(Number(data.budget_amount_percent || 0));
	}

	const maxPercent = percents.length ? Math.max(...percents) : 0;
	if (maxPercent > 100) {
		return "Over Budget";
	}
	if (maxPercent >= 100) {
		return "On Budget";
	}
	return "Under Budget";
}
