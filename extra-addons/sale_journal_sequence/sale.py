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

class sale_order(osv.Model):
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            if vals.get('invoice_type_id',False):
                invoice_type = self.pool.get('sale_journal.invoice.type').browse(cr, uid, vals['invoice_type_id'], context=context)
                if invoice_type.sequence_id:
                    vals['name'] = self.pool.get('ir.sequence').get_id(cr, uid, invoice_type.sequence_id.id)
            else:
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale_order') or '/'
        return super(sale_order, self).create(cr, uid, vals, context=context)

