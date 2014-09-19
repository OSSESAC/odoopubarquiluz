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

class account_expense_populate_statement(osv.osv_memory):
    _name = "account.expense.populate.statement"
    _columns = {
            'company_id': fields.many2one('res.company', string="Company"),
            'statement_id': fields.many2one('account.bank.statement', string='Cash Statement', required=True,
                                          domain=[('state','in',['open']),('journal_id.type', '=', 'cash')]),
            'date': fields.date('date'),
            'currency_id': fields.related('statement_id','journal_id','currency',type="many2one",
                                          relation="res.currency", string="Currency", readonly=True),
            'amount': fields.float('Amount', required=True),
        }
    _defaults = {
            'company_id': lambda s,cr,u,i,c={}: c.has_key('active_id') and s.pool.get('account.expense').browse(cr,u,c['active_id'],context=c).company_id.id or False
        }

    def onchange_statement(self, cr, uid, ids, statement_id, context=None):
        context = context or {}
        res = {'value': {}}
        if not statement_id:
            return res
        statement = self.pool.get('account.bank.statement').browse(cr, uid, statement_id, context=context)
        res['value']['date'] = statement.date
        res['value']['currency_id'] = statement.journal_id.currency.id or statement.journal_id.company_id.currency_id.id
        return res

    def get_statement_line_new(self,cr,uid,expense,statement, amount, date, context=None):
        return self.pool.get('account.cash.statement.populate').get_statement_line_new(cr,uid,expense,statement, amount, date=date, context=context)

    def populate_statement(self, cr, uid, ids, context=None):
        context = context or {}
        statement_line_obj = self.pool.get('account.bank.statement.line')
        
        data = self.browse(cr, uid, ids[0], context=context)
        expense = self.pool.get('account.expense').browse(cr, uid, context['active_id'], context=context)
        s = self.get_statement_line_new(cr,uid,expense,data.statement_id,data.amount,data.date,context=context)
        statement_line_obj.create(cr, uid, 
                    s, context=context)
        return {'type': 'ir.actions.act_window_close'}