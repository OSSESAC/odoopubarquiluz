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

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
            'internal_number': fields.char('Internal Number', 32, readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]}),
        }
    _defaults = {
            'internal_number': '/',
        }
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        res = super(purchase_order,self).wkf_confirm_order(cr, uid, ids, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            if order.internal_number == '/':
                self.write(cr, uid, [order.id], {'name':self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.seq'),
                                                    'internal_number':order.name}, context=context)
        return res