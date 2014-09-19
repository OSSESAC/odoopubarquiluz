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
    "name": "Electronic Invoice",
    "version": "0.1",
    "description": """
Manage the electronic invoice
=============================

The management of electronic invoice integrate the invoices with digital signatures and certificates usually in a PKI infastructure with xml messages to a webservices to generate and validate the electronic invoices.

Key Features
------------
* Add support to manage the webservices communication to generate and validate a electronic invoice
* Generate a abstract model to manage electronic invoices from several countries

    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Financial",
    "depends": [
        "base_pki",
        "account",
        ],
    "data":[
        "security/account_einvoice_security.xml",
        "security/ir.model.access.csv",
        "account_einvoice_workflow.xml",
        "account_einvoice_view.xml",
        "account_view.xml",
	    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
    "certificate" : "",
}