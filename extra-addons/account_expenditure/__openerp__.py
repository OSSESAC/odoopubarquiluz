# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
    "name": "Expenditure Management",
    "version": "1.0",
    "description": """
Expenditure Manage with Multiple Invoice
========================================

The management of expenditures, enables you to track your employees expenditures in easy and secure way.
OpenERP has several methods of tracking the expenses. In this way this module will generate expenses reports based on multiple supplier invoices and a new expense module.

Key Features
------------
* Manage the authorization of Expenditure
* Allow manage expense invoices integrated by expenditures
* Optimize the expense and treasury management

Dashboard / Reports for Money Transfer will include:
----------------------------------------------------
* Expenditures Report
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Financial",
    "depends": [
        "account_transfer",
        "account_expense",
        "hr_partner",
        ],
    "data":[
        "wizard/expense_populate_transfer_view.xml",
        "account_expense_data.xml",
        "account_expense_view.xml",
        "account_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}