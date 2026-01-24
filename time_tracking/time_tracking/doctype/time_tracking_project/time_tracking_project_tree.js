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
        const rawName = node.title || node.label || "";
        const name = frappe.utils.escape_html(rawName ? __(rawName) : "");
        const data = node.data || {};
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
                    `<span class="${statusClass}">${frappe.utils.escape_html(
                        __(status)
                    )}</span>`
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
            `.tree-link .tt-project-meta { margin-left: 6px; font-size: 11px; color: #6c757d; }
            .tree-link .tt-status-under { color: #0d6efd; }
            .tree-link .tt-status-on { color: #28a745; }
            .tree-link .tt-status-over { color: #dc3545; }
            .tree-link .tt-status-badge {
                display: inline-block;
                padding: 1px 6px;
                border-radius: 10px;
                font-size: 10px;
                line-height: 1.4;
                border: 1px solid transparent;
            }
            .tree-link .tt-status-active {
                color: #1e7e34;
                background: #e6f4ea;
                border-color: #c3e6cb;
            }
            .tree-link .tt-status-inactive {
                color: #a71d2a;
                background: #f8d7da;
                border-color: #f5c6cb;
            }
            .tree-link .tt-booking-on {
                color: #1f6f2c;
                background: #e8f6ef;
                border-color: #c6e9d8;
            }
            .tree-link .tt-booking-off {
                color: #a94442;
                background: #f2dede;
                border-color: #ebccd1;
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
