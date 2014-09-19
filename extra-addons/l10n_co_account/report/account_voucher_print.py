# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2000-2013 Teradata . Cubic ERP (<http://cubicerp.com).
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

class report_account_voucher_print(report_sxw.rml_parse):
    _name = 'report.account.voucher.print'
    _cr = None
    _uid = None
    def __init__(self, cr, uid, name, context):
        super(report_account_voucher_print, self).__init__(cr, uid, name, context)
        self._cr = cr
        self._uid = uid
        self.localcontext.update({
            'time': time,
            'convert': self.convert,
            'day': self.day,
            'month': self.month,
            'year': self.year,
        })

    def convert(self, amount, currency): return self.pool.get('ir.translation').amount_to_text(amount, 'co', currency or 'PESOS')
    
    def day(self, date): return self.pool.get('ir.translation').date_part(date, 'day', format='number' ,lang='co')
    
    def month(self, date): return self.pool.get('ir.translation').date_part(date, 'month', format='text' ,lang='co')
    
    def year(self, date): return self.pool.get('ir.translation').date_part(date, 'year', format='number' ,lang='co')
    

report_sxw.report_sxw(
    'report.account.voucher.print',
    'account.voucher',
    'addons/l10n_co_account/report/account_voucher_print.rml',
    parser=report_account_voucher_print,header="external"
)