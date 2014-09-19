# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2012 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
from tools.translate import _
from openerp.tools.float_utils import float_round


class account_journal(osv.Model):
    _inherit = 'account.journal'
    _columns = {
            'is_paybill': fields.boolean('Paybill Journal'),
        }
    _defaults = {
            'is_paybill' : False,
        }

class account_bank_statement(osv.Model):
    
    def _get_complete_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for statement in self.browse(cr, uid, ids, context=context):
            res[statement.id] = "[%s] %s (%s)"%(statement.name,statement.journal_id.name,statement.date)
        return res
    
    _inherit = "account.bank.statement"
    _rec_name = 'complete_name'
    _columns = {
            'complete_name': fields.function(_get_complete_name,string="Complete Name",type='char'),
        }