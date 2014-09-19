# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2012 Cubic ERP - Teradata SAC. (http://cubicerp.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from osv import osv, fields
from tools.translate import _

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
            'first_name': fields.char('First Name', size=32),
            'middle_name': fields.char('Middle Name', size=32),
            'surname': fields.char('Surname', size=32),
            'mother_name': fields.char("Mother's Name", size=32)
        }

#    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
#        if not args:
#            args = []
#        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
#            
#            ids = self.search(cr, uid, [('ref', operator, '%%%s%%'%name)] + args, limit=limit, context=context)
#            if ids:
#                res = self.name_get(cr, uid, ids, context)
#                return res
#        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    def create(self, cr, uid, vals, context=None):
        if vals.get('name') and not (vals.get('is_company') or vals.get('fist_name') or vals.get('surname')):
            names = filter(None,vals.get('name').split(' '))
            if len(names) > 2:
                i = 0
                while i < len(names):
                    if names[i].lower() in ('de', 'del'):
                        if i+1 < len(names):
                            if names[i+1].lower() in ('la'):
                                 if i+2 < len(names):
                                     names[i] = names[i] + ' ' + names.pop(i+1) + ' ' + names.pop(i+1)
                            else:
                                names[i] = names[i] + ' ' + names.pop(i+1)
                    i += 1
            if len(names) > 0:
                vals['first_name'] = names[0]
            if len(names) > 1:
                vals['surname'] = names[1]
            if len(names) == 3:
                vals['mother_name'] = names[2]
            if len(names) == 4:
                vals['middle_name'] = names[1]
                vals['surname'] = names[2]
                vals['mother_name'] = names[3]
        return super(res_partner,self).create(cr, uid, vals, context=context)
    
    
    def onchange_person_name(self, cr, uid, ids, first_name, middle_name, surname, mother_name, context=None):
        res = {'value':{}}
        res['value']['name'] = (first_name and (first_name+' ') or '') + (middle_name and (middle_name+' ') or '') + (surname and (surname+' ') or '') + (mother_name and (mother_name+' ') or '')
        return res

    def vat_change(self, cr, uid, ids, value, context=None):
        res = super(res_partner,self).vat_change(cr, uid, ids, value, context=context)
        if len(str(value)) > 2:
            res['value']['ref'] = value[2:]
        return res

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
