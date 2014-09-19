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
from openerp.tools.float_utils import float_round


class account_transfer(osv.Model):
    
    def _get_type (self, cr, uid, context=None):
        res = super(account_transfer,self)._get_type(cr, uid, context=context)
        res.append(('expense','Expense Transfer'))
        return res
    
    _inherit = 'account.transfer'
    _columns = {
        'type': fields.selection(_get_type,'Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'expense_id' : fields.many2one('account.expense', string='Account Expense', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def voucher_get(self, cr, uid, trans, context=None):
        res = super(account_transfer,self).voucher_get(cr, uid, trans,context=context)
        if trans.expense_id:
            res['expense_id'] = trans.expense_id.id
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        for trans in self.browse(cr, uid, ids, context=context):
            if trans.expense_id and trans.expense_id.state == 'done':
                raise osv.except_osv(_('User Error!'),_('You can not cancel a transfer associate to a expense in state done (Transfer: %s - Expense: %s)')%(trans.name,trans.expense_id.name))
        return super(account_transfer,self).action_cancel(cr, uid, ids, context=context)

class account_tax(osv.Model):
    
    _name = 'account.tax'
    _inherit = 'account.tax'

    def compute_all_included(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None):
        """
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = totalin2 = totalex2 = float_round(price_unit * quantity, precision)
        tin = []
        tex = []
        tin2 = []
        tex2 = []
        
        for tax in taxes:
            tin.append(tax)
            if not tax.price_include:
                tex2.append(tax)
            else:
                tin2.append(tax)
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        tin2 = self.compute_inv(cr, uid, tin2, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        for r in tin2:
            totalex2 += r.get('amount', 0.0)
        totlex_qty = 0.0
        totlex_qty2 = 0.0
        try:
            totlex_qty = totalex/quantity
            totlex_qty2 = totalex2/quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        tex2 = self._compute(cr, uid, tex2, totalex, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        for r in tex2:
            totalin2 -= r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex,
            'price_unit': totalin2,
        }
      
       
class account_voucher(osv.Model):
    _inherit = "account.voucher"
    _columns = {
            'expense_id': fields.many2one('account.expense', string='Account Expense'),
        }
    
    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if context.get('expense_id', False):
            vals['expense_id'] = context['expense_id']
        return super(account_voucher,self).create(cr, uid, vals, context=context)
    
    def account_move_get(self, cr, uid, voucher_id, context=None):
        context = context or {}
        res = super(account_voucher,self).account_move_get(cr, uid, voucher_id, context=context)
        expense = self.browse(cr, uid, voucher_id, context=context)
        if expense.expense_id:
            res['expense_id'] = expense.expense_id.id 
        return res

class bank_statement_line(osv.Model):
    _inherit = 'account.bank.statement.line'
    _columns = {
            'expense_id': fields.many2one('account.expense','Account Expense'),
        }


class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
            'is_expense': fields.boolean('Expense Journal'),
        }
    _defaults = {
            'is_expense' : False,
        }
    

class account_move(osv.Model):
    
    _name = 'account.move'
    _inherit = 'account.move'
    _columns = {
            'expense_id': fields.many2one('account.expense', string='Account Expense'),
        }