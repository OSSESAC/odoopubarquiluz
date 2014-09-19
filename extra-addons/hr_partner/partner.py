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

from openerp.osv import osv, fields
from openerp.tools.translate import _

class res_partner(osv.Model):

    def _get_is_employee(self, cr, uid, ids, name, args, context=None):
        res = {}
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('address_home_id','in',ids)],context=context)
        for id in ids: res[id] = False
        for employee in employee_obj.browse(cr, uid, employee_ids, context=context):
            res[employee.address_home_id.id] = True
        return res
    
    def _get_partner_from_employee(self, cr, uid, ids, context=None):
        res = {}
        employee_obj = self.pool.get('hr.employee')
        employee_ids = employee_obj.search(cr, uid, [('id','in',ids),('address_home_id','!=',False)], context=context)
        for employee in employee_obj.browse(cr, uid, employee_ids, context=context):
            res[employee.address_home_id.id] = True
        return res.keys()
    
    def _set_is_employee(self, cr, uid, id, name, value, fnct_inv_arg, context=None):
        if not value:
            employee_obj = self.pool.get('hr.employee')
            employee_ids = employee_obj.search(cr, uid, [('address_home_id','=',id)], context=context)
            employee_obj.write(cr, uid, employee_ids, {'address_home_id':False}, context=context)
        else:
            raise osv.except_osv('Error!', _("You must select a address home on employee form."))
        return True
    
    _inherit = "res.partner"
    _columns = {
        'is_employee': fields.function(_get_is_employee, type="boolean", string='Employee', fnct_inv=_set_is_employee,
                                    store={
                                        'hr.employee': (_get_partner_from_employee, ['address_home_id'], 20),
                                    }, help="Check this box if the contact is an Employee."),
	}
