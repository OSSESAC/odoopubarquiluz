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
    "name": "Payment Transfer for Invoices",
    "version": "1.0",
    "description": """
Manage cash/bank transfers for invoices
=======================================

The management of money transfers, enables you to track your cash and bank transfers to suppliers and customers in easy and secure way.
OpenERP has several methods of tracking the payment transfers on invoices. In this way this module will generate cash / bank transfers to suppliers / from customers integrated with bank reconciliation.

Key Features
------------
* Generate cash / bank transfers to customer/supplier invoices
* Integrate all process to reconciliations

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Purchase",
    "depends": [
        "account",
        "account_transfer",
        ],
    "data":[
        "account_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}