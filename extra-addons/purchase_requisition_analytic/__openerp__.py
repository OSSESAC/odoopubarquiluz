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
    "name": "Purchase Requisition with Analytic and Approves",
    "version": "1.0",
    'description': """
Analytics Accounts for purchases requisitions and Approves.
===========================================================

This module modifies the purchase requisition workflow in order to add analytic accounting and validation to approve the requisitions.

Key Features
------------
* Add analytic account on purchase requisition
* Add approve state on purchase requisition
* Add responsible group to approve requisitions
* Add description field on requisition line
        """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Purchase",
    "depends": [
		"purchase_requisition",
        "analytic",
        "hr",
        "report_geraldo",
	    ],
	"data":[
		"purchase_requisition_data.xml",
        "purchase_requisition_view.xml",
        "purchase_requisition_report.xml",
        "analytic_view.xml",
        "hr_view.xml",
        "security/purchase_requisition_analytic.xml",
	    ],
    "demo_xml": [
	    ],
    "update_xml": [
	    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
