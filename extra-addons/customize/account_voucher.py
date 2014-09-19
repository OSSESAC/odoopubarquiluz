# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2014 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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

class account_voucher(osv.Model):
    _name = "account.voucher"
    _inherit = "account.voucher"
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        res = []
        for voucher in self.browse(cr, uid, ids, context=context):
            name = ''
            if voucher.number:
                name += '['+voucher.number
            if voucher.reference:
                if name:
                    name += ' / '+voucher.reference + '] '
                else:
                    name += '['+voucher.reference+'] '
            elif name:
                name += '] '
            name += voucher.partner_id.name + ' '
            name += "(%s %.2f)"%(voucher.currency_id.symbol, voucher.amount)
            res.append((voucher.id,name))
        return res
