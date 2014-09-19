# -*- coding: utf-8 -*-
# Copyright 2011 Thamini S.à.R.L    This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import locale
from osv import osv
from osv import fields
import decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

WRITABLE_ONLY_IN_DRAFT = dict(readonly=True, states={'draft': [('readonly', False)]})

class acctvat_decl_template(osv.osv):
    _name = 'account.vat.decl.template'
    _types_selection = [
        ('monthly', 'Monthly'),
        ('bimonthly','Bi-Monthly'),
        ('quarterly', 'Quaterly'),
        ('yearly', 'Yearly'),
    ]
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'valid_from': fields.date('Valid From', required=True),
        'valid_to': fields.date('Valid To',
                                help='Define the end of validity of this declaration, if not precised this document is ALWAYS valid'),
        'type': fields.selection(_types_selection, 'Type', required=True),
        'computed_name': fields.char('Computed Name', size=64,
                                help='The computed name of new declaration base on this one'),
        'case_template_ids': fields.one2many('account.vat.decl.case.template', 'decl_template_id', 'Cases Template'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'type': 'monthly',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.vat.decl', context=c),
    }

    def find_by_period(self, cr, uid, decl_type, period_from_id, period_to_id, context=None):
        if context is None: context={}
        period_obj = self.pool.get('account.period')
        period_from = period_obj.browse(cr, uid, period_from_id, context)
        period_to = period_obj.browse(cr, uid, period_to_id, context)
        company_id = context.get('company_id',self.pool.get('res.company')._company_default_get(cr, uid, 'account.vat.decl', context=context))
        tmpl_ids = self.search(cr, uid, [('company_id','=',company_id),
                '&',
                    ('type','=',decl_type),
                    ('valid_from','<=',period_from.date_start),
                    '|',
                        ('valid_to','=',False),
                        '&',('valid_to','!=',False),('valid_to','>=',period_to.date_stop)
                ])
        if not tmpl_ids:
            raise osv.except_osv(_('Error'), _('No VAT declaration template found'))
        return tmpl_ids[0]

    def _get_computed_name(self, cr, uid, ids, period_from_id, period_to_id, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if context is None:
            context = {}
        template = self.browse(cr, uid, ids[0], context=context)
        # switch to user locale
        old_locale = locale.getlocale(locale.LC_TIME)
        new_locale_code = context.get('lang', 'C').lower()
        new_locale_found = False
        for l in [ k for k in locale.locale_alias.keys() if k.startswith(new_locale_code) ]:
            try:
                locale.setlocale(locale.LC_TIME, locale.locale_alias[l])
                new_locale_found = True
                break
            except locale.Error:
                pass
        if not new_locale_found:
            locale.setlocale(locale.LC_TIME, 'C')

        period_obj = self.pool.get('account.period')
        pfrom_record = period_obj.browse(cr, uid, period_from_id, context=context)
        pfrom_dt = datetime.strptime(pfrom_record.date_start, '%Y-%m-%d')
        pto_record = period_obj.browse(cr, uid, period_to_id, context=context)
        pto_dt = datetime.strptime(pto_record.date_start, '%Y-%m-%d')
        vals = {
            'from_Y': pfrom_dt.strftime('%Y'),
            'from_B': pfrom_dt.strftime('%B'),
            'from_m': pfrom_dt.strftime('%m'),
            'to_Y': pto_dt.strftime('%Y'),
            'to_B': pto_dt.strftime('%B'),
            'to_m': pto_dt.strftime('%m'),
        }
        try:
            computedname = template.name + ' - ' + pfrom_record.name
        except Exception:
            computedname = ''
        # restore old locale
        locale.setlocale(locale.LC_TIME, '.'.join(map(str, [ l for l in old_locale if l is not None ])))
        # return final result
        return computedname

    def _template_check_recursion(self, cr, uid, id, context=None):
        vatcase_deps = {}
        vatcase_obj = self.pool.get('account.vat.decl.case.template')
        vatcase_ids = vatcase_obj.search(cr, uid, [('decl_template_id','=',id)],
                                         context=context)

        def checkvatdict(caseid):
            vatcase_deps.setdefault(caseid, {'d': set(), 'r': set()})

        for vatcase in vatcase_obj.browse(cr, uid, vatcase_ids, context=context):
            checkvatdict(vatcase.id)
            crev = vatcase_deps[vatcase.id]['r']
            for line in vatcase.line_ids:
                value, = line.get_by_record()
                if value and value._name == 'account.vat.decl.case.template':
                    checkvatdict(value.id)
                    vdep = vatcase_deps[value.id]['d']

                    # for parent + current cases add depend to VALUE
                    for c in list(crev) + [vatcase.id]:
                        checkvatdict(c)
                        vatcase_deps[c]['d'].update([value.id])
                        vatcase_deps[c]['d'].update(vdep)

                    # for child + current value add reverse to VATCASE
                    for c in list(vdep) + [value.id]:
                        vatcase_deps[c]['r'].update([vatcase.id])
                        vatcase_deps[c]['r'].update(crev)
            if vatcase_deps[vatcase.id]['d'].intersection(vatcase_deps[vatcase.id]['r']):
                return False

        for k, deps in vatcase_deps.iteritems():
            if deps['d'].intersection(deps['r']):
                return False
        return True

    def add_case_depends(self, cr, uid, id, stack=None, context=None):
        if stack is None:
            stack = []
        if id in stack:
            return stack.index(id)
        vatcase_obj = self.pool.get('account.vat.decl.case.template')
        vmax = []
        for line in vatcase_obj.browse(cr, uid, id, context=context).line_ids:
            value, = line.get_by_record()
            if not value:
                continue
            if value._name == 'account.vat.decl.case.template':
                result = self.add_case_depends(cr, uid, value.id, stack, context)
                vmax.append(result)
        if not vmax:
            stack.append(id)
        else:
            stack.insert(max(vmax)+1, id)
        return stack.index(id)

    def _generate_compute_graph(self, cr, uid, id, context=None):
        account_stack = set()
        taxcode_stack = set()
        journal_dict = {}
        vatcase_stack = []

        if isinstance(id, (list, tuple)):
            id = id[0]
        if not self._template_check_recursion(cr, uid, id, context=context):
            raise osv.except_osv(_('Error'), _('The VAT template have loop in case dependencies'))

        vatcase_obj = self.pool.get('account.vat.decl.case.template')
        vatcase_ids = vatcase_obj.search(cr, uid, [('decl_template_id','=',id)], context=context)

        for vatcase in vatcase_obj.browse(cr, uid, vatcase_ids, context=context):
            for line in vatcase.line_ids:
                value, = line.get_by_record()
                if not value:
                    continue
                if value._name == 'account.account':
                    account_stack.add(value.id)
                elif value._name == 'account.tax.code':
                    taxcode_stack.add(value.id)
                elif value._name == 'account.vat.decl.case.template':
                    self.add_case_depends(cr, uid, value.id, vatcase_stack, context)
                #YT 21/09/2012
                value_journal = line.get_by_record(type="account.journal")
                if value_journal:
                    if value._name not in journal_dict:
                        journal_dict[value._name] = {}
                    if value.id not in journal_dict[value._name]:
                        journal_dict[value._name][value.id] = set()
                    journal_dict[value._name][value.id].add(value_journal[0].id)
                        
            self.add_case_depends(cr, uid, vatcase.id, vatcase_stack, context)
        return {
            'account.account': list(account_stack),
            'account.tax.code': list(taxcode_stack),
            'account.vat.decl.case.template': list(vatcase_stack),
            'account.journal': journal_dict,
        }

acctvat_decl_template()

class acctvat_decl_case_template(osv.osv):
    _name = 'account.vat.decl.case.template'
    #_order = "decl_template_id, sequence, RPAD(number,16,' ') ASC"
    _order = "decl_template_id, sequence ASC"

    def _get_case_summary(self, cr, uid, ids, fname, args, context=None):
        result = {}
        vatcaseline_obj = self.pool.get('account.vat.decl.case.line.template')
        vatcaseline_type_field = vatcaseline_obj.fields_get(cr, uid, ['type'], context=context)
        vatcaseline_types = dict(vatcaseline_type_field['type']['selection'])

        for case in self.browse(cr, uid, ids, context=context):
            summary = []
            for line in case.line_ids:
                summary.append((line.sign, vatcaseline_types[line.type], line.value))
            if not summary:
                result[case.id] = u''
                continue
            def display_line(i, sign, type_, value):
                if i == 0 and sign == '+':
                    sign = ''
                pad = i>1 and ' ' or ''
                return '%s%s%s (%s)' % (sign, pad, type_, value)
            summary_text = ' '.join([ display_line(i, *s) for i, s in enumerate(summary) ])
            result[case.id] = summary_text
        return result

    _columns = {
        'decl_template_id': fields.many2one('account.vat.decl.template', 'Declaration Template', required=True, ondelete='cascade'),
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
        'sequence': fields.integer('Sequence'),
        'number': fields.char('Number', size=16, required=True),
        'line_ids': fields.one2many('account.vat.decl.case.line.template',
                                    'case_template_id', 'Lines'),
        'summary': fields.function(_get_case_summary, type='text', string='Summary', readonly=True, method=True),
        'company_id': fields.related('decl_template_id','company_id',type='many2one',obj='res.company',string='Company'),
    }
    _defaults = {
        'sequence': 0,
    }

    _sql_constraints = [
        ('unique_number_per_decl_template', 'UNIQUE(decl_template_id, number)', 'Case Number must be unique per Declaration Template'),
    ]
acctvat_decl_case_template()

class acctvat_decl_case_line_template(osv.osv):
    _name = 'account.vat.decl.case.line.template'
    _signs_selection = [
        ('-', '-'),
        ('+', '+'),
    ]
    _value_references_selection = [
        ('account.tax.code', 'Tax Code'),
        ('account.account', 'Account'),
        ('account.vat.decl.case.template', 'Case'),
    ]
    _value_search_map = {
        'account.tax.code': 'code',
        'account.account': 'code',
        'account.vat.decl.case.template': 'number',
        'account.journal': 'code',
    }

    _columns = {
        'case_template_id': fields.many2one('account.vat.decl.case.template', 'Case Template', required=True, ondelete='cascade'),
        'sequence': fields.integer('Selection'),
        'sign': fields.selection(_signs_selection, 'Sign', required=True),
        'type': fields.selection(_value_references_selection, 'Type', required=True, size=32),
        'value': fields.char('Value', required=True, size=128),
        'journal_code': fields.char('Journal Code', size=256, help="Code journal. Empty to find all journals."), #YT 21/9/2012
        'coefficient' : fields.boolean('Coefficient'), #YT 21/9/2012
        'python_coefficient': fields.text('Coefficient Python Code', required=True, help="Python code apply to calculate the coefficent. By default 1."), #YT 21/9/2012
        'company_id': fields.related('case_template_id','decl_template_id','company_id',type='many2one',obj='res.company',string='Company'),
    }

    _defaults = {
        'sequence': 0,
        'type': 'account.tax.code',
        'sign': '+',
        'coefficient' : False,
        'python_coefficient': '''# table: base.element object or None\n# cache: Cache\n# value: Value\n\n#result = table.get_element_percent(cr,uid,'COD_TABLE','COD_ELEMENT')/100\n\nresult = 1''',
    }

    def get_by_record(self, cr, uid, ids, type=None, context=None):
        records = []
        for line in self.browse(cr, uid, ids, context=context):
            model = line.type
            value = line.value
            if type == 'account.journal':
                model = type
                value = line.journal_code
                if not value:
                    return []
            model_obj = self.pool.get(model)
            model_search_field = self._value_search_map[model]
            resids = model_obj.search(cr, uid, [(model_search_field,'=',value),('company_id','=',line.company_id.id)], context=context)
            if not resids or (resids and len(resids) != 1):
                raise osv.except_osv(_('Error'), _('Unable to find unique %s with %s = %s') % (model, model_search_field, value))
            res = model_obj.browse(cr, uid, resids[0], context=context)
            records.append(res)
        return records

acctvat_decl_case_line_template()

# Objects
class acctvat_decl(osv.osv):
    _name = 'account.vat.decl'
    _types_selection = [
        ('monthly', 'Monthly'),
        ('bimonthly','Bi-Monthly'),
        ('quarterly', 'Quaterly'),
        ('yearly', 'Yearly'),
    ]
    _types_delta = {
        'monthly': relativedelta(months=1, days=-1),
        'bimonthly': relativedelta(months=2, days=-1),
        'quarterly': relativedelta(months=3, days=-1),
        'yearly': relativedelta(months=12, days=-1),
    }
    _states_selection = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ]
    _columns = {
        'decl_template_id': fields.many2one('account.vat.decl.template', 'Declaration Template', required=True, **WRITABLE_ONLY_IN_DRAFT),
        'name': fields.char('Name', size=64, required=True, **WRITABLE_ONLY_IN_DRAFT),
        'from_period_id': fields.many2one('account.period', 'Period From', required=True, **WRITABLE_ONLY_IN_DRAFT),
        'to_period_id': fields.many2one('account.period', 'Period To', required=True, **WRITABLE_ONLY_IN_DRAFT),
        'type': fields.selection(_types_selection, 'Type', required=True, **WRITABLE_ONLY_IN_DRAFT),
        'case_ids': fields.one2many('account.vat.decl.case', 'decl_id', 'Cases', **WRITABLE_ONLY_IN_DRAFT),
        'note': fields.text('Note', help='Allow to write so note about the declaration'),
        'state': fields.selection(_states_selection, 'State', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, **WRITABLE_ONLY_IN_DRAFT),
    }
    _defaults = {
        'state': 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.vat.decl', context=c),
    }

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def _get_period_to(self, cr, uid, from_period_id, decl_type, context=None):
        period_obj = self.pool.get('account.period')
        from_period = period_obj.browse(cr, uid, from_period_id, context=context)
        from_period_start_dt = datetime.strptime(from_period.date_start, '%Y-%m-%d')
        to_period_start_dt = from_period_start_dt + self._types_delta[decl_type]
        return period_obj.find(cr, uid, to_period_start_dt, context)[0]

    def onchange_from_period(self, cr, uid, ids, from_period_id, type_, decl_template_id, context=None):
        decl_tmpl_obj = self.pool.get('account.vat.decl.template')
        #period_obj = self.pool.get('account.period')
        ocv = {'value': {'to_period_id': False}}
        if not from_period_id or (not type_ and not decl_template_id):
            return ocv
        if not type_:
            try:
                tmpl = decl_tmpl_obj.browse(cr, uid, decl_template_id, context=context)
                type_ = tmpl.type
            except AttributeError:
                return ocv # default value
        try:
            to_period_id = self._get_period_to(cr, uid, from_period_id, type_, context)
            ocv['value']['to_period_id'] = to_period_id
        except osv.except_osv:
            pass # no period found?
        return ocv

    def _compute_values(self, cr, uid, vatdecl_record, compute_graph, context=None):
        if context is None: context = {}
        context.update({'company_id': vatdecl_record.company_id.id})
        #cache = {}
        period_obj = self.pool.get('account.period')
        period_ids = tuple(period_obj.build_ctx_periods(cr, uid,
                                            vatdecl_record.from_period_id.id,
                                            vatdecl_record.to_period_id.id))
        precision_obj = self.pool.get('decimal.precision')
        precision = precision_obj.precision_get(cr, uid, 'Account')
        move_states = ('draft', 'posted')
        cache = {}

        # account.account
        account_model = 'account.account'
        account_cache = cache.setdefault(account_model, {})
        account_obj = self.pool.get(account_model)
        account_ids = compute_graph.get(account_model, [])
        #YT 11/9/2012
        if account_ids:
            ctx = {'periods': period_ids, 'initial_bal': False, 'company_id': vatdecl_record.company_id.id}
            if 'account.journal' in compute_graph:
                journal_ids = compute_graph.get('account.journal',[])
                if journal_ids:
                    ctx['journal_id'] = journal_ids
            
            result = account_obj.read(cr, uid, account_ids, ['balance'], context=ctx)
            for a in result:
                #YT 11/9/2012
                #model_cache[a['id']] = a['balance']
                account_cache[a['id']] = a['balance']

        # account.tax.code
        taxcode_model = 'account.tax.code'
        taxcode_cache = cache.setdefault(taxcode_model, {})
        taxcode_obj = self.pool.get(taxcode_model)
        taxcode_ids = compute_graph.get(taxcode_model, {})
        ctx = {'based_on': 'invoices', 'company_id': vatdecl_record.company_id.id}
        where = ' AND line.period_id IN %s AND move.state IN %s '
        where_params = (period_ids, move_states)
        #_logger.info('taxcode_ids:%s'%(taxcode_ids))
        if taxcode_ids:
            #YT 21/9/2012
            if 'account.journal' in compute_graph:
                result = {}
                for taxcode in taxcode_ids:
                    result[taxcode] = 0.0
                    if ('account.tax.code' in compute_graph['account.journal']) and (taxcode in compute_graph['account.journal']['account.tax.code']):
                        journal_ids = compute_graph['account.journal']['account.tax.code'].get(taxcode,set())
                        result[taxcode] += taxcode_obj._sum(cr, uid, [taxcode], None, None, ctx, where + ' AND line.journal_id IN %s ', (where_params[0],where_params[1],tuple(journal_ids)))[taxcode]
                    else:
                        result[taxcode] += taxcode_obj._sum(cr, uid, [taxcode], None, None, ctx, where, where_params)[taxcode]
            else:
                result = taxcode_obj._sum(cr, uid, taxcode_ids, None, None, ctx, where, where_params)
            _logger.info('result:%s'%(result))
            taxcode_cache.update(result)

        # account.vat.decl.case.template
        vatcase_model = 'account.vat.decl.case.template'
        vatcase_cache = cache.setdefault(vatcase_model, {})
        vatcase_obj = self.pool.get(vatcase_model)
        vatcase_ids = compute_graph.get(vatcase_model, {})
        vatcase_line_sign = {'+': 1, '-': -1}
        localdict = {'cr':cr, 'uid':uid, 'table': self.pool.get('base.element')}
        for vatcase in vatcase_obj.browse(cr, uid, vatcase_ids, context=context):
            result = 0.0
            for line in vatcase.line_ids:
                value, = line.get_by_record()
                if not value:
                    continue
                coeff = 1.0
                #_logger.info("_compute_values value:%s - cache:%s - vatcase_line_sign:%s - line:%s"%(value,cache,vatcase_line_sign,line.python_coefficient))
                #_logger.info("_compute_values value._name:%s - value.id:%s - cache[value._name]:%s"%(value._name,value.id,cache[value._name]))
                if line.coefficient:
                    localdict['cache'] = cache
                    localdict['value'] = value
                    exec line.python_coefficient in localdict
                    coeff = localdict.get('result', 1)
                result += cache[value._name][value.id] * vatcase_line_sign[line.sign] * coeff
            result = round(result, precision)
            vatcase_cache[vatcase.id] = result
        return cache

    def recompute_values(self, cr, uid, ids, context=None):
        """ recompute all cases value on the requested vat declaration ids """
        vatcase_obj = self.pool.get('account.vat.decl.case')

        for vatdecl in self.browse(cr, uid, ids, context=context):
            vatdecl_id = vatdecl.id
            if vatdecl.state != 'draft':
                continue # skip non draft declarations
            decl_template = vatdecl.decl_template_id
            # generate compute graph and compute values
            compgraph = decl_template._generate_compute_graph()
            cache = self._compute_values(cr, uid, vatdecl, compgraph, context)
            case_cache = cache['account.vat.decl.case.template']

            current_cases_ids = vatcase_obj.search(cr, uid, [('decl_id','=',vatdecl_id)], context=context)
            current_cases_map = dict([(x['case_template_id'][0], x['value']) for x in vatcase_obj.read(cr, uid, current_cases_ids, context=context)])
            # remove existing cases
            vatcase_obj.unlink(cr, uid, current_cases_ids, context=context)
            # add new cases
            for casetmpl in decl_template.case_template_ids:
                case_value = case_cache[casetmpl.id]
                if not casetmpl.line_ids and casetmpl.id in current_cases_map:
                    # keep current value (case have no line template, and is already present)
                    case_value = current_cases_map[casetmpl.id]
                vatcase_obj.create(cr, uid, {
                    'decl_id': vatdecl_id,
                    'case_template_id': casetmpl.id,
                    'sequence': casetmpl.sequence,
                    'name': casetmpl.name,
                    'number': casetmpl.number,
                    'value': case_value,
                })
        return True

acctvat_decl()

class acctvat_decl_case(osv.osv):
    _name = 'account.vat.decl.case'
    #_order = "decl_id, sequence, RPAD(number,16,' ') ASC"
    _order = "decl_id, sequence ASC"
    _columns = {
        'decl_id': fields.many2one('account.vat.decl', 'Declaration', required=True, ondelete='cascade'),
        'case_template_id': fields.many2one('account.vat.decl.case.template', 'Case Template', required=True),
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Name', size=64, required=True),
        'number': fields.char('Number', size=16, required=True),
        'value': fields.float('Value', digits_compute=dp.get_precision('Account'), required=True),
    }
    _defaults = {
        'sequence': 0,
    }

    _sql_constraints = [
        ('unique_number_per_decl', 'UNIQUE(decl_id, number)', 'Case Number must be unique per Declaration'),
    ]
acctvat_decl_case()
