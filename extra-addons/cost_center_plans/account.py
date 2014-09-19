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

class account_move(osv.osv):
    _inherit = "account.move"
    _columns = {
            'parent_move_analytic_id': fields.many2one('account.move','Analytic Move',ondelete="cascade",
                                                help="Parent account move for this analytic move"),
            'child_move_analytic_ids': fields.one2many('account.move','parent_move_analytic_id',string="Child Analytic Moves"),
        }
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('name','/') != '/' or vals.get('ref',False):
            for move in self.browse(cr, uid, ids, context=context):
                self.write(cr, uid, [ch.id for ch in move.child_move_analytic_ids], {'ref': '%s - %s'%(vals.get('name') or move.name,vals.get('ref') or move.ref or '')}, context=context)
        return super(account_move, self).write(cr, uid, ids, vals, context=context)
    
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _columns = {
            'analytic_line_id': fields.many2one('account.analytic.line','Analytic Line',ondelete="cascade"),
        }
    
    def post_analytic_line_create(self, cr, uid, analytic_line_id, move_line, analytic_plans_line, amount, context=None):
        if context is None:
            context = {}
        if amount and analytic_plans_line.analytic_account_id.account_cost_center and move_line.move_id.journal_id.analytic_journal_id.journal_id.charge_account_id:
            debit = amount<0 and amount * -1 or 0.0
            credit = amount>0 and amount or 0.0
            rate = analytic_plans_line.rate / 100
            vals = {'line_id': [(0,0,self._analytic_line_cost_get_item(cr, uid, analytic_line_id, move_line, analytic_plans_line, amount, context=context)),
                (0,0,{
                    'move_id' : move_line.move_id.id,
                    'analytic_account_id': False, 
                    'tax_code_id': False, 
                    'analytic_lines': [], 
                    'tax_amount': 0.0, 
                    'name': "%s (%s%%)"%(move_line.name, analytic_plans_line.rate), 
                    'ref': analytic_plans_line.plan_id.name, 
                    'currency_id': move_line.currency_id, 
                    'debit': credit,
                    'credit': debit, 
                    'product_id': move_line.product_id.id, 
                    'date_maturity': False, 
                    'date': move_line.date,
                    'amount_currency': move_line.amount_currency * rate, 
                    'product_uom_id': move_line.product_uom_id.id, 
                    'quantity': move_line.quantity * rate, 
                    'partner_id': move_line.partner_id.id, 
                    'account_id': move_line.move_id.journal_id.analytic_journal_id.journal_id.charge_account_id.id,
                    'analytic_line_id': analytic_line_id,
                })]}
            move_id = False
            for analytic_move_id in move_line.move_id.child_move_analytic_ids:
                move_id = analytic_move_id.id
                break
            if not move_id:
                if context.has_key('analytic_move_id_%s'%move_line.move_id.id):
                    move_id = context.get('analytic_move_id_%s'%move_line.move_id.id)
                else:
                    move_id = self.pool.get('account.move').create(cr, uid, {
                                                        'company_id': move_line.move_id.company_id.id,
                                                        'journal_id': move_line.move_id.journal_id.analytic_journal_id.journal_id.id,
                                                        'period_id': move_line.move_id.period_id.id,
                                                        'date': move_line.move_id.date,
                                                        'ref': context.has_key('invoice') and context.get('invoice').internal_number or move_line.move_id.ref,
                                                        'parent_move_analytic_id': move_line.move_id.id}, context=context)
                    context.update({'analytic_move_id_%s'%move_line.move_id.id:move_id})
            self.pool.get('account.move').write(cr, uid, [move_id], vals, context=context)
        return True
    
    def _analytic_line_cost_get_item(self, cr, uid, analytic_line_id, move_line, analytic_plans_line, amount, context=None):
        debit = amount<0 and amount * -1 or 0.0
        credit = amount>0 and amount or 0.0
        rate = analytic_plans_line.rate / 100
        return {
                'move_id' : move_line.move_id.id,
                'analytic_account_id': False, 
                'tax_code_id': False, 
                'analytic_lines': [], 
                'tax_amount': 0.0, 
                'name': "%s (%s%%)"%(move_line.name, analytic_plans_line.rate), 
                'ref': analytic_plans_line.plan_id.name, 
                'currency_id': move_line.currency_id, 
                'debit': debit,
                'credit': credit, 
                'product_id': move_line.product_id.id, 
                'date_maturity': False, 
                'date': move_line.date,
                'amount_currency': move_line.amount_currency * rate, 
                'product_uom_id': move_line.product_uom_id.id, 
                'quantity': move_line.quantity * rate, 
                'partner_id': move_line.partner_id.id, 
                'account_id': analytic_plans_line.analytic_account_id.account_cost_center.id,
                'related_account_id': move_line.account_id.id,
                'analytic_line_id': analytic_line_id,
            }