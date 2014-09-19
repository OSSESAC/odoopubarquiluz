# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2014 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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
import time
import openerplib
import sys
from openerpetl import oer_etl

class etl_server(osv.Model):
    _name = 'etl.server'
    _description = 'ETL Server'
    _columns = {
            'name': fields.char('Name', size=128, required=True, translate=True),
            'type': fields.selection([('odbc','ODBC'), 
                                      ('xmlrpc','XML-RPC'),
                                      ('postgresql','PostgreSQL')], 'Server Type', required=True),
            'str_connection': fields.char('String Connection', size=2048),
            'host': fields.char('Host',64),
            'port': fields.integer('Port'),
            'database': fields.char('Data Base',32),
            'database_encoding': fields.char('Data Base Encoding',16),
            'login': fields.char('Login',32),
            'password': fields.char('Password',32),
            'job_ids': fields.one2many('etl.job','src_server_id','Jobs'),
            'local_server': fields.boolean('Local Server'),
            'active': fields.boolean('Active'),     
        }
    _defaults = {
            'active' : True,
            'host': 'localhost',
            'port': 8069,
            'local_server': False,
            'type': 'xmlrpc',
        }

class etl_log(osv.Model):
    _name = 'etl.log'
    _description = 'ETL Log'
    _columns = {
            'name': fields.datetime('Time', readonly=True),
            'job_id': fields.many2one('etl.job',string='Job', readonly=True),
            'model': fields.char('Model', 64, readonly=True),
            'model_id': fields.integer('ID', help="Usually internal local database id", readonly=True),
            'pk': fields.char('PK', 512, help="Usually primary key conadenated on source database", readonly=True),
            'level': fields.selection([('info','Information'), ('warning','Warning'), ('error','Error')], 'Level', required=True, readonly=True),
            'log': fields.text('Log', required=True, readonly=True),
            'traceback': fields.text('Traceback', readonly=True),
            'check': fields.boolean('Check'),
        }
    _defaults = {
            'name' : lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'info',
            'check': False,
        }
    _order = "name desc"

