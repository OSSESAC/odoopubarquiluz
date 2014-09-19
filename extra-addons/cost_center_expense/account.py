# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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

class account_expense_invoice(osv.Model):
    
    def _one_line_field_read(self, cr, uid, ids, line, context=None):
        res = super(account_expense_invoice,self)._one_line_field_read(cr, uid, ids, line, context=context)
        res.update({
                'account_cc_id': line.account_cc_id.id,
            })
        return res
        
    def _one_line_field_map(self, cr, uid, id, context=None):
        res = super(account_expense_invoice,self)._one_line_field_map(cr, uid, id, context=context)
        res.update({
                'account_cc_id': 'account_cc_id',
            })
        return res
    
    def _get_one_line(self, cr, uid, ids, name, args, context=None):
        return super(account_expense_invoice,self)._get_one_line(cr, uid, ids, name, args, context=context)
       
    def _set_one_line(self, cr, uid, id, name, value, arg, context=None):
        return super(account_expense_invoice,self)._set_one_line(cr, uid, id, name, value, arg, context=context)
    
    _name = 'account.expense.invoice'
    _inherit = 'account.expense.invoice'
    _columns = {
            'account_cc_id': fields.function(_get_one_line, type="many2one", obj='account.account', string='Cost Center', multi="expense_all",
                                           fnct_inv=_set_one_line, domain=[('type','<>','view'), ('type', '<>', 'closed'), ('is_cost_center','=',True)], help="Debit account to make a aditional journal entry like to cost center account"),
        }

    def onchange_analytic_id(self, cr, uid, ids, analytic_id):
        res = {'value':{}}
        if not analytic_id:
            return res
        account = self.pool.get('account.analytic.account').browse(cr, uid, analytic_id)
        res['value']['account_cc_id'] = account.account_cost_center and account.account_cost_center.id or False
        return res