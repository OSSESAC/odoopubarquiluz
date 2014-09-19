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

class account_expense_populate_transfer(osv.osv_memory):
    
    _name = "account.expense.populate.transfer"
    _columns = {
            'company_id': fields.many2one('res.company', string="Company"),
            'journal_id': fields.many2one('account.journal', string='Source Journal', required=True,
                                          domain=[('type','in',['cash','bank'])]),
            'partner_id': fields.many2one('res.partner', string="Partner"),
            'have_partner': fields.related('journal_id','have_partner',type="boolean",
                                      string="Have Partner", readonly=True),
            'date': fields.date('date'),
            'currency_id': fields.related('journal_id','currency', type="many2one",
                                      relation="res.currency", string="Currency", readonly=True),
            'amount': fields.float('Amount', required=True),
        }
    _defaults = {
            'date': lambda *a: time.strftime('%Y-%m-%d'),
        }
    
    def onchange_journal(self, cr, uid, ids, journal_id, context=None):
        context = context or {}
        res = {'value': {}}
        if not journal_id:
            return res
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        res['value']['currency_id'] = journal.currency.id or journal.company_id.currency_id.id
        res['value']['have_partner'] = journal.have_partner
        return res

    def populate_transfer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        transfer_obj = self.pool.get('account.transfer')
        data = self.browse(cr, uid, ids[0], context=context)
        expense = self.pool.get('account.expense').browse(cr, uid, context['active_id'], context=context)
        
        src_journal = data.journal_id
        src_partner_id = data.partner_id.id
        dst_journal = expense.journal_id
        dst_partner_id = expense.partner_id.id
        if context.get('expense_direction','forward') == 'back':
            src_journal = expense.journal_id
            src_partner_id = expense.partner_id.id
            dst_journal = data.journal_id
            dst_partner_id = data.partner_id.id

        value = transfer_obj.onchange_journal(cr, uid, ids, src_journal.id, dst_journal.id,
                                       time.strftime('%Y-%m-%d'), 1.0, data.amount)['value']
        transfer_obj.create(cr,uid,{
                                'company_id': expense.company_id.id,
                                'type': 'expense',
                                'origin': expense.name,
                                'src_journal_id': src_journal.id,
                                'src_partner_id': src_partner_id,
                                'src_amount': data.amount,
                                'dst_journal_id': dst_journal.id,
                                'dst_partner_id': dst_partner_id,
                                'dst_amount': value['dst_amount'],
                                'exchange_rate': value['exchange_rate'],
                                'expense_id': expense.id,
                            },context=context)
        return {'type': 'ir.actions.act_window_close'}