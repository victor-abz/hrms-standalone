# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class PermissionApplication(Document):
    def validate(self):
        self.validate_time()

    def validate_time(self):
        # Ensure arriving time is not less than leaving time
        if self.date_and_time_of_arriving < self.date_and_time_of_leaving:
            frappe.throw("The date and time of arriving cannot be before the date and time of leaving.")
        if self.date_and_time_of_leaving < nowdate():
            frappe.throw("the date can't be in the past.")
