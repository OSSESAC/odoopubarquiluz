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

from osv import osv, fields
from tools.translate import _
import time
import addons.decimal_precision as dp
import netsvc

class account_expense(osv.Model):
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        currency_obj = self.pool.get('res.currency')
        res = {}
        for expense in self.browse(cr, uid, ids, context=context):
            currency = expense.journal_id.currency or expense.journal_id.company_id.currency_id
            res[expense.id] = {'amount_untaxed': 0.0, 
                               'amount_tax': 0.0, 
                               'amount_total':0.0,
                               'amount_statement': 0.0,
                               'amount_transfer': 0.0,
                               'amount_balance': 0.0,
                               'currency_id': currency.id,
                               'exchange_inv': (expense.exchange_rate and 1.0 / expense.exchange_rate or 0.0),
                            }
            for invoice in expense.invoice_ids:
                if invoice.state in ['cancel']:
                    continue
                res[expense.id]['amount_total'] += invoice.expense_total
                for tax_line in invoice.tax_line:
                    res[expense.id]['amount_tax'] += tax_line.amount
            res[expense.id]['amount_untaxed'] = res[expense.id]['amount_total'] - res[expense.id]['amount_tax']
            for statement in expense.statement_ids:
                if statement.statement_id.state in ['cancel']:
                    continue
                amount = statement.amount
                if statement.statement_id.currency.id != expense.currency_id.id:
                    amount = currency_obj.compute(cr, uid, 
                                            statement.statement_id.currency.id, 
                                            expense.currency_id.id, 
                                            statement.amount,
                                            context=dict(context, date=statement.date)) 
                res[expense.id]['amount_statement'] += statement.amount
            for transfer in expense.transfer_ids:
                if transfer.state in ['cancel']:
                    continue
                sign = 0.0
                amount = transfer.dst_amount
                if transfer.src_journal_id.id == expense.journal_id.id:
                    sign = 1.0
                    amount = transfer.src_amount
                elif transfer.dst_journal_id.id == expense.journal_id.id:
                    sign = -1.0
                res[expense.id]['amount_transfer'] += (amount * sign)
            res[expense.id]['amount_transfer_inv'] = res[expense.id]['amount_transfer'] * -1.0
            res[expense.id]['amount_statement_inv'] = res[expense.id]['amount_statement'] * -1.0
            res[expense.id]['amount_balance'] = ((res[expense.id]['amount_statement'] + res[expense.id]['amount_transfer']) * -1) - res[expense.id]['amount_total'] 
        return res
    
    def _get_expense_from_invoice(self, cr, uid, ids, context=None):
        res = {}
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        for invoice_id in ids:
            expense_invoice_ids = expense_invoice_obj.search(cr, uid, [('invoice_id','=',invoice_id)], context=context)
            for expense_invoice in self.pool.get('account.expense.invoice').browse(cr, uid, expense_invoice_ids, context=context):
                res[expense_invoice.expense_id.id] = True
        return res.keys()
    
    def _get_expense_from_statement(self, cr, uid, ids, context=None):
        res = {}
        stm_line_obj = self.pool.get('account.bank.statement.line')
        stm_line_ids = stm_line_obj.search(cr, uid, [('id','in',ids),('expense_id','!=',False)],context=context)
        for stm_line in stm_line_obj.browse(cr, uid, stm_line_ids, context=context):
            res[stm_line.expense_id.id] = True
        return res.keys()
    
    def _get_expense_from_transfer(self, cr, uid, ids, context=None):
        res = {}
        transfer_obj = self.pool.get('account.transfer')
        transfer_ids = transfer_obj.search(cr, uid, [('id','in',ids),('expense_id','!=',False)],context=context)
        for transfer in transfer_obj.browse(cr, uid, transfer_ids, context=context):
            res[transfer.expense_id.id] = True
        return res.keys()
    
    _name = 'account.expense'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Expense with multiple invoices and one payment'
    _order = 'name desc'
    _track = {
        'state': {
            'account_expense.mt_expense_done': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }
    _columns = {
            'company_id' : fields.many2one('res.company','Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'type': fields.selection([('expense','Expense'),
                                      ('paybill','Pay Bill'),
                                      ('expenditure','Expenditure')], string='Type', required=True, readonly=True),
            'name': fields.char('Number', size=32, required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'date': fields.date('Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'notes': fields.text('Notes', select=True, readonly=True, states={'draft':[('readonly',False)]}),
            'origin': fields.char('Source Document', size=64, help="Reference of the document that produced this invoice.", readonly=True, states={'draft':[('readonly',False)]}),
            'period_id': fields.many2one('account.period', string='Period', readonly=True, domain=[('state','<>','done')], 
                                         help="Keep empty to use the period of the validation(invoice) date.", states={'draft':[('readonly',False)]}),
            'journal_id': fields.many2one('account.journal','Journal', readonly=True, states={'draft':[('readonly',False)]},
                                          required=True, help="Cash Journal to pay the invoices"),
            'have_partner': fields.related('journal_id','have_partner',type='boolean',string='Have Partner',readonly=True),
            'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account', 
                                                   help="Analytic account for apply on the payment step",
                                                   domain=[('type','!=','view')], readonly=True, states={'draft':[('readonly',False)]}),
            'currency_id': fields.function(_amount_all, type='many2one', relation='res.currency', string='Currency', multi='all', store=True),
            'partner_id': fields.many2one('res.partner','Partner', readonly=True, states={'draft':[('readonly',False)]}, 
                                          help="Partner asocied to cash journal, usually an employee"),
            'invoice_ids': fields.one2many('account.expense.invoice','expense_id', string='Expense Lines', readonly=True, states={'pre-approve':[('readonly',False)],'confirm':[('readonly',False)],'draft':[('readonly',False)]}),
            'move_ids': fields.one2many('account.move','expense_id', string='Account Moves', readonly=True, states={'draft':[('readonly',False)]}),
            'statement_ids': fields.one2many('account.bank.statement.line','expense_id','Statement Lines', readonly=True, states={'draft':[('readonly',False)]}),
            'transfer_ids' : fields.one2many('account.transfer','expense_id', string='Money Transfers', readonly=True, states={'pre-approve':[('readonly',False)],'confirm':[('readonly',False)],'draft':[('readonly',False)]}),
            'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Amount',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['invoice_ids'], 20),
                    'account.invoice': (_get_expense_from_invoice, ['tax_line','invoice_line','state'], 20),
                }, multi='all', help="Total amount of expenses, included taxes."),
            'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Tax',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['invoice_ids'], 20),
                    'account.invoice': (_get_expense_from_invoice, ['tax_line','invoice_line','state'], 20),
                }, multi='all'),
            'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Untaxed',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['invoice_ids'], 20),
                    'account.invoice': (_get_expense_from_invoice, ['tax_line','invoice_line','state'], 20),
                }, multi='all'),
            'amount_statement': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Statement',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['statement_ids'], 20),
                    'account.bank.statement.line': (_get_expense_from_statement, ['amount','expense_id','type'], 20),
                }, multi='all', help="Total income amount payed to this pay bill"),
            'amount_statement_inv': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Statement',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['statement_ids'], 20),
                    'account.bank.statement.line': (_get_expense_from_statement, ['amount','expense_id','type'], 20),
                }, multi='all', help="Total income amount payed to this pay bill with possitive sign"),
            'amount_transfer': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Transfer',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['transfer_ids'], 20),
                    'account.transfer': (_get_expense_from_transfer, ['exchange_rate','src_amount','dst_amount','state'], 20),
                }, multi='all', help="Total income amount transferred to this expenditure"),
            'amount_transfer_inv': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Transfer',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['transfer_ids'], 20),
                    'account.transfer': (_get_expense_from_transfer, ['exchange_rate','src_amount','dst_amount','state'], 20),
                }, multi='all', help="Total income amount transferred to this expenditure with possitive sign"),
            'amount_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Balance',
                store={
                    'account.expense': (lambda self, cr, uid, ids, c={}: ids, ['transfer_ids','invoice_ids','statement_ids'], 20),
                    'account.invoice': (_get_expense_from_invoice, ['tax_line','invoice_line','state'], 20),
                    'account.bank.statement.line': (_get_expense_from_statement, ['amount','expense_id','type'], 20),
                    'account.transfer': (_get_expense_from_transfer, ['exchange_rate','src_amount','dst_amount','state'], 20),
                }, multi='all', help="The balance or difference amount, must be zero to done this document. Balance = Incomes - Expenses"),
            'exchange_rate': fields.float('Exchange Rate', digits_compute=dp.get_precision('Exchange'), readonly=True, states={'draft':[('readonly',False)]}),
            'exchange_inv': fields.function(_amount_all, string='1 / Exchange Rate', type='float', digits_compute=dp.get_precision('Exchange'), readonly=True, multi='all'),
            'state': fields.selection([('draft','Draft'),
                                       ('pre-confirm','Pre-Confirm'),
                                       ('confirm','Confirm'),
                                       ('pre-approve','Pre-Approve'),
                                       ('approve','Approve'),
                                       ('open','Validate'),
                                       ('paid','Paid'),
                                       ('done','Done'),
                                       ('cancel','Cancel')],string='State',track_visibility='onchange',readonly=True),
        }
    _defaults = {
            'name': '/',
            'type': lambda s,cr,u,c={}: c.get('expense_type','expense'),
            'company_id': lambda s,cr,u,c: s.pool.get('res.users').browse(cr,u,u).company_id.id,
            'date': lambda *a: time.strftime('%Y-%m-%d'),
            'exchange_rate': 1.0,
            'exchange_inv': 1.0,
            'state' : 'draft',
        }
    _sql_constraints = [('name_unique','unique(company_id,type,name)',_('The number must be unique!'))]
    
    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not vals.has_key('type'):
            vals['type'] = context.get('expense_type','expense')
        if vals.get('name','/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'account.expense.'+vals.get('type','expense'))
        return super(account_expense,self).create(cr, uid, vals, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        context = context or {}
        default = default or {}
        default['invoice_ids'] = []
        default['statement_ids'] = []
        default['transfer_ids'] = []
        default['move_ids'] = []
        default['name'] = '/'
        default['state'] = 'draft'
        return super(account_expense,self).copy(cr, uid, id, default=default, context=context)
    
    def action_open(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            for expense_invoice in expense.invoice_ids:
                if expense_invoice.state in ('draft','proforma','proforma2'):
                    netsvc.LocalService("workflow").trg_validate(uid, 'account.expense.invoice', expense_invoice.id, 'invoice_open', cr)
        return True
    
    def action_paid(self, cr, uid, ids, context=None):
        context = context or {}
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        for expense in self.browse(cr, uid, ids, context=context):
            for expense_invoice in expense.invoice_ids:
                if expense_invoice.state == 'paid':
                    continue
                expense_invoice_obj.invoice_pay_customer(cr, uid, [expense_invoice.id], context=context)
        return True
    
    
    def _get_reverse_lines(self, cr, uid, expense_invoice, lines, context=None):
        res = []
        for line in lines:
            l = {'name': line.name,
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'debit': line.credit,
                'credit': line.debit,
                'amount_currency': line.amount_currency * -1,
                'currency_id': line.currency_id.id,
                'invoice': line.invoice.id,
                }
            res.append((0,0,l))
            l1 = l.copy()
            l1['partner_id'] = expense_invoice.expense_id.partner_id.id
            l1['debit'] = line.debit
            l1['credit'] = line.credit
            l1['amount_currency'] = line.amount_currency
            res.append((0,0,l1))
        return res
        
    def _get_reverse_move(self, cr, uid, expense_invoice, move, lines, context=None):
        return {
                'ref': move.ref,
                'line_id': self._get_reverse_lines(cr, uid, expense_invoice, lines, context=context),
                'journal_id': move.journal_id.id,
                'date': move.date,
                'narration': move.narration,
                'period_id': move.period_id.id,
                'company_id': move.company_id.id,
                'expense_id': move.expense_id.id,
            }
    
    def action_generate_transfer(self, cr, uid, ids, context=None):
        return True
    
    def action_pre_approve(self, cr, uid, ids, context=None):
        return True
    
    def action_approve(self, cr, uid, ids, context=None):
        return True
    
    def action_paid_reverse(self, cr, uid, ids, context=None):
        context = context or {}
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        for expense in self.browse(cr, uid, ids, context=context):
            for expense_invoice in expense.invoice_ids:
                moves = []
                for move_line in  expense_invoice.payment_ids:
                    moves.append(move_line.move_id)
                for move in set(moves):
                    lines = []
                    for line in move.line_id:
                        if line.account_id.id == expense.journal_id.default_credit_account_id.id:
                            lines.append(line)
                    if lines:
                        s = self._get_reverse_move(cr, uid, expense_invoice, move, lines, context=context)
                        self.pool.get('account.move').create(cr, uid, 
                                            s, context=context)
        return True
    
    def action_done(self, cr, uid, ids, context=None):
        context = context or {}
        for expense in self.browse(cr, uid, ids, context=context):
            if expense.type == 'expense':
                continue
            difference = abs(expense.amount_total + expense.amount_statement + expense.amount_transfer)
            if difference > 0.01:
                raise osv.except_osv(_('Wrong Balance !'),
                                     _("The balance of expense must be zero. The actual balance on %s is %s %s"%(expense.name,expense.journal_id.currency.symbol or expense.journal_id.company_id.currency_id.symbol,difference)) )
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        for expense in self.browse(cr, uid, ids, context=context):
            for expense_invoice in expense.invoice_ids:
                if expense_invoice.state == 'cancel':
                    continue
                expense_invoice_obj.action_cancel(cr, uid, [expense_invoice.id], context=context)
        return True
            
    def action_cancel_draft(self, cr, uid, ids, *args):
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        wf_service = netsvc.LocalService("workflow")
        for expense in self.browse(cr, uid, ids):
            for expense_invoice in expense.invoice_ids:
                if expense_invoice.state == 'draft':
                    continue
                expense_invoice_obj.action_cancel_draft(cr, uid, [expense_invoice.id], *args)
        self.write(cr, uid, ids, {'state':'draft'})
        for exp_id in ids:
            wf_service.trg_delete(uid, 'account.expense', exp_id, cr)
            wf_service.trg_create(uid, 'account.expense', exp_id, cr)
        return True

    def validate_account_moves(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        move_obj = self.pool.get('account.move')
        for expense in self.browse(cr, uid, ids, context=context):
            for move in expense.move_ids:
                if move.state == 'draft':
                    move_obj.button_validate(cr, uid, [move.id], context=context)
        return True

    def button_reset_taxes(self, cr, uid, ids, context=None):
        expense_invoice_obj = self.pool.get('account.expense.invoice')
        for expense in self.browse(cr, uid, ids, context=context):
            for expense_invoice in expense.invoice_ids:
                if expense_invoice.state in ['draft']:
                    expense_invoice_obj.button_reset_taxes(cr, uid, [expense_invoice.id], context=context)
        return True

    def onchange_journal(self, cr, uid, ids, journal_id, exchange_rate, context=None):
        context = context or {}
        res = {'value': {}}
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        res['value']['currency_id'] = journal.currency and journal.currency.id or journal.company_id.currency_id.id
        if context.has_key('expense_partner_id'):
            res['value']['partner_id']  = context['expense_partner_id']
        else:
            res['value']['partner_id']  = journal.user_id and journal.user_id.partner_id.id or False
        res['value']['have_partner'] = journal.have_partner
        
        res['value']['exchange_rate'] = exchange_rate
        if journal.currency.id and journal.company_id.currency_id.id <> journal.currency.id:
            res['value']['exchange_rate'] = src_journal.currency.rate or journal.company_id.currency_id.rate or 0.0
        else:
            res['value']['exchange_rate'] = 1.0
        res['value']['exchange_inv'] = res['value']['exchange_rate'] and (1.0 / res['value']['exchange_rate']) or 0.0
 
        return res
    
    
class account_expense_invoice(osv.Model):

    def _amount_untaxed(self, cr, uid, ids, name, args, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for invoice in self.browse(cr, uid, ids):
            taxes = tax_obj.compute_all_included(cr, uid, invoice.tax_ids, invoice.expense_total, 1.0, product=invoice.product_id, partner=invoice.partner_id)
            res[invoice.id] = taxes['total']
            cur = invoice.currency_id
            res[invoice.id] = cur_obj.round(cr, uid, cur, res[invoice.id])
        return res
    
    def _to_invoice_ids(self, cr, uid, ids, context=None):
        res = {}
        for expense_invoice in self.browse(cr, uid, [x for x in ids if x != None], context=context):
            res[expense_invoice.invoice_id.id] = True
        return res.keys()
    
    def _to_invoice_id(self, cr, uid, id, context=None):
        return self.browse(cr, uid, id, context=context).invoice_id.id
    
    def _get_one_line(self, cr, uid, ids, name, args, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for expense_invoice in self.browse(cr, uid, ids, context=context):
            res[expense_invoice.id] = {
                    'product_id': False,
                    'description': '',
                    'expense_account_id': False,
                    'analytic_id': False,
                    'tax_ids': [],
                    'expense_untaxed': 0.0,
                    'expense_total': 0.0,
                }
            for line in expense_invoice.invoice_id.invoice_line:
                res[expense_invoice.id].update(self._one_line_field_read(cr, uid, ids, line, context=context))
                for tax in line.invoice_line_tax_id:
                    res[expense_invoice.id]['tax_ids'].append(tax.id)
                taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, line.price_subtotal, 1.0, product=line.product_id, partner=expense_invoice.partner_id)
                cur = expense_invoice.currency_id
                res[expense_invoice.id]['expense_untaxed'] = cur_obj.round(cr, uid, cur, taxes['total'])
                res[expense_invoice.id]['expense_total'] = cur_obj.round(cr, uid, cur, taxes['total_included'])
                break
        return res
    
    def _one_line_field_read(self, cr, uid, ids, line, context=None):
        return {
                'product_id': line.product_id.id,
                'description': line.name,
                'expense_account_id': line.account_id.id,
                'analytic_id': line.account_analytic_id.id,
            }
        
    def _one_line_field_map(self, cr, uid, id, context=None):
        return {
                'product_id': 'product_id',
                'description': 'name',
                'expense_account_id': 'account_id',
                'analytic_id': 'account_analytic_id',
                'tax_ids': 'invoice_line_tax_id',
                'expense_total': 'price_unit',
            }
    
    def _one_line_default_values(self, cr, uid, id, context=None):
        return {
                'name': '/',
            }
    
    def _one_line_values(self, cr, uid, expense_invoice, values, vals, context=None):
        if context is None: context = {}
        if not values: values = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        field_map = self._one_line_field_map(cr, uid, id, context=context)
        for k in vals.keys():
            if field_map.has_key(k):
                values[field_map[k]] = vals[k]
            else:
                values[k] = vals[k]
            if k == 'expense_total':
                values['discount'] = 0.0
                values['quantity'] = 1.0
                if expense_invoice:
                    taxes = tax_obj.compute_all_included(cr, uid, context.get('expense_invoice_tax_ids',expense_invoice.tax_ids),
                                                  vals[k], 1.0, product=expense_invoice.product_id, partner=expense_invoice.partner_id)
                    cur = expense_invoice.currency_id
                    values[field_map[k]] = cur_obj.round(cr, uid, cur, taxes['price_unit'])
                else:
                    values[field_map[k]] = tax_obj.compute_all_included(cr, uid, context.get('expense_invoice_tax_ids',[]),
                                                  vals[k], 1.0, context.get('expense_invoice_product_id',False), context.get('expense_invoice_partner_id',False))['price_unit']
        return values
        
    def _set_one_line(self, cr, uid, id, name, value, arg, context=None):
        line_obj = self.pool.get("account.invoice.line")
        expense_invoice = self.browse(cr, uid, id, context=context)
        line_id = len(expense_invoice.invoice_line)>0 and expense_invoice.invoice_line[0].id or False
        field_map = self._one_line_field_map(cr, uid, id, context=context)
        # Define the default dictionary values for the create 
        default_values = self._one_line_default_values(cr, uid, id, context=context)
        values = {}
        if not line_id:
            if default_values.has_key(field_map[name]):
                del default_values[field_map[name]]
            values = default_values.copy() 
        values = self._one_line_values(cr, uid, expense_invoice, values, {name: value}, context=context)    
        if line_id:
            line_obj.write(cr, uid, [line_id], values, context=context)
        else:
            line_obj.create(cr, uid, values, context=context)
        return True

    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        type_inv = context.get('type', 'in_invoice')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = context.get('company_id', user.company_id.id)
        type2journal = {'out_invoice': 'sale', 'in_invoice': 'purchase', 'out_refund': 'sale_refund', 'in_refund': 'purchase_refund'}
        journal_obj = self.pool.get('account.journal')
        res = journal_obj.search(cr, uid, [('type', '=', type2journal.get(type_inv, 'sale')),
                                            ('company_id', '=', company_id)],
                                                limit=1)
        return res and res[0] or False

    _name = "account.expense.invoice"
    _inherits = {'account.invoice': 'invoice_id'}
    _columns = {
            'expense_id': fields.many2one('account.expense', required=True, string='Expense'),
            'product_id': fields.function(_get_one_line,string="Product",type="many2one",obj="product.product",multi="expense_all",
                                          fnct_inv=_set_one_line),
            'description': fields.function(_get_one_line,string='Description', type="text", multi="expense_all",
                                           fnct_inv=_set_one_line),
            'expense_account_id': fields.function(_get_one_line,string="Expense Account",type="many2one",obj="account.account", 
                                                  multi="expense_all", fnct_inv=_set_one_line),
            'analytic_id': fields.function(_get_one_line, type="many2one", obj='account.analytic.account', string='Analytic', multi="expense_all",
                                           fnct_inv=_set_one_line),
            'tax_ids': fields.function(_get_one_line,type="many2many",relation='account.tax', string='Taxes', multi="expense_all",
                                       fnct_inv=_set_one_line),
            'expense_total': fields.function(_get_one_line, type="float", string='Total Expense', 
                                             digits_compute= dp.get_precision('Product Price'), multi="expense_all",
                                             fnct_inv=_set_one_line),
            'expense_untaxed': fields.function(_get_one_line, string='Expense  Untaxed', type="float", readonly=True,
                                              digits_compute= dp.get_precision('Account'), multi="expense_all"),
            'invoice_id': fields.many2one('account.invoice', string="Invoice", ondelete="cascade", required=True, select=True),
        }
    _defaults = {
            'expense_total': 0.0,
            'expense_untaxed': 0.0,
            'expense_account_id' : lambda s, cr, u, c={}: s.pool.get('ir.property').get(cr, u, 'property_account_expense_categ', 'product.category', context=c).id,
            'description': '/',
            'journal_id': _get_journal,
        }
    
    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        unlink_invoice_ids = []
        for expense_invoice in self.browse(cr, uid, ids, context=context):
            invoice_id = expense_invoice.invoice_id.id
            if not self.search(cr, uid, [('invoice_id', '=', invoice_id), ('id', '!=', expense_invoice.id)], context=context):
                 unlink_invoice_ids.append(invoice_id)
            unlink_ids.append(expense_invoice.id)
        self.pool.get('account.invoice').unlink(cr, uid, unlink_invoice_ids, context=context)
        return super(account_expense_invoice, self).unlink(cr, uid, unlink_ids, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if vals.get('tax_ids', False):
            tax_obj = self.pool.get('account.tax')
            context['expense_invoice_tax_ids'] = []
            for t in vals['tax_ids']:
                if t[0] == 2: continue
                context['expense_invoice_tax_ids'] += tax_obj.browse(cr, uid, t[2], context=context)
            if not vals.has_key('expense_total') and len(ids)==1:
                vals['expense_total'] = self.browse(cr, uid, ids[0], context=context).expense_total
        return super(account_expense_invoice, self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        values = self._one_line_default_values(cr, uid, id, context=context)
        for x in vals:
            if x in ('product_id',
                        'description',
                        'expense_account_id',
                        'analytic_id',
                        'tax_ids',
                        'expense_total',):
                values.update({x:vals[x]})
        if vals.has_key('tax_ids'):
            tax_obj = self.pool.get('account.tax')
            context['expense_invoice_tax_ids'] = []
            for t in vals['tax_ids']:
                if t[0] == 2: continue
                context['expense_invoice_tax_ids'] += tax_obj.browse(cr, uid, t[2], context=context)
        if vals.has_key('product_id'):
            context['expense_invoice_product_id'] = self.pool.get('product.product').browse(cr,uid,vals['product_id'],context=context)
        if vals.has_key('partner_id'):
            context['expense_invoice_partner_id'] = self.pool.get('res.partner').browse(cr,uid,vals['partner_id'],context=context)
        vals['invoice_line'] = [(0,0,self._one_line_values(cr, uid, None, None, values, context=context))]
        return super(account_expense_invoice, self).create(cr, uid, vals, context)
    
    def message_get_subscription_data(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').message_get_subscription_data(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
    
    def action_cancel(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').action_cancel(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        for exp_inv_id in ids:
            wf_service.trg_delete(uid, 'account.expense.invoice', exp_inv_id, cr)
            wf_service.trg_create(uid, 'account.expense.invoice', exp_inv_id, cr)
        return self.pool.get('account.invoice').action_cancel_draft(cr, uid, self._to_invoice_ids(cr, uid, ids), *args)
        
    def action_date_assign(self, cr, uid, ids, *args):
        return self.pool.get('account.invoice').action_date_assign(cr, uid, self._to_invoice_ids(cr, uid, ids), *args)
        
    def action_invoice_sent(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').action_invoice_sent(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
        
    def action_move_create(self, cr, uid, ids, context=None):
        account_move_obj = self.pool.get('account.move')
        self.pool.get('account.invoice').action_move_create(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
        for expense_invoice in self.browse(cr, uid, ids, context=context):
            account_move_obj.write(cr, uid, [expense_invoice.move_id.id], 
                                   {'expense_id':expense_invoice.expense_id.id}, context=context)
        return True
        
    def action_number(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').action_number(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context))
    
    def invoice_print(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').invoice_print(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
    
    def invoice_validate(self, cr, uid, ids, context=None):
        context = context or {}
        context['account_expense_invoice_ids'] = ids 
        return self.pool.get('account.invoice').invoice_validate(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
    
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        context = context or {}
        voucher_obj = self.pool.get("account.voucher")
        wf_service = netsvc.LocalService("workflow")
        for expense_invoice in self.browse(cr, uid, ids, context=context):
            val = {}
            val['date'] = expense_invoice.expense_id.date
            val['type'] = 'payment'
            val['company_id'] = expense_invoice.expense_id.company_id.id
            val['reference'] = expense_invoice.expense_id.name + str(expense_invoice.number and (' - ' + expense_invoice.number) or '')
            val['partner_id'] = self.pool.get('res.partner')._find_accounting_partner(expense_invoice.partner_id).id
            amount = expense_invoice.residual
            if expense_invoice.type in ('out_refund', 'in_refund'):
                amount = -expense_invoice.residual
            val['amount'] = amount
            val['journal_id'] = expense_invoice.expense_id.journal_id.id
            val['account_id'] = expense_invoice.expense_id.journal_id.default_debit_account_id.id
            payment_rate = 1.0
            if expense_invoice.expense_id.journal_id.currency.id and expense_invoice.expense_id.company_id.currency_id.id <> expense_invoice.expense_id.journal_id.currency.id:
                val['payment_rate'] = expense_invoice.expense_id.exchange_inv
            val['payment_rate'] = payment_rate
            val['payment_rate_currency_id'] = expense_invoice.expense_id.journal_id.currency.id or expense_invoice.expense_id.company_id.currency_id.id
            
            val['line_dr_ids'] = [(0,0,{})]
            val['line_dr_ids'][0][2]['account_analytic_id'] = expense_invoice.expense_id.account_analytic_id and expense_invoice.expense_id.account_analytic_id.id or 0
            val['line_dr_ids'][0][2]['currency_id'] = expense_invoice.expense_id.journal_id.currency.id or expense_invoice.expense_id.company_id.currency_id.id
            val['line_dr_ids'][0][2]['amount'] = amount
            val['line_dr_ids'][0][2]['name'] = expense_invoice.expense_id.origin
            move_line_ids = [x.id for x in expense_invoice.move_id.line_id if x.account_id.id == expense_invoice.account_id.id]
            val['line_dr_ids'][0][2]['move_line_id'] = move_line_ids and move_line_ids[0] or 0
            val['line_dr_ids'][0][2]['amount_unreconciled'] = expense_invoice.account_id.id #rev tofix
            val['line_dr_ids'][0][2]['amount_original'] = expense_invoice.account_id.id #rev to fix
            val['line_dr_ids'][0][2]['account_id'] = expense_invoice.account_id.id
            val['line_dr_ids'][0][2]['type'] = 'dr'
            val['line_dr_ids'][0][2]['date_due'] = expense_invoice.date_due
            val['line_dr_ids'][0][2]['date_original'] = expense_invoice.date_invoice
            ctx = context.copy()
            ctx['close_after_process'] = True
            ctx['invoice_type'] = expense_invoice.type
            ctx['invoice_id'] = expense_invoice.id,
            ctx['type'] = 'payment'
            ctx['expense_id'] = expense_invoice.expense_id.id
            voucher_id = voucher_obj.create(cr, uid, val, context=ctx)
            wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
            
        return self.write(cr, uid, ids, {'state':'paid'}, context=context)
    
    def test_paid(self, cr, uid, ids, *args):
        return self.pool.get('account.invoice').test_paid(cr, uid, self._to_invoice_ids(cr, uid, ids), *args)
    
    def confirm_paid(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').confirm_paid(cr, uid, self._to_invoice_ids(cr, uid, ids), context=context)
    
    def move_line_id_payment_get(self, cr, uid, ids, *args):
        return self.pool.get('account.invoice').move_line_id_payment_get(cr, uid, self._to_invoice_ids(cr, uid, ids), *args)
        
    def move_line_id_payment_gets(self, cr, uid, ids, *args):
        return self.pool.get('account.invoice').move_line_id_payment_gets(cr, uid, self._to_invoice_ids(cr, uid, ids), *args)
        
    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        return self.pool.get('account.invoice').onchange_journal_id(cr, uid, ids, journal_id=journal_id, context=context)
        
    def onchange_company_id(self, cr, uid, ids, company_id, part_id, type, invoice_line, currency_id):
        return self.pool.get('account.invoice').onchange_company_id(cr, uid, ids, company_id, part_id, type, invoice_line, currency_id)
        
    def onchange_invoice_line(self, cr, uid, ids, lines):
        return self.pool.get('account.invoice').onchange_invoice_line(cr, uid, ids, lines)
    
    def onchange_partner_bank(self, cursor, user, ids, partner_bank_id=False):
        return self.pool.get('account.invoice').onchange_partner_bank(cursor, user, ids, partner_bank_id=partner_bank_id)
           
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        return self.pool.get('account.invoice').onchange_partner_id(cr, uid, ids, type, partner_id,\
            date_invoice=date_invoice, payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)
        
    def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice):
        return self.pool.get('account.invoice').onchange_payment_term_date_invoice(cr, uid, ids, payment_term_id, date_invoice)
        
    
    def onchange_product(self, cr, uid, ids, product_id, partner_id, context=None):
        res = {'value': {}}
        if not partner_id:
            raise osv.except_osv(_('No Partner Defined !'),_("You must first select a partner !") )
        if not product_id:
            return res
        fpos_obj = self.pool.get('account.fiscal.position')
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        a = product.property_account_expense.id
        if not a:
            a = product.categ_id.property_account_expense_categ.id
        a = fpos_obj.map_account(cr, uid, partner.property_account_position, a)
        if a:
            res['value']['expense_account_id'] = a
            
        taxes = product.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        tax_ids = fpos_obj.map_tax(cr, uid, partner.property_account_position, taxes)
        res['value']['tax_ids'] = tax_ids
        res['value']['description'] = product.description or product.name
        
        return res
    
    def onchange_partner(self, cr, uid, ids, partner_id, context=None):
        res = {'value': {}}
        if not partner_id:
            return res
        res['value']['account_id'] = self.pool.get("res.partner").browse(cr, uid, partner_id, context=context).property_account_payable.id
        return res
    
    def onchange_expenese_total(self, cr, uid, ids, expense_total, context=None):
        res = {'value': {}}
        res['value']['check_total'] = expense_total
        return res
    
    def button_reset_taxes(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').button_reset_taxes(cr, uid, self._to_invoice_ids(cr, uid, ids, context=context), context=context)
    