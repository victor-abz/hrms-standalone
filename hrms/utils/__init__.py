import functools
import math
from collections.abc import Generator
from datetime import timedelta

import requests
from pypika import Order
from pypika.terms import ExistsCriterion

import frappe
from frappe import _
from frappe.query_builder.utils import DocType
from frappe.utils import (
    add_days,
    add_months,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_first_day,
    getdate,
    today,
)

country_info = {}


@frappe.whitelist(allow_guest=True)
def get_country(fields=None):
    global country_info
    ip = frappe.local.request_ip

    if ip not in country_info:
        fields = ["countryCode", "country", "regionName", "city"]
        res = requests.get(
            "https://pro.ip-api.com/json/{ip}?key={key}&fields={fields}".format(
                ip=ip, key=frappe.conf.get("ip-api-key"), fields=",".join(fields)
            )
        )

        try:
            country_info[ip] = res.json()

        except Exception:
            country_info[ip] = {}

    return country_info[ip]


def get_date_range(start_date: str, end_date: str) -> list[str]:
    """returns list of dates between start and end dates"""
    no_of_days = date_diff(end_date, start_date) + 1
    return [add_days(start_date, i) for i in range(no_of_days)]


def generate_date_range(
    start_date: str, end_date: str, reverse: bool = False
) -> Generator[str, None, None]:
    no_of_days = date_diff(end_date, start_date) + 1

    date_field = end_date if reverse else start_date
    direction = -1 if reverse else 1

    for n in range(no_of_days):
        yield add_days(date_field, direction * n)


def get_employee_email(employee_id: str) -> str | None:
    employee_emails = frappe.db.get_value(
        "Employee",
        employee_id,
        ["prefered_email", "user_id", "company_email", "personal_email"],
        as_dict=True,
    )

    return (
        employee_emails.prefered_email
        or employee_emails.user_id
        or employee_emails.company_email
        or employee_emails.personal_email
    )


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def get_period_list(
    from_fiscal_year,
    to_fiscal_year,
    period_start_date,
    period_end_date,
    filter_based_on,
    periodicity,
    accumulated_values=False,
    company=None,
    reset_period_on_fy_change=True,
    ignore_fiscal_year=False,
):
    """Get a list of dict {"from_date": from_date, "to_date": to_date, "key": key, "label": label}
    Periodicity can be (Yearly, Quarterly, Monthly)"""

    if filter_based_on == "Fiscal Year":
        fiscal_year = get_fiscal_year_data(from_fiscal_year, to_fiscal_year)
        validate_fiscal_year(fiscal_year, from_fiscal_year, to_fiscal_year)
        year_start_date = getdate(fiscal_year.year_start_date)
        year_end_date = getdate(fiscal_year.year_end_date)
    else:
        validate_dates(period_start_date, period_end_date)
        year_start_date = getdate(period_start_date)
        year_end_date = getdate(period_end_date)

    year_end_date = getdate(today()) if year_end_date > getdate(today()) else year_end_date

    months_to_add = {"Yearly": 12, "Half-Yearly": 6, "Quarterly": 3, "Monthly": 1}[periodicity]

    period_list = []

    start_date = year_start_date
    months = get_months(year_start_date, year_end_date)

    for i in range(cint(math.ceil(months / months_to_add))):
        period = frappe._dict({"from_date": start_date})

        if i == 0 and filter_based_on == "Date Range":
            to_date = add_months(get_first_day(start_date), months_to_add)
        else:
            to_date = add_months(start_date, months_to_add)

        start_date = to_date

        # Subtract one day from to_date, as it may be first day in next fiscal year or month
        to_date = add_days(to_date, -1)

        if to_date <= year_end_date:
            # the normal case
            period.to_date = to_date
        else:
            # if a fiscal year ends before a 12 month period
            period.to_date = year_end_date

        if not ignore_fiscal_year:
            pass
            # period.to_date_fiscal_year = get_fiscal_year(period.to_date, company=company)[0]
            # period.from_date_fiscal_year_start_date = get_fiscal_year(
            #     period.from_date, company=company
            # )[1]

        period_list.append(period)

        if period.to_date == year_end_date:
            break

    # common processing
    for opts in period_list:
        key = opts["to_date"].strftime("%b_%Y").lower()
        if periodicity == "Monthly" and not accumulated_values:
            label = formatdate(opts["to_date"], "MMM YYYY")
        else:
            if not accumulated_values:
                label = get_label(periodicity, opts["from_date"], opts["to_date"])
            else:
                if reset_period_on_fy_change:
                    label = get_label(
                        periodicity, opts.from_date_fiscal_year_start_date, opts["to_date"]
                    )
                else:
                    label = get_label(periodicity, period_list[0].from_date, opts["to_date"])

        opts.update(
            {
                "key": key.replace(" ", "_").replace("-", "_"),
                "label": label,
                "year_start_date": year_start_date,
                "year_end_date": year_end_date,
            }
        )

    return period_list


