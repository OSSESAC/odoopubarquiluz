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

class hr_employee(osv.Model):
    _inherit = 'hr.employee'
    
    def get_prior_month_code(self, cr, uid, _id, current_date=time.strftime('%Y-%m-%d'), code='GROSS', context=None):
        res = 0.0
        payslip_line_obj = self.pool.get('hr.payslip.line')
        payslip_lines = payslip_line_obj.browse(cr, uid, payslip_line_obj.search(cr, uid, [('slip_id.employee_id','=',_id),
                                                                            ('slip_id.date_from','>=','%s-01-01'%current_date[0:4]),
                                                                            ('slip_id.date_to','<',current_date),
                                                                            ('slip_id.state','=','done'),
                                                                            ('code','=',code)], context=context), context=context)
        for line in payslip_lines:
            res += line.total
        return res

class hr_salary_rule(osv.Model):
    _name = 'hr.salary.rule'
    _inherit = 'hr.salary.rule'

    _defaults = {
        'amount_python_compute': '''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.
# employee_obj: reference to hr.employee object
# element_obj: reference to base.element object
# table_obj: reference to base.table object

# Note: returned value have to be set in the variable 'result'

result = contract.wage * 0.10''',
        'condition_python':
'''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs
# employee_obj: reference to hr.employee object
# element_obj: reference to base.element object
# table_obj: reference to base.table object

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10''',
     }
    
    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        localdict['element_obj'] = self.pool.get('base.element')
        localdict['table_obj'] = self.pool.get('base.table')
        localdict['employee_obj'] = self.pool.get('hr.employee')
        localdict['cr'] = cr
        localdict['uid'] = uid
        return super(hr_salary_rule,self).compute_rule(cr, uid, rule_id, localdict, context=context)
    
    def satisfy_condition(self, cr, uid, rule_id, localdict, context=None):
        localdict['element_obj'] = self.pool.get('base.element')
        localdict['table_obj'] = self.pool.get('base.table')
        localdict['employee_obj'] = self.pool.get('hr.employee')
        localdict['cr'] = cr
        localdict['uid'] = uid
        return super(hr_salary_rule,self).satisfy_condition(cr, uid, rule_id, localdict, context=context)