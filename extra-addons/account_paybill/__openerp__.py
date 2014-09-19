# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Pay Bills with Expenses",
    "version": "1.0",
    "description": """
Register and pay expenses with multiple invoices
================================================

The management of expenses with multiple invoice, enables you to track your documented expenses with receipts or invoices allowing their accouting in easy and quickly way.
OpenERP has another method to track and register the expenses using only one receipt voucher. But in this way this module will register and manager expense report with multples receipt vouchers (or invoices) and one payment.

Key Features
------------
* Manage Pay Bills with multiple receipts or invoices
* Register multiple invoices and these payment in one step
* Allow to register the accounting in easy way
* Optimize the expense report procedure

Dashboard / Reports for Expenses with Receipts will include:
------------------------------------------------------------
* Pay bill with multiple invoices report
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Financial",
    "depends": [
        "account_voucher",
        "account_expense",
        "hr_partner",
        ],
    "data":[
        "wizard/cash_statement_populate_view.xml",
        "wizard/expense_populate_statement_view.xml",
        "account_expense_view.xml",
        "account_view.xml",
	   ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: