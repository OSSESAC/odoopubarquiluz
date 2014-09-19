# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_cashbox_line(osv.osv):

    """ Cash Box Details """

    _name = 'account.cashbox.line'
    _description = 'CashBox Line'
    _rec_name = 'pieces'

    def _sub_total(self, cr, uid, ids, name, arg, context=None):

        """ Calculates Sub total
        @param name: Names of fields.
        @param arg: User defined arguments
        @return: Dictionary of values.
        """
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'subtotal_opening' : obj.pieces * obj.number_opening,
                'subtotal_closing' : obj.pieces * obj.number_closing,
            }
        return res

    def on_change_sub_opening(self, cr, uid, ids, pieces, number, *a):
        """ Compute the subtotal for the opening """
        return {'value' : {'subtotal_opening' : (pieces * number) or 0.0 }}

    def on_change_sub_closing(self, cr, uid, ids, pieces, number, *a):
        """ Compute the subtotal for the closing """
        return {'value' : {'subtotal_closing' : (pieces * number) or 0.0 }}

    _columns = {
        'pieces': fields.float('Unit of Currency', digits_compute=dp.get_precision('Account')),
        'number_opening' : fields.integer('Number of Units', help='Opening Unit Numbers'),
        'number_closing' : fields.integer('Number of Units', help='Closing Unit Numbers'),
        'subtotal_opening': fields.function(_sub_total, string='Opening Subtotal', type='float', digits_compute=dp.get_precision('Account'), multi='subtotal'),
        'subtotal_closing': fields.function(_sub_total, string='Closing Subtotal', type='float', digits_compute=dp.get_precision('Account'), multi='subtotal'),
        'bank_statement_id' : fields.many2one('account.bank.statement', ondelete='cascade'),
     }

account_cashbox_line()

class account_cash_statement(osv.osv):

    _inherit = 'account.bank.statement'

    def _update_balances(self, cr, uid, ids, context=None):
        """
            Set starting and ending balances according to pieces count
        """
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            if (statement.journal_id.type not in ('cash',)) or (not statement.journal_id.cash_control):
                continue
            start = end = 0
            for line in statement.details_ids:
                start += line.subtotal_opening
                end += line.subtotal_closing
            data = {
                'balance_start': start,
                'balance_end_real': end,
            }
            res[statement.id] = data
            super(account_cash_statement, self).write(cr, uid, [statement.id], data, context=context)
        return res

    def _get_sum_entry_encoding(self, cr, uid, ids, name, arg, context=None):

        """ Find encoding total of statements "
        @param name: Names of fields.
        @param arg: User defined arguments
        @return: Dictionary of values.
        """
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            res[statement.id] = sum((line.amount for line in statement.line_ids), 0.0)
        return res

    def _get_company(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        company_pool = self.pool.get('res.company')
        user = user_pool.browse(cr, uid, uid, context=context)
        company_id = user.company_id
        if not company_id:
            company_id = company_pool.search(cr, uid, [])
        return company_id and company_id[0] or False

    def _get_statement_from_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.bank.statement.line').browse(cr, uid, ids, context=context):
            result[line.statement_id.id] = True
        return result.keys()

    def _compute_difference(self, cr, uid, ids, fieldnames, args, context=None):
        result =  dict.fromkeys(ids, 0.0)

        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.balance_end_real - obj.balance_end

        return result

    def _compute_last_closing_balance(self, cr, uid, ids, fieldnames, args, context=None):
        result = {}
        for stmt in self.browse(cr, uid, ids, context=context):
            result[stmt.id] = 0.0
            if stmt.previus_id:
                result[stmt.id] = stmt.previus_id.balance_end_real
        return result

    def onchange_journal_id(self, cr, uid, ids, journal_id, line_ids=[], balance_end_real=0.0, opening_details_ids=[], context=None):
        result = super(account_cash_statement, self).onchange_journal_id(cr, uid, ids, journal_id)
        if not journal_id:
            return result
        result['value']['cash_control'] = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context).cash_control
        statement_ids = self.search(cr, uid,
                [('journal_id', '=', journal_id),('state', '=', 'confirm'),'|',('next_id','=',False),('next_id','=',journal_id)],
                order='date desc, id desc',
                limit=1,
                context=context)
        result['value']['previus_id'] = statement_ids and statement_ids[0] or False
        result['value'].update(self.onchange_previus_id(cr, uid, ids, result['value']['previus_id'], journal_id, opening_details_ids, context=context)['value'])
        result['value'].update(self.onchange_details(cr, uid, ids, result['value']['opening_details_ids'], line_ids, result['value']['cash_control'], result['value']['last_closing_balance'], balance_end_real, context=context)['value'])
        return result

    def onchange_previus_id(self, cr, uid, ids, previus_id, journal_id, opening_details_ids, context=None):
        result = {'value':{}}
        if not journal_id:
            return result
        result['value']['opening_details_ids'] = []
        for detail in opening_details_ids:
            if detail[0] in [1,4]:
                result['value']['opening_details_ids'].append((2, detail[1], detail[2]))
            elif detail[0] == 2:
                result['value']['opening_details_ids'].append(detail)
        result['value']['last_closing_balance'] = 0.0
        if not previus_id:
            for value in self.pool.get('account.journal').browse(cr, uid, journal_id, context=context).cashbox_line_ids:
                result['value']['opening_details_ids'].append([0, False, {'pieces':value.pieces, 'number_opening':0, 'subtotal_opening':0.0, 'number_closing':0, 'subtotal_closing':0.0}])
        else:
            st = self.browse(cr, uid, previus_id, context=context)
            for value in st.details_ids:
                result['value']['opening_details_ids'].append([0, False, {'pieces':value.pieces, 'number_opening':value.number_closing, 'subtotal_opening':value.number_closing*value.pieces, 'number_closing':0, 'subtotal_closing':0.0}])
            result['value']['last_closing_balance'] = st.balance_end_real
        return result


    def onchange_details(self, cr, uid, ids, details_ids, line_ids, cash_control, balance_start, balance_end_real, context=None):
        res = {'value':{'total_entry_encoding':0.0,'balance_start':0.0,'balance_end':0.0,'balance_end_real':0.0,}}
        cashbox_line_obj = self.pool.get('account.cashbox.line')
        stmt_line_obj = self.pool.get('account.bank.statement.line')
        for action, line_id, data in line_ids:
            amount = 0.0
            if action != 0:
                stmt_line = stmt_line_obj.browse(cr, uid, line_id, context=context)
                amount = stmt_line.amount
            amount = data and data.get('amount') or amount
            if action in (1, 4, 0):
                #1,4:Modified 0:inserted
                res['value']['total_entry_encoding'] += amount
#            elif action == 2:
#                #deleted
        res['value']['balance_end'] = res['value']['total_entry_encoding']
        if not cash_control:
            res['value']['balance_start'] += balance_start
            res['value']['balance_end_real'] += balance_end_real
            res['value']['balance_end'] += balance_start
        else:
            for action, line_id, data in details_ids:
                pieces = number_opening = number_closing = 0.0
                if action != 0:
                    cashbox_line = cashbox_line_obj.browse(cr, uid, line_id, context=context)
                    pieces = cashbox_line.pieces 
                    number_opening = cashbox_line.number_opening
                    number_closing = cashbox_line.number_closing
                pieces = data and data.get('pieces') or pieces 
                number_opening = data and data.get('number_opening') or number_opening
                number_closing = data and data.get('number_closing') or number_closing
                if action in (1, 4, 0):
                    #1,4:Modified 0:inserted
                    res['value']['balance_start'] += pieces * number_opening
                    res['value']['balance_end_real'] += pieces * number_closing
                    res['value']['balance_end'] += pieces * number_opening
#                elif action == 2:
#                    #deleted
        res['value']['difference'] = res['value']['balance_end_real'] - res['value']['balance_end'] 
        return res
        
    def _next_id(self, cr, uid, ids, name, arg, context=None):
        res=dict.fromkeys(ids, False)
        for stmt in self.browse(cr, uid, ids, context=context):
            for next in stmt.next_ids:
                if next.state == 'cancel':
                    continue
                res[stmt.id] = next.id
                break 
        return res
        
    _columns = {
        'total_entry_encoding': fields.function(_get_sum_entry_encoding, string="Total Transactions",
            store = {
                'account.bank.statement': (lambda self, cr, uid, ids, context=None: ids, ['line_ids','move_line_ids'], 10),
                'account.bank.statement.line': (_get_statement_from_line, ['amount'], 10),
            }),
        'closing_date': fields.datetime("Closed On"),
        'details_ids' : fields.one2many('account.cashbox.line', 'bank_statement_id', string='CashBox Lines'),
        'opening_details_ids' : fields.one2many('account.cashbox.line', 'bank_statement_id', string='Opening Cashbox Lines'),
        'closing_details_ids' : fields.one2many('account.cashbox.line', 'bank_statement_id', string='Closing Cashbox Lines'),
        'user_id': fields.many2one('res.users', 'Responsible', required=False),
        'difference' : fields.function(_compute_difference, method=True, string="Difference", type="float"),
        'last_closing_balance' : fields.function(_compute_last_closing_balance, method=True, string='Last Closing Balance', type='float'),
        'cash_control': fields.related('journal_id','cash_control', string="Cash Control", type="boolean", readonly=True),
        'previus_id': fields.many2one('account.bank.statement', string='Previus Statement', 
                                      readonly=True, states={'draft':[('readonly',False)]}),
        'next_ids': fields.one2many('account.bank.statement','previus_id',string='Next Statements', readonly=True),
        'next_id' : fields.function(_next_id,type="many2one",relation='account.bank.statement', string='Next Statement', readonly=True,
                                    store={'account.bank.statement': (lambda s, cr, uid, ids, c={}:[st.previus_id.id for st in s.pool.get('account.bank.statement').browse(cr,uid,ids,context=c)], ['previus_id'], 20),}),
    }
    _defaults = {
        'state': 'draft',
        'date': lambda self, cr, uid, context={}: context.get('date', time.strftime("%Y-%m-%d %H:%M:%S")),
        'user_id': lambda self, cr, uid, context=None: uid,
    }

    def create(self, cr, uid, vals, context=None):
        journal = False
        if vals.get('journal_id'):
            journal = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'], context=context)
        if journal and (journal.type == 'cash') and not vals.get('details_ids'):
            vals['details_ids'] = []
        if vals.get('previus_id'):
            stmt = self.pool.get('account.bank.statement').browse(cr, uid, vals['previus_id'], context=context)
            if stmt.next_id:
                raise osv.except_osv(_('User Error!'), (_('You do not select a previus statement (%s) used by other statement (%s)') % (stmt.previus_id.name,stmt.previus_id.next_id.name, )))
            vals['balance_start'] = stmt.balance_end_real
        res_id = super(account_cash_statement, self).create(cr, uid, vals, context=context)
        self._update_balances(cr, uid, [res_id], context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        """
        Update redord(s) comes in {ids}, with new value comes as {vals}
        return True on success, False otherwise

        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be update
        @param vals: dict of new values to be set
        @param context: context arguments, like lang, time zone

        @return: True on success, False otherwise
        """
        if vals.get('previus_id'):
            stmt = self.pool.get('account.bank.statement').browse(cr, uid, vals['previus_id'], context=context)
            if stmt.next_id:
                raise osv.except_osv(_('User Error!'), (_('You do not select a previus statement (%s) used by other statement (%s)') % (stmt.previus_id.name,stmt.previus_id.next_id.name, )))
        
        res = super(account_cash_statement, self).write(cr, uid, ids, vals, context=context)
        self._update_balances(cr, uid, ids, context)
        return res

    def _user_allow(self, cr, uid, statement_id, context=None):
        return True

    def button_previus_id(self, cr, uid, ids, context=None):
        for stmt in self.browse(cr, uid, ids, context=context):
            if not stmt.previus_id:
                continue
            self.pool.get('account.cashbox.line').unlink(cr, uid, [d.id for d in stmt.details_ids], context=context)
            self.write(cr, uid, [stmt.id], {'balance_start': stmt.previus_id.balance_end_real, 
                                            'details_ids': [(0,False,{'pieces':d.pieces, 'number_opening':d.number_closing, 'subtotal_opening':d.number_closing*d.pieces, 'number_closing':0, 'subtotal_closing':0.0}) for d in stmt.previus_id.details_ids]},
                       context=context)
        return True

    def button_open(self, cr, uid, ids, context=None):
        """ Changes statement state to Running.
        @return: True
        """
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}
        statement_pool = self.pool.get('account.bank.statement')
        for statement in statement_pool.browse(cr, uid, ids, context=context):
            vals = {}
            if not self._user_allow(cr, uid, statement.id, context=context):
                raise osv.except_osv(_('Error!'), (_('You do not have rights to open this %s journal!') % (statement.journal_id.name, )))
            if statement.previus_id and statement.previus_id.next_id and statement.previus_id.next_id.id != statement.id:
                raise osv.except_osv(_('User Error!'), (_('You do not select a previus statement (%s) used by other statement (%s)') % (statement.previus_id.name,statement.previus_id.next_id.name, )))
            if statement.name and statement.name == '/':
                c = {'fiscalyear_id': statement.period_id.fiscalyear_id.id}
                if statement.journal_id.sequence_id:
                    st_number = obj_seq.next_by_id(cr, uid, statement.journal_id.sequence_id.id, context=c)
                else:
                    st_number = obj_seq.next_by_code(cr, uid, 'account.cash.statement', context=c)
                vals.update({
                    'name': st_number
                })

            vals.update({
                'state': 'open',
            })
            self.write(cr, uid, [statement.id], vals, context=context)
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        for stmt in self.browse(cr, uid, ids, context=context):
            if stmt.next_id and stmt.next_id.state != 'draft':
                raise osv.except_osv(_('User Error!'),
                                _('The next cash statement (%s) must be in draft state') % (stmt.next_id.name,))
        return super(account_cash_statement,self).button_cancel(cr, uid, ids, context=context)

    def statement_close(self, cr, uid, ids, journal_type='bank', context=None):
        if journal_type == 'bank':
            return super(account_cash_statement, self).statement_close(cr, uid, ids, journal_type, context)
        vals = {
            'state':'confirm',
            'closing_date': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.write(cr, uid, ids, vals, context=context)

    def check_status_condition(self, cr, uid, state, journal_type='bank'):
        if journal_type == 'bank':
            return super(account_cash_statement, self).check_status_condition(cr, uid, state, journal_type)
        return state=='open'

    def button_confirm_cash(self, cr, uid, ids, context=None):
        absl_proxy = self.pool.get('account.bank.statement.line')
        TABLES = ((_('Profit'), 'profit_account_id'), (_('Loss'), 'loss_account_id'),)
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.previus_id:
                if obj.previus_id.state != 'confirm':
                    raise osv.except_osv(_('User Error!'),
                                _('The previus cash statement (%s) must be in confirm state') % (obj.previus_id.name,))
                if obj.previus_id.balance_end_real != obj.balance_start:
                    raise osv.except_osv(_('User Error!'),
                                _('The start balance (%s) must be equal to balance end real (%s) of previus cash statement (%s)') % (obj.balance_start,obj.previus_id.balance_end_real,obj.previus_id.name))
            if obj.difference == 0.0:
                continue
            for item_label, item_account in TABLES:
                if not getattr(obj.journal_id, item_account):
                    raise osv.except_osv(_('Error!'),
                                         _('There is no %s Account on the journal %s.') % (item_label, obj.journal_id.name,))
            is_profit = obj.difference < 0.0
            account = getattr(obj.journal_id, TABLES[is_profit][1])
            values = {
                'statement_id' : obj.id,
                'journal_id' : obj.journal_id.id,
                'account_id' : account.id,
                'amount' : obj.difference,
                'name' : _('Exceptional %s') % TABLES[is_profit][0],
            }
            absl_proxy.create(cr, uid, values, context=context)
        super(account_cash_statement, self).button_confirm_bank(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'closing_date': time.strftime("%Y-%m-%d %H:%M:%S")}, context=context)

account_cash_statement()

class account_journal(osv.osv):
    _inherit = 'account.journal'

    def _default_cashbox_line_ids(self, cr, uid, context=None):
        # Return a list of coins in Euros.
        result = [
            dict(pieces=value) for value in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
        ]
        return result

    _columns = {
        'cashbox_line_ids' : fields.one2many('account.journal.cashbox.line', 'journal_id', 'CashBox'),
    }

    _defaults = {
        'cashbox_line_ids' : _default_cashbox_line_ids,
    }

account_journal()

class account_journal_cashbox_line(osv.osv):
    _name = 'account.journal.cashbox.line'
    _rec_name = 'pieces'
    _columns = {
        'pieces': fields.float('Values', digits_compute=dp.get_precision('Account')),
        'journal_id' : fields.many2one('account.journal', 'Journal', required=True, select=1, ondelete="cascade"),
    }

    _order = 'pieces asc'

account_journal_cashbox_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
