// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Permission Application", {
	refresh(frm) {

        frm.trigger('set_employee');
	},

    setup: function (frm) {
    
        frm.set_query('employee', hrms.queries.employee);
      },
    
      async set_employee(frm) {
        if (frm.doc.employee) return;
    
        const employee = await hrms.get_current_employee(frm);
        if (employee) {
          frm.set_value('employee', employee);
        }
      },
});
