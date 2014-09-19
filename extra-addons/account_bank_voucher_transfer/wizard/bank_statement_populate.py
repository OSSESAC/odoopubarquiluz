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

from openerp.osv import osv

class account_voucher_populate_statement(osv.osv_memory):
    _inherit = "account.voucher.populate.statement"

    def get_statement_line_new(self,cr,uid,voucher,statement,context=None):
        res = super(account_voucher_populate_statement,self).get_statement_line_new(cr,uid,voucher,statement,context=context)
        if voucher.type == 'transfer':
            sign = -1.0
            account_id = voucher.transfer_id.src_journal_id.default_debit_account_id and voucher.transfer_id.src_journal_id.default_debit_account_id.id or res['account_id']
            res['name'] = voucher.transfer_id.name
            res['ref'] = voucher.transfer_id.origin
            for line in voucher.line_ids:
                if line.account_id.type == 'payable': 
                    sign = -1.0
                    account_id = line.account_id.id 
                if line.type == 'cr': sign = -1.0 * sign

            res['account_id'] = account_id 
            res['amount'] = sign * res['amount']
            res['type'] = (sign > 0) and 'customer' or 'supplier'
        return res