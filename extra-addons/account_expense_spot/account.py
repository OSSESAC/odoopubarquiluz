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
from openerp.tools.translate import _
import time
import netsvc


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def transfer_spot_get(self, cr, uid, invoice, spot_amount, context=None):
        res = super(account_invoice,self).transfer_spot_get(cr, uid, invoice, spot_amount, context=context)
        expense_invoice_ids = self.pool.get('account.expense.invoice').search(cr, uid, [('invoice_id','=',invoice.id)],context=context)
        if len(expense_invoice_ids) > 0:
            res['expense_id'] = expense_invoice_ids[0]
        return res
        
    def spot_voucher_get(self, cr, uid, invoice, trans, context=None):
        res = super(account_invoice,self).spot_voucher_get(cr, uid, invoice, trans, context=context)
        expense_invoice_ids = self.pool.get('account.expense.invoice').search(cr, uid, [('invoice_id','=',invoice.id)],context=context)
        if len(expense_invoice_ids) > 0:
            res['expense_id'] = expense_invoice_ids[0]
        return res