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

class account_expense(osv.Model):
    _inherit = 'account.expense'

    def action_approve(self, cr, uid, ids, context=None):
        for expense in self.browse(cr, uid, ids, context=context):
            if expense.type=='paybill' and not self.pool.get('res.currency').is_zero(cr, uid, expense.currency_id, expense.amount_balance):
                raise osv.except_osv(_('User Error!'),_('Te balance amount must be zero (current balance:%d)')%(expense.amount_balance))
        return super(account_expense,self).action_approve(cr, uid, ids, context=context)