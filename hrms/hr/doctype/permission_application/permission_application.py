# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

from frappe.model.document import Document
from frappe.utils import nowdate, get_datetime
from datetime import datetime

class PermissionApplication(Document):
    def validate(self):
        self.validate_time()

    def validate_time(self):
        # Convert fields to datetime objects
        date_and_time_of_arriving = get_datetime(self.date_and_time_of_arriving)
        date_and_time_of_leaving = get_datetime(self.date_and_time_of_leaving)
        current_date = get_datetime(nowdate())

        # Ensure arriving time is not less than leaving time
        if date_and_time_of_arriving < date_and_time_of_leaving:
            frappe.throw("The date and time of arriving cannot be before the date and time of leaving.")

        # Ensure leaving time is not in the past
        if date_and_time_of_leaving < current_date:
            frappe.throw("The date and time of leaving cannot be in the past.")