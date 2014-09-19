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

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _analytic_posting(self, cr, uid, il, context=None):
        res = super(account_invoice, self)._analytic_posting(cr, uid, il, context=context)
        return res and not il.get('asset_id',False)
    
    def action_cancel(self, cr, uid, ids, context=None):
        super(account_invoice,self).action_cancel(cr, uid, ids, context=context)
        asset_ids = []
        for invoice in self.browse(cr, uid, ids, context=context):
            for line in invoice.invoice_line:
                asset_ids += [a.id for a in line.asset_ids]
        asset_ids and self.pool.get('account.asset.asset').unlink(cr, uid, asset_ids, context=context)
        return True
    
class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
            'asset_ids': fields.one2many('account.asset.asset','invoice_line_id','Assets')
        }
    
    def asset_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line,self).asset_get_item(cr, uid, line, context=context)
        res['invoice_line_id'] = line.id
        if line.analytics_id:
            res['analytics_id'] = line.analytics_id.id 
        return res
    
    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line,self).move_line_get_item(cr, uid, line, context=context)
        if res.has_key('analytics_id') and line.asset_category_id:
            del res['analytics_id']
        return res
    
    
class account_move(osv.osv):
    _inherit = "account.move"
    _columns = {
            'depreciation_line_id': fields.many2one('account.asset.depreciation.line','Depreciation Line', ondelete="cascade"),
        }
    
    
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    
    def _analytic_line_cost_get_item(self, cr, uid, analytic_line_id, move_line, analytic_plans_line, amount, context=None):
        res = super(account_move_line,self)._analytic_line_cost_get_item(cr, uid, analytic_line_id, move_line, analytic_plans_line, amount, context=context)
        if move_line.asset_id:
            res['asset_id'] = move_line.asset_id.id
        return res