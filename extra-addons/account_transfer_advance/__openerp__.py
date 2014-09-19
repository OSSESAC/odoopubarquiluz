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
    "name": "Payment Advances for Sales and Purchases",
    "version": "1.0",
    "description": """
Manage payment advances for purchase orders and sale orders
===========================================================

The management of payment advances, enables you to track your cash and bank transfers to suppliers and customers in easy and secure way.
OpenERP has several methods of tracking the payment advances. In this way this module will generate cash / bank transfers to suppliers / from customers integrated with invoices, pays and bank reconciliation.

Key Features
------------
* Generate cash / bank transfers to payment advances
* Allow manage sales advances using transfers
* Allow manage purchase advances using transfers
* Integrate all process to invoices, pay and reconciliations

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Purchase",
    "depends": [
        "sale",
        "purchase",
        "account_transfer",
        ],
    "data":[
        "account_view.xml",
        "partner_view.xml",
        "account_transfer_view.xml",
        "wizard/purchase_advance_transfer_view.xml",
        "wizard/sale_advance_transfer_view.xml",
        "purchase_view.xml",
        "sale_view.xml",
        "account_data.xml",
        "partner_data.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
