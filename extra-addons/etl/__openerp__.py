# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
    "name": "ETL - Extract Tranform and Load Data",
    "version": "0.1",
    "description": """
Manage and Perform ETL Operations in OpenERP
============================================

Add ETL funcionality to OpenERP to extract, transform and load data from any source like to an ODBC, other PostgreSQL or other OpenERP

Main Features
-------------
* Support ODBC, PostgreSQL and XMLRPC as source or destinity server
* Support dinamic mapping of fields and values
* Support equivalent table to transform the values
* Execute Jobs from a shell script or a OpenERP Task
* Detailed log with errors, warnings and information
+ Jobs by batch or per call

Main Libraries
--------------
* OpenERP ETL Client https://pypi.python.org/pypi/openerp-client-etl

Installation
------------
First you need installa the pyodbc library on your system, use the next commands for Ubuntu:

    $ sudo apt-get install g++
    $ sudo apt-get install unixodbc unixodbc-dev
    $ sudo apt-get install python-pyodbc

ETL Module need the OpenERP ETL Client Library installed on your system, in order to install this library use the cross platform easy_install:

    $ easy_install openerp-client-lib
    $ easy_install openerp-client-etl

About the Author
----------------
Cubic ERP has started projects with OpenERP from 2009, and initiated as OpenERP CTP Partner from 2011. We are expert consultors with certification FEC-V7 of OpenERP, and top contributors on apps.openerp.com with more than 75 modules published and 5 modules included on ofiicial release of OpenERP.
    """,
    "author": "Cubic ERP",
    "website": "http://cubicERP.com",
    "category": "Migration",
    "depends": [
		"base",
	    ],
	"data":[
		"security/ir.model.access.csv",
        "etl_view.xml",
	    ],
    "demo_xml": [
	    ],
    "active": False,
    "installable": True,
}