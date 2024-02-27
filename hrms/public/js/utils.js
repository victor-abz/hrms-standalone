frappe.provide('hrms');
frappe.provide('hrms.utils');

$.extend(hrms, {
  proceed_save_with_reminders_frequency_change: () => {
    frappe.ui.hide_open_dialog();
    frappe.call({
      method:
        'hrms.hr.doctype.hr_settings.hr_settings.set_proceed_with_frequency_change',
      callback: () => {
        cur_frm.save();
      },
    });
  },

  set_payroll_frequency_to_null: (frm) => {
    if (cint(frm.doc.salary_slip_based_on_timesheet)) {
      frm.set_value('payroll_frequency', '');
    }
  },

  get_current_employee: async (frm) => {
    const employee = (
      await frappe.db.get_value(
        'Employee',
        { user_id: frappe.session.user },
        'name'
      )
    )?.message?.name;

    return employee;
  },

  get_currency: function (company) {
    if (!company && cur_frm) company = cur_frm.doc.company;
    if (company)
      return (
        frappe.get_doc(':Company', company)?.default_currency ||
        frappe.boot.sysdefaults.currency
      );
    else return frappe.boot.sysdefaults.currency;
  },

  get_presentation_currency_list: () => {
    const docs = frappe.boot.docs;
    let currency_list = docs
      .filter((d) => d.doctype === ':Currency')
      .map((d) => d.name);
    currency_list.unshift('');
    return currency_list;
  },

  toggle_naming_series: function () {
    if (cur_frm.fields_dict.naming_series) {
      cur_frm.toggle_display(
        'naming_series',
        cur_frm.doc.__islocal ? true : false
      );
    }
  },
});

$.extend(hrms.utils, {
  get_party_name: function (party_type) {
    var dict = {
      Customer: 'customer_name',
      Supplier: 'supplier_name',
      Employee: 'employee_name',
      Member: 'member_name',
    };
    return dict[party_type];
  },

  copy_value_in_all_rows: function (doc, dt, dn, table_fieldname, fieldname) {
    var d = locals[dt][dn];
    if (d[fieldname]) {
      var cl = doc[table_fieldname] || [];
      for (var i = 0; i < cl.length; i++) {
        if (!cl[i][fieldname]) cl[i][fieldname] = d[fieldname];
      }
    }
    refresh_field(table_fieldname);
  },

  get_tree_options: function (option) {
    // get valid options for tree based on user permission & locals dict
    let unscrub_option = frappe.model.unscrub(option);
    let user_permission = frappe.defaults.get_user_permissions();
    let options;

    if (user_permission && user_permission[unscrub_option]) {
      options = user_permission[unscrub_option].map((perm) => perm.doc);
    } else {
      options = $.map(locals[`:${unscrub_option}`], function (c) {
        return c.name;
      }).sort();
    }

    // filter unique values, as there may be multiple user permissions for any value
    return options.filter(
      (value, index, self) => self.indexOf(value) === index
    );
  },
  get_tree_default: function (option) {
    // set default for a field based on user permission
    let options = this.get_tree_options(option);
    if (options.includes(frappe.defaults.get_default(option))) {
      return frappe.defaults.get_default(option);
    } else {
      return options[0];
    }
  },
  overrides_parent_value_in_all_rows: function (
    doc,
    dt,
    dn,
    table_fieldname,
    fieldname,
    parent_fieldname
  ) {
    if (doc[parent_fieldname]) {
      let cl = doc[table_fieldname] || [];
      for (let i = 0; i < cl.length; i++) {
        cl[i][fieldname] = doc[parent_fieldname];
      }
      frappe.refresh_field(table_fieldname);
    }
  },
  create_new_doc: function (doctype, update_fields) {
    frappe.model.with_doctype(doctype, function () {
      var new_doc = frappe.model.get_new_doc(doctype);
      for (let [key, value] of Object.entries(update_fields)) {
        new_doc[key] = value;
      }
      frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
    });
  },
  get_terms: function (tc_name, doc, callback) {
    if (tc_name) {
      return frappe.call({
        method:
          'basic.setup.doctype.terms_and_conditions.terms_and_conditions.get_terms_and_conditions',
        args: {
          template_name: tc_name,
          doc: doc,
        },
        callback: function (r) {
          callback(r);
        },
      });
    }
  },
});
