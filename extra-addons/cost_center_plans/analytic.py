# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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


class account_analytic_journal(osv.Model):
    _inherit = 'account.analytic.journal'
    _columns = {
            'journal_id' : fields.many2one('account.journal',string="Account Journal",help="This journal is used to make the financial cost center moves"),
            'charge_account_id': fields.related('journal_id','charge_account_id', type='many2one', relation='account.account', string='Charge Account', readonly=True,
                                                  help="Usually used in account moves of financial cost center")
        }

class account_analytic_plan_instance(osv.Model):
    _inherit = 'account.analytic.plan.instance'
    _columns = {
            'company_id': fields.many2one('res.company','Company', required=True),
            'charge_account_id': fields.related('journal_id','journal_id','charge_account_id', type='many2one', relation='account.account', string='Charge Account', readonly=True,
                                                  help="Usually used in account moves of financial cost center")
        }
    _defaults = {
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.analytic', context=c),
        }

class account_analytic_plan_instance_line(osv.Model):
    _inherit = 'account.analytic.plan.instance.line'
    _columns = {
            'account_cost_center': fields.related('analytic_account_id','account_cost_center', type='many2one', relation='account.account', string='Account Cost Center', readonly=True)
        }

class account_analytic_line(osv.Model):
    _inherit = 'account.analytic.line'
    _columns = {
        'account_move_line_ids' : fields.one2many('account.move.line','analytic_line_id',string="Account Move Lines",readonly=True),
        }