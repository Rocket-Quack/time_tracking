import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class TimeTrackingProfile(Document):
    def validate(self):
        self._validate_overtime_balance()

    def _validate_overtime_balance(self):
        if _is_admin():
            return

        previous = self.get_doc_before_save()
        if previous and flt(previous.overtime_balance_hours) != flt(self.overtime_balance_hours):
            frappe.throw(_("Overtime balance can only be updated by an admin."))


def _is_admin(user=None):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "Time Tracking Admin" in roles


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    if _is_admin(user):
        return ""
    return f"`tabTime Tracking Profile`.`user` = {frappe.db.escape(user)}"


def has_permission(doc, user):
    if not user:
        user = frappe.session.user
    if _is_admin(user):
        return True
    if not doc:
        return False
    return doc.user == user
