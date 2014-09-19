# -*- coding: utf-8 -*-
# Copyright 2011 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from osv import osv
from osv import fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _

class account_vat_declaration_wizard(osv.osv):
    _name = 'account.vat.declaration.wizard'
    _types_selection = [
        ('monthly', 'Monthly'),
        ('bimonthly', 'Bi-Monthly'),
        ('quarterly', 'Quaterly'),
        ('yearly', 'Yearly'),
    ]
    _types_delta = {
        'monthly': relativedelta(months=1, days=-1),
        'bimonthly': relativedelta(months=2, days=-1),
        'quarterly': relativedelta(months=3, days=-1),
        'yearly': relativedelta(months=12, days=-1),
    }

    _columns = {
        'type': fields.selection(_types_selection, 'Type', required=True),
        'from_period_id': fields.many2one('account.period', 'Period From', required=True),
        'to_period_id': fields.many2one('account.period', 'Period To', required=True),
        'name': fields.char('Name', size=64, required=True),
        'decl_tmpl_id': fields.many2one('account.vat.decl.template', 'Declaration Template', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }
    _defaults = {
        'type': 'monthly',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.vat.decl', context=c),
    }

    def onchange_from_period(self, cr, uid, ids, period_from_id, decl_type, company_id, context=None):
        if context is None: context={}
        context['company_id'] = company_id
        ocv = {'value': {}}
        if not period_from_id or not decl_type:
            ocv['value']['to_period_id'] = False
            ocv['value']['decl_tmpl_id']  = False
            ocv['value']['name'] = ''
            return ocv
        #period_obj = self.pool.get('account.period')
        vatdecl_obj = self.pool.get('account.vat.decl')
        tmplvatdecl_obj = self.pool.get('account.vat.decl.template')
        period_to_id = None
        try:
            period_to_id = vatdecl_obj._get_period_to(cr, uid, period_from_id, decl_type, context)
        except osv.except_osv:
            raise osv.except_osv(_('Error'), _('No end period found for the current period / type combinaison'))
        template_id = tmplvatdecl_obj.find_by_period(cr, uid, decl_type, period_from_id, period_to_id, context)
        computed_name = tmplvatdecl_obj._get_computed_name(cr, uid, template_id, period_from_id, period_to_id)
        ocv['value'].update({
            'to_period_id': period_to_id,
            'decl_tmpl_id': template_id,
            'name': computed_name
        })
        return ocv

    def create_new_declaration(self, cr, uid, ids, context=None):
        if not ids:
            return False
        wizard = self.browse(cr, uid, ids[0], context)
        actmodel, actid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_vat_declaration', 'action_account_vat_decl')
        vatdecl_obj = self.pool.get('account.vat.decl')
        new_vatdecl_id = vatdecl_obj.create(cr, uid, {
            'name': wizard.name,
            'type': wizard.type,
            'decl_template_id': wizard.decl_tmpl_id.id,
            'from_period_id': wizard.from_period_id.id,
            'to_period_id': wizard.to_period_id.id,
            'company_id': wizard.company_id.id,
        })
        if new_vatdecl_id:
            vatdecl_obj.recompute_values(cr, uid, [new_vatdecl_id], context)
            act = self.pool.get(actmodel).read(cr, uid, actid, context=context)
            act.update({
                'res_id': new_vatdecl_id,
                'view_mode': 'form,tree',
            })
            return act
        return False

account_vat_declaration_wizard()
