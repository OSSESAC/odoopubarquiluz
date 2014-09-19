# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Cubic ERP (<http://cubicerp.com>).
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

from osv import fields, osv

class hr_department(osv.osv):
    _inherit = 'hr.department'
    _columns = {
            'analytic_account_ids': fields.one2many('account.analytic.account','department_id',string='Analytic Accounts',
                                                    help="Account analyticis like to cost centers"),
            'manager_user_id': fields.related('manager_id','user_id',type='many2one',obj='res.users',string='Manager User',
                                                    readonly=True),
        }