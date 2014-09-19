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

from openerp.osv import osv, fields
import openerp.exceptions
import addons.decimal_precision as dp
from openerp.tools.translate import _
import time
import netsvc

class account_journal(osv.osv):
    
    def _last_balance(self, cr, uid, ids, name, args, context=None):
        res = {}
        statement_obj = self.pool.get('account.bank.statement')
        transfer_obj = self.pool.get('account.transfer')
        for journal in self.browse(cr, uid, ids, context=context):
            res[journal.id] = {'last_balance':0.0,'last_balance_date':False,'pending_transfer':0.0,'last_transfer_date':False}
            statement_ids = statement_obj.search(cr, uid,
                [('journal_id', '=', journal.id),('state', '=', 'confirm'),('next_id','=',False)],
                order='date desc, id desc', limit=1, context=context)
            statement = False
            if statement_ids:
                statement = statement_obj.browse(cr, uid, statement_ids[0], context=context)
            else:
                statement_ids = statement_obj.search(cr, uid,
                    [('journal_id', '=', journal.id),('state', '=', 'confirm')],
                    order='date desc, id desc', limit=1, context=context)
                if statement_ids:
                    statement = statement_obj.browse(cr, uid, statement_ids[0], context=context)
            if statement:
                res[journal.id]['last_balance'] = statement.balance_end_real
                res[journal.id]['last_balance_date'] = statement.closing_date
            transfer_ids = transfer_obj.search(cr, uid,
                [('cash_box_id', '=', journal.id),('state', 'in',['confirm'])],
                order='date desc, id desc', context=context)
            if transfer_ids:
                for transfer in transfer_obj.browse(cr, uid, transfer_ids, context=context):
                    if transfer_ids[0] == transfer.id:
                        res[journal.id]['last_transfer_date'] = transfer.date
                    if transfer.src_journal_id.id == journal.id:
                        res[journal.id]['pending_transfer'] -= transfer.src_amount 
                    elif transfer.dst_journal_id.id == journal.id:
                        res[journal.id]['pending_transfer'] += transfer.dst_amount
        return res
    
    _inherit = 'account.journal'
    _columns = {
            'is_cash_box': fields.boolean('Cash Box Journal'),
            'statement_ids': fields.one2many('account.bank.statement','journal_id',string='Cash Statements'),
            'transfer_ids': fields.one2many('account.transfer','cash_box_id',string='Cash Box Transfers'),
            'amount_min': fields.float('Minimal Amount', digits_compute=dp.get_precision('Account'),
                                          help="Minimal amount to stand in the box cash"),
            'amount_max': fields.float('Maximal Amount', digits_compute=dp.get_precision('Account'),
                                          help="Maximal amount to stand in the box cash"),
            'last_balance': fields.function(_last_balance,type='float',string='Last Balance End', digits_compute=dp.get_precision('Account'),
                                          multi='last', help="Last balance amount end of cash statements"),
            'last_balance_date': fields.function(_last_balance,type='date',string='Last Balance Date',multi='last'),
            'pending_transfer': fields.function(_last_balance,type='float',string='Pending to Transfer', digits_compute=dp.get_precision('Account'),
                                          multi='last', help="Amount pending cash transfer  to replenish this cash box"),
            'last_transfer_date': fields.function(_last_balance,type='date',string='Last Transfer Date',multi='last'),
            'property_bank_journal_id': fields.property('account.journal', type='many2one', view_load=True,
                                               relation='account.journal', string='Bank Journal',
                                               help="Default bank journal to make the automated cash transfers"),
        }
    _defaults = {
            'is_cash_box' : False,
        }
    
    def action_replenish(self, cr, uid, ids, context=None):
        transfer_obj = self.pool.get('account.transfer')
        wf_service = netsvc.LocalService("workflow")
        for journal in self.browse(cr, uid, ids, context=context):
            if not journal.property_bank_journal_id:
                raise openerp.exceptions.Warning(_('You must configure a new property (property_bank_journal_id) for the current company on default bank journal field!'))
            difference = journal.amount_max - (journal.pending_transfer + journal.last_balance)
            if difference > 0.0:
                src_journal = journal.property_bank_journal_id
                dst_journal = journal
                value = transfer_obj.onchange_journal(cr, uid, ids, src_journal.id, dst_journal.id,
                                               time.strftime('%Y-%m-%d'), 1.0, difference)['value']
                trans_id = transfer_obj.create(cr,uid,{
                                        'company_id': journal.company_id.id,
                                        'type': 'cash-box',
                                        'origin': _("Replenish of %s")%journal.name,
                                        'src_journal_id': src_journal.id,
                                        'src_amount': difference,
                                        'dst_journal_id': dst_journal.id,
                                        'dst_amount': value['dst_amount'],
                                        'exchange_rate': value['exchange_rate'],
                                        'cash_box_id': journal.id,
                                    },context=context)
                wf_service.trg_validate(uid, 'account.transfer', trans_id, 'transfer_confirm', cr)
        return True
    
class account_cash_statement(osv.osv):

    _inherit = 'account.bank.statement'
    _columns = {
        'sequence' : fields.integer('Sequence'),
    }
    
class account_transfer(osv.Model):
    
    def _get_type (self, cr, uid, context=None):
        res = super(account_transfer,self)._get_type(cr, uid, context=context)
        res.append(('cash-box','Cash Box Transfer'))
        return res
    
    _inherit = 'account.transfer'
    _columns = {
        'type': fields.selection(_get_type,'Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'cash_box_id' : fields.many2one('account.journal', string='Cash Box', readonly=True, states={'draft':[('readonly',False)]}),
    }