class etl_job(osv.Model):
    _name = 'etl.job'
    _description = 'ETL Job'
    _columns = {
            'name': fields.char('Name', size=256, required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'type': fields.selection([('batch','Batch'),
                                      ('per-call','Per Call')], string="Type", required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'local_server_id': fields.many2one('etl.server',string='Local Server', domain=[('local_server','=',True)], required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'src_server_id': fields.many2one('etl.server',string='Source Server', domain=[('local_server','=',False)], required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'dst_server_id': fields.many2one('etl.server',string='Destinity Server', domain=[('local_server','=',False)], required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'date': fields.date('Date', readonly=True, states={'draft':[('readonly',False)]}),
            'query_begin': fields.text('Query Begin', help="This commands will not return rows", readonly=True, states={'draft':[('readonly',False)]}),
            'query_begin_delay': fields.integer('Query Begin Delay', help="Time in seconds to waiting the execution of the query begin", readonly=True, states={'draft':[('readonly',False)]}),
            'query': fields.text('Query', help="This query must return rows", readonly=True, states={'draft':[('readonly',False)]}),
            'query_end': fields.text('Query End', help="This commands will not return rows", readonly=True, states={'draft':[('readonly',False)]}),
            'row_default_value': fields.text('Row Default Values', readonly=True, states={'draft':[('readonly',False)]}),
            'query_encoding': fields.related('src_server_id', 'database_encoding', string='Data Base Encoding', type='char', readonly=True, states={'draft':[('readonly',False)]}),
            'query_result_size': fields.selection([(5,'5 rows'),
                                                   (15,'15 rows'),
                                                   (50,'50 rows'),
                                                   (150,'150 rows')], string="Result Size"),
            'query_result': fields.text('Query Result', readonly=True),
            'mapping_ids': fields.one2many('etl.mapping.job','job_id',string='Mappings Job', readonly=True, states={'draft':[('readonly',False)]}),
            'log_ids': fields.one2many('etl.log','job_id',string='Log Job'),
            'load_model_id': fields.many2one('ir.model',string='Model to Load', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'load_model': fields.related('load_model_id', 'model', type="char", string="Load Model"),
            'date_start': fields.datetime('Run Start', readonly=True),
            'date_end': fields.datetime('Run End', readonly=True),
            'state': fields.selection([('draft','Draft'),
                                       ('ready','Ready'),
                                       ('run','Runing'),
                                       ('done','Done')], 'State', readonly=True),
            'reprocess': fields.boolean('Reprocess', readonly=True, states={'draft':[('readonly',False)]}),
        }
    _defaults = {
            'state' : 'draft',
            'date': lambda *a: time.strftime('%Y-%m-%d'),
            'type': 'batch',
            'row_default_value': '{}',
            'reprocess': False,
            'query_result_size': 15,
        }

    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft', 'date_start': False, 'date_end': False}, context=context)
    
    def action_ready(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'ready'}, context=context)
    
    def action_run(self, cr, uid, ids, context=None):
        for job in self.browse(cr, uid, ids, context=context):
            if job.type == 'batch' and job.state == 'ready':
                self.set_task(cr, uid, [job.id], context=context)
                self.action_start(cr, uid, [job.id], context=context)
        return True
    
    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done', 'reprocess':False, 'date_end': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
    
    def action_start(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'run', 'date_start': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
    
    def action_reprocess(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'reprocess': True}, context=context)
        return self.action_draft(cr, uid, ids, context=context)
    
    def button_load_model_data(self, cr, uid, ids, context=None):
        if not ids:
            return {}
        job = self.browse(cr, uid, ids[0], context=context)
        return {
          'view_type':'form',
          'view_mode':'tree,form',
          'res_model': job.load_model,
          'view_id':False,
          'name': 'Loaded Data',
          'domain': [('id','in',[l.model_id for l in job.log_ids if l.model_id and l.level=='info'])],
          'type':'ir.actions.act_window',
          'context':context,
        }
    
    def do_query(self, cr, uid, ids, context=None):
        for job in self.browse(cr, uid, ids):
            oer_local = openerplib.get_connection(hostname="localhost",
                                         port=job.local_server_id.port, database=cr.dbname,
                                         login=job.local_server_id.login, password=job.local_server_id.password)
            etl = oer_etl(oer_local)
            result = "" 
            rows = etl.get_rows(job.id)
            for i, row in enumerate(rows):
                if i == 0:
                    for r in row:
                        result += r + " | "
                    result = result and  result[:-3] + '\n' or '\n'
                for r in row: 
                    if type(row[r]) is unicode or type(row[r]) is str:
                        result += row[r]  + " | "
                    else:
                        result += str(row[r])  + " | "
                result = result and  result[:-3] + '\n' or '\n'
                if job.query_result_size and i > job.query_result_size:
                    result += '...\n'
                    break
            result += "(%s rows retrieved)"%len(rows)
            if job.query_encoding and type(result) is not unicode:
                result = result.decode(job.query_encoding)
            self.write(cr, uid, [job.id], {'query_result': result}, context=context)
        return True
    
    def load(self, cr, uid, ids):
        for job in self.browse(cr, uid, ids):
            oer_local = openerplib.get_connection(hostname="localhost",
                                         port=job.local_server_id.port, database=cr.dbname,
                                         login=job.local_server_id.login, password=job.local_server_id.password)
            etl = oer_etl(oer_local) 
            for row in etl.get_rows(job.id):
                new_id = etl.create(job.id, etl.get_values(job.id,row), pk=row.get('pk',False))
        self.action_done(cr, uid, ids)
        return True
    
    def delete(self, cr, uid, ids, context=None):
        to_del = {'etl.log':[]}
        for job in self.browse(cr, uid, ids):
            for log in job.log_ids:
                if log.level != 'error' and log.model and log.model_id:
                    if not to_del.has_key(log.model):
                        to_del[log.model] = [] 
                    to_del[log.model].append(log.model_id)
                to_del['etl.log'].append(log.id)
        for k, v in to_del.items():
            self.pool.get(k).unlink(cr, uid, v, context=context)
        return self.action_draft(cr, uid, ids, context=context)
    
    def set_task(self, cr, uid, ids, context=None):
        return self.pool.get('ir.cron').create(cr, uid, {'name': 'ETL load task jobs:%s'%ids,
                                                         'user_id': uid,
                                                         'interval_type': 'minutes',
                                                         'doall': False,
                                                         'numbercall': 1,
                                                         'model': 'etl.job',
                                                         'function': 'load',
                                                         'args': '[%s]'%ids}, context=context)

class etl_mapping_job(osv.Model):
    _name = 'etl.mapping.job'
    _description = 'ETL Mapping Job'
    _columns = {
            'job_id': fields.many2one('etl.job', string="Job", required=True),
            'model_id': fields.related('job_id','load_model_id', type='many2one', relation="ir.model", string="Model", readonly=True),
            'field_id': fields.many2one('ir.model.fields', string="Field"),
            'field_name': fields.char('Field Name', 128, required=True),
            'field_type': fields.char('Field Type', 32, required=True),
            'field_relation': fields.char('Field Relation', 256),
            'search_null': fields.boolean('Search Null',help="Allow to search on name search null values"),
            'name_search': fields.text('Name Search', help="Use this field to customize the name search for this mapping. Example on account.account use next: [('code',=,account_number)]"),
            'value': fields.text('Value'),
            'mapping_id': fields.many2one('etl.mapping', string="Value Mapping"),
            'per_call_job_id': fields.many2one('etl.job', string="Job to Call", 
                                      help="Use this job to create new values on destinity server",
                                      domain=[('type','=','per-call'),('state','=','ready')]),
            'sequence': fields.integer('Sequence'),
        }
    _defaults = {
            'sequence': 5,
            'search_null': True,
        }
    _order = "sequence"
    _sql_constraints = [('job_value_uniq','unique(job_id,field_name)','The Job and Field must be unique!'),
                        ('field_relation_check',"check(field_type <> 'many2one' or not (field_relation is null or field_relation = ''))",'If the field type is many2one, then the field relation must be set!'),]
    
    def onchange_field(self, cr, uid, ids, field_id, context=None):
        res = {'value': {}}
        if not field_id:
            return res
        field = self.pool.get('ir.model.fields').browse(cr, uid, field_id, context=context)
        res['value']['field_name'] = field.name
        res['value']['field_type'] = field.ttype
        res['value']['field_relation'] = field.relation
        return res

class etl_mapping(osv.Model):
    _name = 'etl.mapping'
    _description = 'ETL Mapping'
    _columns = {
            'name': fields.char('Name', size=64, required=True),
            'date': fields.date('Date'),
            'active': fields.boolean('Active'),
            'line_ids': fields.one2many('etl.mapping.line', 'mapping_id', string="Mapping Lines"),
            'return_null': fields.boolean('Return Null'),
        }
    _defaults = {
            'date' : lambda *a: time.strftime('%Y-%m-%d'),
            'active': True,
            'return_null': True,
        }
    _sql_constraints = [('name_uniq','unique(name)','The name must be unique!'),]

    def get_object_reference(self, cr, uid, module, xml_id):
        try:
            res = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
        except Exception as e:
            res = False, False
        return res
    
class etl_mapping_line(osv.Model):
    
    def _get_map_ref(self, cr, uid, context=None):
        return [('res.partner','Partner')]
    
    _name = 'etl.mapping.line'
    _description = 'ETL Mapping Line'
    _columns = {
            'mapping_id': fields.many2one('etl.mapping',string='Mapping', required=True),
            'name': fields.char('Original Char',256, required=True),
            'map_char': fields.char('Map Char',256),
            'map_id': fields.integer('Map Id'),
            'map_xml_id': fields.char('Map XML Id',128),
            'map_ref': fields.reference('Map Reference', _get_map_ref, 64, help="Use this field only in case the destinity server is equal to your local OpenERP server"),
            'is_default': fields.boolean('Default', help="This row is selected when the value is not equal to another lines")
        }
    _defaults = {
            'is_default': False,
        }
    _sql_constraints = [('mapping_name_uniq','unique(mapping_id,name)','The mapping and source char must be unique!'),]
