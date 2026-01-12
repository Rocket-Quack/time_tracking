frappe.ui.form.on("Time Tracking Holiday List", {
    refresh(frm) {
        set_holiday_list_name(frm);
    },
    year(frm) {
        set_holiday_list_name(frm);
    },
});

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
