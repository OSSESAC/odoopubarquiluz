# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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


class workflow(osv.osv):
    _inherit = "workflow"
    _columns = {
        'instance_ids': fields.one2many('workflow.instance','wkf_id',string='Instances'),
    }

class wkf_activity(osv.osv):
    _inherit = "workflow.activity"
    _columns = {
        'workitem_ids': fields.one2many('workflow.workitem','act_id',string='Instances'),
    }
    
class wkf_instance(osv.osv):
    
    def _get_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for instance in self.browse(cr, uid, ids, context=context):
            res[instance.id] = "%s (%s)"%(instance.res_type,instance.res_id)
        return res
    
    _inherit = "workflow.instance"
    _rec_name = 'name'
    _columns = {
        'name':  fields.function(_get_name, type="char", string="Complete Name"),
	    'workitem_ids': fields.one2many('workflow.workitem','inst_id',string='Instances'),
	}
