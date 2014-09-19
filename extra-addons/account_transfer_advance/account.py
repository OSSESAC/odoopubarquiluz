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

class account_transfer(osv.osv):
    
    def _get_type (self, cr, uid, context=None):
        res = super(account_transfer,self)._get_type(cr, uid, context=context)
        res.append(('advance_supplier','Supplier Advance Transfer'))
        res.append(('advance_customer','Customer Advance Transfer'))
        return res
    
    _inherit = 'account.transfer'
    _columns = {
            'type': fields.selection(_get_type,'Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'purchase_id': fields.many2one('purchase.order','Purchase Order'),
            'sale_id': fields.many2one('sale.order','Sale Order'),
        }
    
class account_journal(osv.Model):
    _inherit = "account.journal"
    _columns = {
            'is_cash_advance': fields.boolean('Cash in Advance Transfer'),
        }
    _defaults = {
            'is_cash_advance': False,
        }