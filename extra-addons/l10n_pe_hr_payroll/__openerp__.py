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
###############################################################################
{
    'name': 'Peru - Payroll',
    'category': 'Localization',
    'author': 'Cubic ERP',
    'depends': ['hr_payroll',
                'hr_payroll_account',
                'base_table_payroll',
                'l10n_pe_base',
                'l10n_pe_4ta',
                ],
    'version': '1.0',
    'description': """
Peruvian Payroll Rules.
=======================

    * Allowances/Deductions
    * Employee Payslip
    * Monthly Payroll Register
    * Salary, ESSALUD, Withholding Tax, Child Allowance, ...
    """,

    'auto_install': False,
    'demo': [],
    'data':[
        'data/base.table.csv',
        'data/base.element.csv',
        'l10n_pe_hr_payroll_data.xml',
        'hr_view.xml',
    ],
    'installable': True
}