def get_label(periodicity, from_date, to_date):
    if periodicity == "Yearly":
        if formatdate(from_date, "YYYY") == formatdate(to_date, "YYYY"):
            label = formatdate(from_date, "YYYY")
        else:
            label = formatdate(from_date, "YYYY") + "-" + formatdate(to_date, "YYYY")
    else:
        label = formatdate(from_date, "MMM YY") + "-" + formatdate(to_date, "MMM YY")

    return label


def get_fiscal_year_data(from_fiscal_year, to_fiscal_year):
    fiscal_year = frappe.db.sql(
        """select min(year_start_date) as year_start_date,
		max(year_end_date) as year_end_date from `tabFiscal Year` where
		name between %(from_fiscal_year)s and %(to_fiscal_year)s""",
        {"from_fiscal_year": from_fiscal_year, "to_fiscal_year": to_fiscal_year},
        as_dict=1,
    )

    return fiscal_year[0] if fiscal_year else {}


def validate_fiscal_year(fiscal_year, from_fiscal_year, to_fiscal_year):
    if not fiscal_year.get("year_start_date") or not fiscal_year.get("year_end_date"):
        frappe.throw(_("Start Year and End Year are mandatory"))

    if getdate(fiscal_year.get("year_end_date")) < getdate(fiscal_year.get("year_start_date")):
        frappe.throw(_("End Year cannot be before Start Year"))


def validate_dates(from_date, to_date):
    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are mandatory"))

    if to_date < from_date:
        frappe.throw(_("To Date cannot be less than From Date"))


def get_months(start_date, end_date):
    diff = (12 * end_date.year + end_date.month) - (12 * start_date.year + start_date.month)
    return diff + 1


def get_accounting_dimensions(as_list=True, filters=None):
    if not filters:
        filters = {"disabled": 0}

    if frappe.flags.accounting_dimensions is None:
        frappe.flags.accounting_dimensions = frappe.get_all(
            "Accounting Dimension",
            fields=["label", "fieldname", "disabled", "document_type"],
            filters=filters,
        )

    if as_list:
        return [d.fieldname for d in frappe.flags.accounting_dimensions]
    else:
        return frappe.flags.accounting_dimensions


def get_account_currency(account):
    """Helper function to get account currency"""
    if not account:
        return

    def generator():
        account_currency, company = frappe.get_cached_value(
            "Account", account, ["account_currency", "company"]
        )
        if not account_currency:
            account_currency = frappe.get_cached_value("Company", company, "default_currency")

        return account_currency

    return frappe.local_cache("account_currency", account, generator)


@frappe.whitelist()
def get_fiscal_year(
    date=None,
    fiscal_year=None,
    label="Date",
    verbose=1,
    company=None,
    as_dict=False,
    boolean=False,
):
    if isinstance(boolean, str):
        boolean = frappe.json.loads(boolean)

    fiscal_years = get_fiscal_years(
        date, fiscal_year, label, verbose, company, as_dict=as_dict, boolean=boolean
    )
    if boolean:
        return fiscal_years
    else:
        return fiscal_years[0]


def get_fiscal_years(
    transaction_date=None,
    fiscal_year=None,
    label="Date",
    verbose=1,
    company=None,
    as_dict=False,
    boolean=False,
):
    fiscal_years = frappe.cache().hget("fiscal_years", company) or []

    if not fiscal_years:
        # if year start date is 2012-04-01, year end date should be 2013-03-31 (hence subdate)
        FY = DocType("Fiscal Year")

        query = (
            frappe.qb.from_(FY)
            .select(FY.name, FY.year_start_date, FY.year_end_date)
            .where(FY.disabled == 0)
        )

        if fiscal_year:
            query = query.where(FY.name == fiscal_year)

        if company:
            FYC = DocType("Fiscal Year Company")
            query = query.where(
                ExistsCriterion(
                    frappe.qb.from_(FYC).select(FYC.name).where(FYC.parent == FY.name)
                ).negate()
                | ExistsCriterion(
                    frappe.qb.from_(FYC)
                    .select(FYC.company)
                    .where(FYC.parent == FY.name)
                    .where(FYC.company == company)
                )
            )

        query = query.orderby(FY.year_start_date, order=Order.desc)
        fiscal_years = query.run(as_dict=True)

        frappe.cache().hset("fiscal_years", company, fiscal_years)

    if not transaction_date and not fiscal_year:
        return fiscal_years

    if transaction_date:
        transaction_date = getdate(transaction_date)

    for fy in fiscal_years:
        matched = False
        if fiscal_year and fy.name == fiscal_year:
            matched = True

        if (
            transaction_date
            and getdate(fy.year_start_date) <= transaction_date
            and getdate(fy.year_end_date) >= transaction_date
        ):
            matched = True

        if matched:
            if as_dict:
                return (fy,)
            else:
                return ((fy.name, fy.year_start_date, fy.year_end_date),)

    error_msg = _("""{0} {1} is not in any active Fiscal Year""").format(
        label, formatdate(transaction_date)
    )
    if company:
        error_msg = _("""{0} for {1}""").format(error_msg, frappe.bold(company))

    if boolean:
        return False

    if verbose == 1:
        frappe.msgprint(error_msg)

    raise FiscalYearError(error_msg)


class FiscalYearError(frappe.ValidationError):
    pass


class PaymentEntryUnlinkError(frappe.ValidationError):
    pass
