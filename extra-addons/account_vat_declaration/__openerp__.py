# -*- coding: utf-8 -*-
##############################################################################
#
#    account_vat_declaration module for OpenERP, Account VAT Declaration
#    Copyright (C) 2011 Thamini S.à.R.L. (<http://www.thamini.com) Xavier ALT
#
#    This file is a part of account_vat_declaration
#
#    account_vat_declaration is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_vat_declaration is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'account_vat_declaration',
    'version': '0.1',
    'author': 'Thamini S.à.R.L. and Cubic ERP',
    'website': 'http://www.cubicerp.com',
    'description': """
        Account VAT Declaration
        
        Powered by Cubic ERP http://cubicERP.com
        
        Cubic ERP Adds:
         - Support to base_table
         - filter by journal code in lines
         - Other fixes
         - Migrated to v7.0
         - Multicompany
    """,
    'depends': [
        'account',
        'base_table',
    ],
    'init_xml': [
    ],
    'demo_xml': [
    ],
    'update_xml': [
        'account_vat_declaration_view.xml',
        'workflow/account_vat_decl.xml',
        'wizard/account_vat_declaration_wizard_view.xml',
    ],
    'active': False,
    'installable': True,
}
