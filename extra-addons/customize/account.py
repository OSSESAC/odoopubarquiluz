# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011-2014 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
import openerp.addons.decimal_precision as dp

class account_journal(osv.Model):
    _name = "account.journal"
    _inherit = "account.journal"
    _columns = {
            'parent_invoice': fields.boolean('Has Parent Invoice'),
        }
    _defaults = {
            'parent_invoice': False,
        }

    def create(self, cr, uid, values, context=None):
        if not values.has_key('code'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'account.journal.code')
        return super(account_journal, self).create(cr, uid, values, context=context)


class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    _columns = {
            'parent_id' : fields.many2one('account.invoice',string="Related Invoice", 
                                            help="This field must be used to register the related invoice from a refound invoice"),
            'parent_invoice': fields.related('journal_id','parent_invoice', type='boolean', readonly=True, 
                                             string="Has Parent Invoice"),
        }

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        res = super(account_invoice,self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        res['parent_id'] = invoice.id
        return res
    
    def onchange_journal_id(self, cr, uid, ids, journal_id=False, context=None):
        res = super(account_invoice,self).onchange_journal_id(cr, uid, ids, journal_id=journal_id, context=context)
        if journal_id:
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            res['value']['parent_invoice'] = journal.parent_invoice
        return res

    
class account_account(osv.osv):
    
    def _compute_customize(self, cr, uid, ids, field_names, arg=None, context=None):
        if context is None:
            context ={}
        res = {}
        initial = self.__compute(cr, uid, ids, ['balance', 'debit', 'credit'], context=context)
        current = self.__compute(cr, uid, ids, ['balance', 'debit', 'credit'], context=context)
        for account in self.browse(cr, uid, ids, context=context):
            res[account.id] = {'debit_initial': 0.0, 'credit_initial': 0.0, 'balance_initial': 0.0,
                               'debit_current': 0.0, 'credit_current': 0.0, 'balance_current': 0.0}
            res[account.id]['debit_initial'] = initial[account.id]['debit']
            res[account.id]['credit_initial'] = initial[account.id]['credit']
            res[account.id]['balance_initial'] = initial[account.id]['balance']
            res[account.id]['debit_current'] = current[account.id]['debit']
            res[account.id]['credit_current'] = current[account.id]['credit']
            res[account.id]['balance_current'] = current[account.id]['balance']
        return res
    
    def _get_parent_id(self, cr, uid, code, company_id, context=None):
        res=False
        parent_code = code[:-1]
        while parent_code:
            parent_ids = self.search(cr, uid, [('company_id','=',company_id),('code','=',parent_code)], context=context)
            if parent_ids:
                parent = self.browse(cr, uid, parent_ids[0], context=context)
                if parent.type == 'view':
                    res = parent.id
                else:
                    res = parent.parent_id.id
                break
            parent_code = parent_code[:-1]
        return res
    
    _name = 'account.account'
    _inherit = 'account.account'
    _columns = {
            'balance_initial': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Initial Balance', multi='customize'),
            'credit_initial': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Initial Credit', multi='customize'),
            'debit_initial': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Initial Debit', multi='customize'),
            'balance_current': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Current Balance', multi='customize'),
            'debit_current': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Current Debit', multi='customize'),
            'credit_current': fields.function(_compute_customize, digits_compute=dp.get_precision('Account'), string='Current Credit', multi='customize'),
        }
    
    def create(self, cr, uid, values, context=None):
        if not values.has_key('parent_id'):
            values['parent_id'] = self._get_parent_id(cr, uid, values.get('code'), values.get('company_id'), context=context)
        return super(account_account, self).create(cr, uid, values, context=context)
