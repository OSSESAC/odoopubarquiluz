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

from osv import osv, fields


class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
#     def create(self, cr, uid, vals, context=None):
#         context = context or {}
#         if vals.get('address_home_id', False):
#             self.pool.get('res.partner').write(cr, uid, [vals['address_home_id']],
#                                                {'is_employee': True}, context=context)
#         return super(hr_employee,self).create(cr, uid, vals, context=context)
#     
#     def write(self, cr, uid, ids, vals, context=None):
#         partner_obj = self.pool.get('res.partner')
#         if vals.has_key('address_home_id'):
#             for employee in self.browse(cr, uid, ids, context=context):
#                 if employee.address_home_id:
#                     partner_obj.write(cr, uid, [employee.address_home_id.id],
#                                            {'is_employee': False}, context=context)
#             if vals['address_home_id']:
#                 partner_obj.write(cr, uid, [vals['address_home_id']],
#                                         {'is_employee': True}, context=context)
#         return super(hr_employee,self).write(cr, uid, ids, vals, context=context)
#     
    def unlink(self, cr, uid, ids, context=None):
        partner_ids = []
        for employee in self.browse(cr, uid, ids, context=context):
            if employee.address_home_id:
                partner_ids.append(employee.address_home_id.id)
        self.pool.get('res.partner').write(cr, uid, partner_ids,
                                            {'is_employee': False}, context=context)
        return super(hr_employee,self).unlink(cr, uid, ids, context=context)

    def onchange_user(self, cr, uid, ids, user_id, context=None):
        res = super(hr_employee,self).onchange_user(cr, uid, ids, user_id, context=context)
        if user_id:
            res['value']['address_home_id'] = self.pool.get('res.users').browse(cr, uid, user_id, context=context).partner_id.id
        return res
    
    def onchange_home(self, cr, uid, ids, address_home_id, context=None):
        res = {'value':{}}
        if address_home_id:
            res['value']['name'] = self.pool.get('res.partner').browse(cr, uid, address_home_id, context=context).name
        return res