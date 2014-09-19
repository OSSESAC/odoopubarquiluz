# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order,self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res['account_cc_id'] = order_line.account_analytic_id and order_line.account_analytic_id.account_cost_center \
                                and order_line.account_analytic_id.account_cost_center.id or False
        return res

class purchase_line_invoice(osv.osv_memory):
    _inherit = 'purchase.order.line_invoice'
    
    def makeInvoices(self, cr, uid, ids, context=None):
        res = super(purchase_line_invoice,self).makeInvoices(cr, uid, ids, context=context)
        invoice_ids = eval(res['domain'])[0][2]
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
            for line in invoice.invoice_line:
                account_cc_id = False
                for order_line in line.purchase_line_ids:
                    account_cc_id = order_line.account_analytic_id and order_line.account_analytic_id.account_cost_center \
                                and order_line.account_analytic_id.account_cost_center.id or False
                if account_cc_id and not line.account_cc_id:
                    self.pool.get('account.invoice.line').write(cr, uid, [line.id],{'account_cc_id': account_cc_id}, context=context)
        return res