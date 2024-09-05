app_name = "hrms"
app_title = "Frappe HR"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Modern HR and Payroll Software"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe", "https://github.com/victor-abz/basic.git"]
source_link = "http://github.com/frappe/hrms"


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hrms/css/hrms.css"
app_include_js = [
    "hrms.bundle.js",
]

fixtures=[
    "Workflow"
]
app_include_css = "hrms.bundle.css"

# website

# include js, css files in header of web template
# web_include_css = "/assets/hrms/css/hrms.css"
# web_include_js = "/assets/hrms/js/hrms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hrms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {
#     "Company": "public/js/erpnext/company.js",
#     "Department": "public/js/erpnext/department.js",
#     "Timesheet": "public/js/erpnext/timesheet.js",
# }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

calendars = ["Leave Application"]

# Generators
# ----------

# automatically create page for each record of this doctype
website_generators = ["Job Opening"]

website_route_rules = [
    {"from_route": "/hrms/<path:app_path>", "to_route": "hrms"},
]
# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        "hrms.utils.get_country",
    ],
}

# Installation
# ------------

# before_install = "hrms.install.before_install"
after_install = "hrms.install.after_install"
after_migrate = "basic.setup.update_select_perm_after_install"

# Uninstallation
# ------------

before_uninstall = "hrms.uninstall.before_uninstall"
# after_uninstall = "hrms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hrms.utils.before_app_install"
after_app_install = "basic.setup.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

before_app_uninstall = "basic.setup.before_app_uninstall"
# after_app_uninstall = "hrms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hrms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

has_upload_permission = {"Employee": "basic.setup.doctype.employee.employee.has_upload_permission"}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Employee": "hrms.overrides.employee_master.EmployeeMaster",
    "Timesheet": "hrms.overrides.employee_timesheet.EmployeeTimesheet"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "User": {
        "validate": "basic.setup.doctype.employee.employee.validate_employee_role",
        "on_update": "basic.setup.doctype.employee.employee.update_user_permissions",
    },
    "Company": {
        "on_update": [
            "hrms.overrides.company.make_company_fixtures",
            # "hrms.overrides.company.set_default_hr_accounts",
        ],
    },
    "Holiday List": {
        "on_update": "hrms.utils.holiday_list.invalidate_cache",
        "on_trash": "hrms.utils.holiday_list.invalidate_cache",
    },
    "Timesheet": {"validate": "hrms.hr.utils.validate_active_employee"},
    "Employee": {
        "validate": "hrms.overrides.employee_master.validate_onboarding_process",
        "on_update": [
            "hrms.overrides.employee_master.update_approver_role",
            "hrms.overrides.employee_master.publish_update",
        ],
        "after_insert": "hrms.overrides.employee_master.update_job_applicant_and_offer",
        "on_trash": "hrms.overrides.employee_master.update_employee_transfer",
        "after_delete": "hrms.overrides.employee_master.publish_update",
    },
    # "Project": {
    #     "validate": "basic.controllers.employee_boarding_controller.update_employee_boarding_status"
    # },
    "Task": {"on_update": "basic.controllers.employee_boarding_controller.update_task"},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "all": [
        "hrms.hr.doctype.interview.interview.send_interview_reminder",
    ],
    "hourly": [
        "hrms.hr.doctype.daily_work_summary_group.daily_work_summary_group.trigger_emails",
    ],
    "hourly_long": [
        "hrms.hr.doctype.shift_type.shift_type.process_auto_attendance_for_all_shifts",
    ],
    "daily": [
        "hrms.controllers.employee_reminders.send_birthday_reminders",
        "hrms.controllers.employee_reminders.send_work_anniversary_reminders",
        "hrms.hr.doctype.daily_work_summary_group.daily_work_summary_group.send_summary",
        "hrms.hr.doctype.interview.interview.send_daily_feedback_reminder",
        "hrms.hr.doctype.job_opening.job_opening.close_expired_job_openings",
    ],
    "daily_long": [
        "hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry.process_expired_allocation",
        "hrms.hr.utils.generate_leave_encashment",
        "hrms.hr.utils.allocate_earned_leaves",
    ],
    "weekly": ["hrms.controllers.employee_reminders.send_reminders_in_advance_weekly"],
    "monthly": ["hrms.controllers.employee_reminders.send_reminders_in_advance_monthly"],
}

# advance_payment_doctypes = ["Gratuity", "Employee Advance"]

invoice_doctypes = ["Expense Claim"]

period_closing_doctypes = ["Payroll Entry"]


bank_reconciliation_doctypes = ["Expense Claim"]

# Testing
# -------

before_tests = "hrms.tests.test_utils.before_tests"

# Overriding Methods
# -----------------------------

# get matching queries for Bank Reconciliation
get_matching_queries = "hrms.hr.utils.get_matching_queries"


# ERPNext doctypes for Global Search
global_search_doctypes = {
    "Default": [
        {"doctype": "Salary Slip", "index": 19},
        {"doctype": "Leave Application", "index": 20},
        {"doctype": "Expense Claim", "index": 21},
        {"doctype": "Employee Grade", "index": 37},
        {"doctype": "Job Opening", "index": 39},
        {"doctype": "Job Applicant", "index": 40},
        {"doctype": "Job Offer", "index": 41},
        {"doctype": "Salary Structure Assignment", "index": 42},
        {"doctype": "Appraisal", "index": 43},
    ],
}

# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hrms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
    "Employee": "hrms.overrides.dashboard_overrides.get_dashboard_for_employee",
    "Holiday List": "hrms.overrides.dashboard_overrides.get_dashboard_for_holiday_list",
    "Task": "hrms.overrides.dashboard_overrides.get_dashboard_for_project",
    "Timesheet": "hrms.overrides.dashboard_overrides.get_dashboard_for_timesheet",
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


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
# 	"hrms.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
