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

class account_journal(osv.Model):
    _inherit = 'account.journal'
    
    _columns = {
            'is_einvoice': fields.boolean('Electronic Invoice'),
            'ejournal_id': fields.many2one('account.ejournal','Electronic Journal'),
        }
    _defaults = {
            'is_einvoice': False,
        }


class account_invoice(osv.Model):
    _inherit = 'account.invoice'
    
    _columns = {
            'is_einvoice': fields.related('journal_id','is_einvoice',string='Electronic Invoice',type='boolean',readonly=True),
            'einvoice_ids': fields.many2many('account.einvoice','account_einvoice_invoice_rel',
                                             'invoice_id','einvoice_id',string="Electronic Invoices",
                                             readonly=True),
        }