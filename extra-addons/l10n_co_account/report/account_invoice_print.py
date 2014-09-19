# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from report import report_sxw
import netsvc

class report_account_invoice_print(report_sxw.rml_parse):
    _name = 'report.account.invoice.print'
    _cr = None
    _uid = None
    _context = None
    def __init__(self, cr, uid, name, context):
        super(report_account_invoice_print, self).__init__(cr, uid, name, context)
        self._cr = cr
        self._uid = uid
        self._context = context
        self.localcontext.update({
            'time': time,
            'convert': self.convert,
            'day': self.day,
            'month': self.month,
            'year': self.year,
            'pickings': self.get_pickings,
            'print_original': self.print_original,
        })

    def convert(self, amount, currency): return self.pool.get('ir.translation').amount_to_text(amount, 'co', currency or 'PESOS')
    
    def day(self, date): return self.pool.get('ir.translation').date_part(date, 'day', format='number' ,lang='co')
    
    def month(self, date): return self.pool.get('ir.translation').date_part(date, 'month', format='text' ,lang='co')
    
    def year(self, date): return self.pool.get('ir.translation').date_part(date, 'year', format='number' ,lang='co')
    
    def print_original(self, invoice_id):
        res = ""
        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(self._cr,self._uid,invoice_id,self._context)
        if invoice.state in ['open','paid']:
            if not invoice.is_print_original:
                res = "(ORIGINAL)"
                invoice_obj.write(self._cr,self._uid,[invoice_id],{'is_print_original':True},self._context)
            else:
                res = "(COPIA)"
        return res
    
    def get_pickings(self, invoice_id):
        res = ''
        sale_obj = self.pool.get('sale.order')
        self._cr.execute('select order_id from sale_order_invoice_rel where invoice_id=%s'%(invoice_id))
        order_ids = self._cr.fetchall()
        #netsvc.Logger().notifyChannel("get_pickings",netsvc.LOG_INFO, "order_ids=%s" % (order_ids))
        sale_ids = []
        for order in order_ids:
            sale_ids.append(order[0])
        
        for sale in sale_obj.browse(self._cr,self._uid,sale_ids):
            for picking in sale.picking_ids:
                res += picking.name + ' / '
        if res[-3:] == ' / ': res = res[:-3]
        return res

report_sxw.report_sxw(
    'report.account.invoice.print',
    'account.invoice',
    'addons/l10n_co_account/report/account_invoice_print.rml',
    parser=report_account_invoice_print,header="external"
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
