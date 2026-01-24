frappe.ui.form.on("Time Tracking Project", {
    refresh(frm) {
        if (frm.is_quick_entry) {
            ensureQuickEntryNotice(frm);
        }
    },
});

function ensureQuickEntryNotice(frm) {
    if (!frm.fields_dict.assignment_mode || !frm.fields_dict.allowed_users) {
        return;
    }
    if (frm.__tt_assignment_notice_added) {
        return;
    }
    frm.__tt_assignment_notice_added = true;

    const wrapper = $(frm.fields_dict.allowed_users.wrapper);
    if (!wrapper.length) {
        return;
    }

    const message = __(
        "Restricted projects require allowed users to be added in the full form."
    );
    const banner = $(`
        <div class="alert alert-warning tt-quick-entry-assignment-note" style="margin-top: 8px;">
            ${message}
        </div>
    `);
    banner.hide();
    wrapper.prepend(banner);

    const toggleBanner = () => {
        const mode = (frm.doc.assignment_mode || "").trim();
        if (mode === "Restricted") {
            banner.show();
        } else {
            banner.hide();
        }
    };

    frm.on("assignment_mode", toggleBanner);
    toggleBanner();
}
