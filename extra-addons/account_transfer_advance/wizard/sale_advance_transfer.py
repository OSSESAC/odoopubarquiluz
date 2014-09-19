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

from openerp.osv import fields, osv
from tools.translate import _
import time

class sale_advance_transfer(osv.osv_memory):
    _name = "sale.advance.transfer"
    _description = "Sale Advance Transfer"
    _columns = {
            'amount': fields.float('Amount to Advance', required=True),
            'journal_id': fields.many2one('account.journal', string="Destinity Journal", required=True,
                                          help="This journal keep  the cash advances, usually is a bank account or cash box"),
        }

    def do_advance_transfer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_id = context.get('active_id')
        transfer_obj = self.pool.get('account.transfer')
        form = self.browse(cr, uid, ids, context=context)[0]
        sale = self.pool.get("sale.order").browse(cr,uid,sale_id,context=context)
        if not sale:
            raise osv.except_osv(_('Error'),_('Sale order not found (id:%s)',sale_id))
        if not sale.partner_id.property_sale_advance_journal:
            raise osv.except_osv(_('Error'),_('Sale advance journal not found. Please fill this in the partner form.'))
        value = transfer_obj.onchange_journal(cr, uid, ids, sale.partner_id.property_sale_advance_journal.id, form.journal_id.id,
                                       time.strftime('%Y-%m-%d'), 1.0, form.amount)['value']
        transfer_obj.create(cr,uid,{
                                'company_id': sale.company_id.id,
                                'type': 'advance_customer',
                                'origin': sale.name,
                                'src_journal_id': sale.partner_id.property_sale_advance_journal.id,
                                'dst_partner_id': sale.partner_id.id,
                                'src_amount': form.amount,
                                'dst_journal_id': form.journal_id.id,
                                'dst_amount': value['dst_amount'],
                                'exchange_rate': value['exchange_rate'],
                                'sale_id': sale.id,
                            },context=context)
        
        return {'type': 'ir.actions.act_window_close'}