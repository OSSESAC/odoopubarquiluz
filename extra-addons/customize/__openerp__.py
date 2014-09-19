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
    "name": "Base Customize",
    "version": "1.0",
    "description": """
Add some general customizations to OpenERP

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "customization",
    "depends": [
		"account",
        "account_load",
        "purchase",
	    ],
	"data":[
		"account_view.xml",
        "account_menu.xml",
        "res_currency_view.xml",
        "res_company_view.xml",
        "account_sequence.xml",
	    ],
    "demo_xml": [
	    ],
    "update_xml": [
	    ],
    "active": False,
    "installable": True,
    "certificate" : "",
}