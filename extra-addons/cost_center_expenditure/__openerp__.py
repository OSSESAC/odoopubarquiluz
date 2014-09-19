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
    "name": "Account Expenditure Cost Center",
    "version": "1.0",
    "description": """
Adds financial cost center in account expenditure with multiple invoices
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Accouting",
    "depends": [
		"account_expenditure",
        "cost_center",
        "cost_center_expense",
	    ],
	"data":[
        "account_view.xml",
	    ],
    "demo_xml": [
	    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}