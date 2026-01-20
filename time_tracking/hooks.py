app_name = "time_tracking"
app_title = "Time Tracking"
app_publisher = "RocketQuackIT"
app_description = "Project-based time tracking for companies: log billable hours, generate timesheets, and export reports for invoicing."
app_email = "contact@rocketquack.eu"
app_license = "mit"
app_icon = "fa fa-clock-o"
app_color = "#0f6e74"
app_logo_url = "/assets/time_tracking/images/time-tracking-logo.png"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "time_tracking",
		"logo": "/assets/time_tracking/images/time-tracking-logo.png",
		"title": "Time Tracking",
		"route": "/app/time-tracking",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/time_tracking/css/time_tracking.css"
# app_include_js = "/assets/time_tracking/js/time_tracking.js"

# include js, css files in header of web template
# web_include_css = "/assets/time_tracking/css/time_tracking.css"
# web_include_js = "/assets/time_tracking/js/time_tracking.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "time_tracking/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"User": "public/js/user.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "time_tracking/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "time_tracking.utils.jinja_methods",
# 	"filters": "time_tracking.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "time_tracking.install.after_install"
after_migrate = "time_tracking.install.after_migrate"

# Fixtures
# --------
# Fixtures are managed via JSON files in /fixtures and synced on migrate.
fixtures = [
	{
		"dt": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Time Tracking Employee",
					"Time Tracking Admin",
					"Time Tracking Manager",
				],
			]
		],
	},
	{"dt": "Workspace", "filters": [["name", "=", "Time Tracking"]]},
	{"dt": "Custom HTML Block", "filters": [["module", "=", "Time Tracking"]]},
]

# Uninstallation
# ------------

# before_uninstall = "time_tracking.uninstall.before_uninstall"
# after_uninstall = "time_tracking.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "time_tracking.utils.before_app_install"
# after_app_install = "time_tracking.utils.after_app_install"

# after_migrate = "time_tracking.install.after_migrate"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "time_tracking.utils.before_app_uninstall"
# after_app_uninstall = "time_tracking.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "time_tracking.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Time Tracking Profile": (
		"time_tracking.time_tracking.doctype.time_tracking_profile.time_tracking_profile"
		".get_permission_query_conditions"
	),
}

has_permission = {
	"Time Tracking Profile": (
		"time_tracking.time_tracking.doctype.time_tracking_profile.time_tracking_profile.has_permission"
	),
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Time Booking": {
		"after_insert": [
			(
				"time_tracking.time_tracking.doctype.time_tracking_project"
				".time_tracking_project.handle_time_booking_insert"
			),
			"time_tracking.time_tracking.overtime_utils.handle_time_booking_change",
			"time_tracking.time_tracking.vacation_utils.handle_vacation_booking_change",
		],
		"on_update": [
			(
				"time_tracking.time_tracking.doctype.time_tracking_project"
				".time_tracking_project.handle_time_booking_update"
			),
			"time_tracking.time_tracking.overtime_utils.handle_time_booking_change",
			"time_tracking.time_tracking.vacation_utils.handle_vacation_booking_change",
		],
		"on_trash": [
			(
				"time_tracking.time_tracking.doctype.time_tracking_project"
				".time_tracking_project.handle_time_booking_trash"
			),
			"time_tracking.time_tracking.overtime_utils.handle_time_booking_change",
			"time_tracking.time_tracking.vacation_utils.handle_vacation_booking_change",
		],
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"time_tracking.time_tracking.notifications.send_booking_reminders",
	],
}

# Testing
# -------

# before_tests = "time_tracking.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "time_tracking.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "time_tracking.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["time_tracking.install.ensure_root_project"]
# after_request = ["time_tracking.utils.after_request"]

# Job Events
# ----------
# before_job = ["time_tracking.utils.before_job"]
# after_job = ["time_tracking.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"time_tracking.auth.validate"
# ]

# login
on_login = "time_tracking.utils.ensure_default_workspace"

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
