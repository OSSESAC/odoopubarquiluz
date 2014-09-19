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

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'

    _columns = {
            'analytics_id': fields.many2one('account.analytic.plan.instance','Analytics Distribution',readonly=True, states={'draft':[('readonly',False)]}),
            'invoice_line_id': fields.many2one('account.invoice.line','Invoice Line',readonly=True, states={'draft':[('readonly',False)]}),
        }
    
class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'
    
    def _depreciation_move_get_item(self, cr, uid, line, context=None):
        res = super(account_asset_depreciation_line, self)._depreciation_move_get_item(cr, uid, line, context=context)
        res['depreciation_line_id'] = line.id
        return res
    
    def _depreciation_move_line_get_item(self, cr, uid, line, move_id, context=None):
        res = super(account_asset_depreciation_line,self)._depreciation_move_line_get_item(cr, uid, line, move_id, context=context)
        if line.asset_id.analytics_id:
            res['analytics_id'] = line.asset_id.analytics_id.id
        return res