import frappe
from frappe.model.document import Document

class TimeTrackingProfile(Document):
    pass


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return ""
    return f"`tabTime Tracking Profile`.`user` = {frappe.db.escape(user)}"


def has_permission(doc, user):
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return True
    if not doc:
        return False
    return doc.user == user
