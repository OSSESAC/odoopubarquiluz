# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2012 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
import openerp.exceptions
from tools.translate import _
import time
import addons.decimal_precision as dp

class account_expense(osv.Model):
    _inherit = 'account.expense'
    _columns = {
            'amount_planed': fields.float('Planed Amount', digits_compute=dp.get_precision('Account'),
                                          readonly=True, states={'draft':[('readonly',False)]},
                                          help="Planed incomes to receive"),
            'date_end': fields.date('Date End', readonly=True, states={'draft':[('readonly',False)]}),
            'description': fields.html('Description', readonly=True, states={'draft':[('readonly',False)]}),
            'property_bank_journal_id': fields.property('account.journal', type='many2one', view_load=True,
                                               relation='account.journal', string='Bank Journal',
                                               readonly=True, states={'draft':[('readonly',False)]},
                                               help="Default bank journal to make the automated cash transfers"),
        }
    
    def action_pre_approve(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            if not expense.invoice_ids:
                raise osv.except_osv(_('User Error!'),_('You must register almost one invoice on invoices tab'))
        return super(account_expense,self).action_pre_approve(cr, uid, ids, context=context)
    
    def action_approve(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            if expense.type=='expenditure' and not self.pool.get('res.currency').is_zero(cr, uid, expense.currency_id, expense.amount_balance):
                raise osv.except_osv(_('User Error!'),_('Te balance amount must be zero (current balance:%d)')%(expense.amount_balance))
        return super(account_expense,self).action_approve(cr, uid, ids, context=context)
    
    def action_generate_transfer(self, cr, uid, ids, context=None):
        context = context or {}
        transfer_obj = self.pool.get('account.transfer')
        for expense in self.browse(cr, uid, ids, context=context):
            if not expense.property_bank_journal_id:
                raise openerp.exceptions.Warning(_("You must configure a new property (property bank journal_id) for the current company, on default bank journal!"))
            amount = expense.amount_planed + expense.amount_transfer
            if amount <= 0.01:
                continue
            src_journal = expense.property_bank_journal_id
            dst_journal = expense.journal_id
            dst_partner_id = expense.partner_id.id
            value = transfer_obj.onchange_journal(cr, uid, ids, src_journal.id, dst_journal.id,
                                           time.strftime('%Y-%m-%d'), 1.0, amount)['value']
            value.update(transfer_obj.onchange_amount(cr, uid, ids, 'dst_amount',0.0,amount,value['exchange_rate'])['value'])
            transfer_obj.create(cr,uid,{
                                    'company_id': expense.company_id.id,
                                    'type': 'expense',
                                    'origin': expense.name,
                                    'src_journal_id': src_journal.id,
                                    'src_amount': value['src_amount'],
                                    'dst_journal_id': dst_journal.id,
                                    'dst_partner_id': dst_partner_id,
                                    'dst_amount': amount,
                                    'exchange_rate': value['exchange_rate'],
                                    'expense_id': expense.id,
                                },context=context)
        return super(account_expense,self).action_generate_transfer(cr, uid, ids, context=context)