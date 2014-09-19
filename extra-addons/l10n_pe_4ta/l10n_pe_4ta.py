# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
import time

class l10n_pe_4ta_suspension(osv.Model):
    _name = "l10n_pe_4ta.suspension"
    _columns = {
            'partner_id': fields.many2one('res.partner', string="Partner", required=True),
            'property_fiscalyear_id': fields.property('account.fiscalyear',
                                                      relation='account.fiscalyear',
                                                      type='many2one' ,
                                                      view_load=True,
                                                      string="fiscal Year", required=True),
            'name': fields.char('Order Number',16),
            'application_result': fields.selection([('valid','Valid'),
                                                    ('invalid','Invalid')], string='Application Result', required=True),
            'application_date': fields.date('Application Date'),
            'application_end': fields.date('Application End'),
        }
    _defaults = {
            'application_result': 'valid',
            'application_date': lambda *a: time.strftime('%Y-%m-%d'),
            'property_fiscalyear_id': lambda s,cr,u,c: s.pool.get('account.fiscalyear').find(cr,u,context=c),
            'application_end': lambda s,cr,u,c: s.pool.get('account.fiscalyear').browse(cr,u,s.pool.get('account.fiscalyear').find(cr,u,context=c),context=c).date_stop,
        }
    _sql_constraints = [('partner_name_uniq','unique(partner_id,name)', 
                         'Partner and order number must be unique!')]
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        return [(r['id'], (str("[%s%s] %s"%(r.property_fiscalyear_id.name,r.name and (' - '+r.name) or '',r.partner_id.name)) or '')) for r in self.browse(cr, uid, ids, context=context)]

    