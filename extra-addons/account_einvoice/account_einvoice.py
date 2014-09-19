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
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time

class account_ejournal(osv.Model):
    _name = "account.ejournal"
    _columns = {
            'company_id': fields.many2one('res.company', 'Company', required=True),
            'name': fields.char('Name', 64, required=True),
            'code': fields.char('Name', 8),
            'journal_ids': fields.one2many('account.journal', 'ejournal_id', 'Financial Journals', readonly=True),
            'type': fields.selection([('bill','Bill'),
                                      ('sumary','Summary Bill'),
                                      ('invalidate','Invalidate Bills')],'Type', required=True),
            'comunication_type': fields.selection([('sync','Synchronous'),
                                                   ('async','Asynchronous'),
                                                   ('batch','Synchronous Batch'),
                                                   ('none','None')],'Comunication Type', required=True),
            'sequence_type': fields.selection([('normal','Normal'),
                                               ('journal','On Financial Journal'),
                                               ('none','None')],'Sequence Type', required=True),
            'sequence_id': fields.many2one('ir.sequence','Sequence'),
            'sequence_reuse': fields.boolean('Reuse Sequence'),
        }
    _default = {
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
            'comunication_type': 'none',
            'sequence_type': 'none',
            'sequence_reuse': False,
        }

    def create_sequence(self, cr, uid, vals, context=None):
        prefix = self.pool.get('res.company').browse(cr, uid, vals['company_id'],context=context).vat
        previx = prefix and prefix[2:] or ''
        if vals.has_key('code'):
            prefix = '-' + vals.get('code').upper()

        seq = {
            'name': vals['name'],
            'implementation':'no_gap',
            'prefix': prefix + "-%(year)s%(month)s%(day)s-",
            'padding': 3,
            'number_increment': 1
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def create(self, cr, uid, vals, context=None):
        if not 'sequence_id' in vals or not vals['sequence_id']:
            vals.update({'sequence_id': self.create_sequence(cr, SUPERUSER_ID, vals, context)})
        return super(account_ejournal, self).create(cr, uid, vals, context)

class account_einvoice(osv.Model):
    _name = "account.einvoice"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'date desc, id desc'
    _columns = {
            'company_id': fields.many2one('res.company','Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'ejournal_id': fields.many2one('account.ejournal','Electronic Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'name': fields.char('Name',64,help="Usually the file name", required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'date': fields.datetime('Date', readonly=True, states={'draft':[('readonly',False)]}),
            'type': fields.selection([('request','Request'),
                                      ('response','Response'),
                                      ('echo','Temporal Response')],'Type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'xml': fields.text('XML Generated', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'file': fields.binary('File', readonly=True, states={'draft':[('readonly',False)]}),
            'invoice_ids': fields.many2many('account.invoice','account_einvoice_invoice_rel',
                                            'einvoice_id','invoice_id',string="Invoices", readonly=True, states={'draft':[('readonly',False)]}),
            'ejournal_type': fields.related('ejournal_id', 'type',type="selection",string="eJournal type", readonly=True),
            'invalidate_id': fields.many2one('account.einvoice','Invalidate Request',ondelete="set null", readonly=True,
                                                domain=[('type','=','request'),('ejournal_type','=','invalidate')], help="Invalidate request used to cancel this request"),
            'origin_ids': fields.one2many('account.einvoice','invalidate_id',string="Origin Requests", readonly=True, states={'draft':[('readonly',False)]},
                                          domain=[('type','=','request'),('ejournal_type','!=','invalidate')]),
            'parent_id': fields.many2one('account.einvoice','Parent Request',ondelete="cascade", readonly=True, states={'draft':[('readonly',False)]},
                                                domain=[('type','=','request')], help="Parent request for this response"),
            'child_ids': fields.one2many('account.einvoice','parent_id',string="Child Responses", readonly=True, states={'draft':[('readonly',False)]}),
            'state': fields.selection([('draft','Draft'),
                                      ('validated','Validated'),
                                      ('send','Send'),
                                      ('warning','Warning'),
                                      ('error','Error'),
                                      ('done','Done'),
                                      ('cancel','Cancel')],'State',readonly=True),
        }
    _defaults = {
            'name': '/',
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
            'state': 'draft',
        }
    _sql_constraints = [
            ('name_uniq', 'unique(name,company_id    )', 'Electronic Invoice Name must be unique per Company!'),
        ]
    
    def action_generate_from_file(self, cr, uid, ids, context=None):
        return True
    
    def action_generate_xml(self, cr, uid, ids, context=None):
        return True
    
    def action_generate_invalidate(self, cr, uid, ids, context=None):
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        return True
    
    def action_validated(self, cr, uid, ids, context=None):
        return True
    
    def action_send(self, cr, uid, ids, context=None):
        return True
    
    def action_warning(self, cr, uid, ids, context=None):
        return True
    
    def action_error(self, cr, uid, ids, context=None):
        return True
    
    def action_done(self, cr, uid, ids, context=None):
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        return True