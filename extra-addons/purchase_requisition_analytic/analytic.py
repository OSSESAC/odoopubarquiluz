# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-TODAY Cubic ERP (<http://cubicerp.com>).
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

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    _columns = {
            'department_id': fields.many2one('hr.department','Department'),
            'chief_project_id': fields.many2one('res.users','Chief Project'),
        }
    
    def onchange_department(self, cr, uid, ids, department_id, context=None):
        if context is None:
            context ={}
        res = {'value': {}}
        if not department_id:
            return res
        department = self.pool.get('hr.department').browse(cr, uid, department_id, context=context)
        res['value'].update({'chief_project_id': department.manager_id.user_id.id})
        return res
    
    def is_user_chief(self, cr, uid, idd, context=None):
        analytic = self.browse(cr, uid, idd, context=context)
        if uid == (analytic.chief_project_id and analytic.chief_project_id.id or 0):
            return True
        department = analytic.department_id
        while department:
            if department.manager_user_id.id == uid:
                return True
            department =  department.parent_id
        return False
