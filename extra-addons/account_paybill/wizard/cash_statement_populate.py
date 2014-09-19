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

import time
from openerp.osv import fields, osv

class account_cash_statement_populate(osv.osv_memory):
    _name = "account.cash.statement.populate"
    _columns = {
            'company_id': fields.many2one('res.company', string="Company"),
            'expense_id': fields.many2one('account.expense', string='Pay Bill', required=True,
                                          domain=[('type','=','paybill'),('state','in',['draft','confirm'])]),
            'partner_id': fields.many2one('res.partner', string="Partner", required=True,
                                          domain=[('employee','=',True)]),
            'currency_id': fields.related('expense_id','journal_id','currency',type="many2one",
                                          relation="res.currency", string="Currency", readonly=True),
            'amount': fields.float('Amount', required=True),
        }
    _defaults = {
            'company_id': lambda s,cr,u,i,c={}: c.has_key('active_id') and s.pool.get('account.bank.statement').browse(cr,u,c['active_id'],context=c).company_id.id or False
        }

    def onchange_partner(self, cr, uid, ids, partner_id, expense_id, context=None):
        context = context or {}
        res = {'value': {}}
        if expense_id:
            return res
        if not partner_id:
            return res
        expense_ids = self.pool.get('account.expense').search(cr, uid, [('partner_id','=',partner_id),('type','=','paybill'),('state','in',['draft','confirm'])], context=context)
        if expense_ids:
            res['value']['expense_id'] = expense_ids[0]
        return res
    
    def onchange_expense(self, cr, uid, ids, expense_id, context=None):
        context = context or {}
        sign = context.get('expense_direction','') == 'forward' and -1.0 or 1.0
        res = {'value': {}}
        expense = self.pool.get('account.expense').browse(cr, uid, expense_id, context=context)
        res['value']['currency_id'] = expense.journal_id.currency.id or expense.journal_id.company_id.currency_id.id
        res['value']['amount'] = expense.amount_balance * sign
        return res
    
    def get_statement_line_new(self,cr,uid,expense,statement, amount, date=None, context=None):
        # Override thi method to modifiy the new statement line to create
        res = {}
        ctx = context.copy()
        ctx['date'] = statement.date
        if date:
            res['date'] = date
            ctx['date'] = date
        amount = self.pool.get('res.currency').compute(cr, uid, expense.journal_id.currency.id or expense.journal_id.company_id.currency_id.id,
                    statement.currency.id, amount, context=ctx)
        sign = -1.0
        #type = 'supplier'
        type = 'general'
        if context.get('expense_direction','forward') == 'back':
            sign = 1.0
            #type = 'customer'
        res.update({
                'name': expense.name or '?',
                'amount': sign * amount,
                'type': type,
                'partner_id': expense.partner_id.id,
                'account_id': expense.journal_id.default_debit_account_id.id,
                'statement_id': statement.id,
                #'ref': voucher.name,
                'expense_id': expense.id,
                })
        return res
    
    def populate_statement(self, cr, uid, ids, context=None):
        context = context or {}
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        data = self.browse(cr, uid, ids[0], context=context)
        statement = statement_obj.browse(cr, uid, context['active_id'], context=context)
        statement_line_obj.create(cr, uid, 
                    self.get_statement_line_new(cr,uid,data.expense_id,statement,data.amount,context=context), context=context)
        return {'type': 'ir.actions.act_window_close'}