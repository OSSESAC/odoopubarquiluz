# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2011 NUMA Extreme Systems (www.numaes.com) for Cubic ERP - Teradata SAC. (http://cubicerp.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import netsvc
import re
import logging

logger = logging.getLogger(__name__)

months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre']

def get_url(url,values={}):
    """Return a string of a get url query"""
    try:
        import urllib
        import urllib2
        from cookielib import CookieJar
        cj = CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        response = opener.open(url)
        rawfile = response.read()
        if values:
            data = urllib.urlencode(values)
            response = opener.open(url, data)
            rawfile = response.read()
        return rawfile
    except ImportError:
        raise Exception ('Error: Unable to import urllib !')
    except IOError:
        raise Exception ('Error: Web Service [%s] does not exist or it is non accesible !' % url)

def sunat_access_exception(Exception):
    pass

def get_sunat_rates(values={}):
    url='http://www.sunat.gob.pe/cl-at-ittipcam/tcS01Alias'
    
    data = get_url(url,values=values)
    if data:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT sent a response")
    else:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. No data retrieved from www.sunat.gob.pe - values: %s'%values)
        return {}

    res_id = re.findall ('<title>SUNAT - Tipo de Cambio Oficial</title>', data)
    if not (res_id and len(res_id)>0):
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Page data could not be recognized! - values: %s'%values)
        return {}

    res_id = re.findall('''<h3>(\S+) - (\d+)</h3>''', data)

    if not(res_id and len(res_id)>0):
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Page data could not be recognized! - values: %s'%values)

    month = res_id[0][0]
    year = int(res_id[0][1])
    today = values and datetime.strptime('%(anho)s-%(mes)s-01'%values,'%Y-%m-%d') or datetime.now()
    
    if (month not in months) or month != months[today.month-1]:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Month is not recognized! - values: %s'%values)
        return {}
    if year != today.year:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Year is not recognized! - values: %s'%values)
        return {}

    res_id = re.findall('''<td width='4%' align='center' class="H3">\D+<strong>(\d+)</strong>\D+<td width='8%' align='center' class="tne10">\D+(\d+.\d+)\D+<td width='8%' align='center' class="tne10">\D+(\d+.\d+)''', data)

    if not(res_id and len(res_id)>0):
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Exchange rates not found! values: %s'%values)
        return {}

    days = {}
    for d in res_id:
        days[int(d[0])] = {
            'Sale': float(d[1]),
            'Purchase': float(d[2]),
        }
    res = {'days': days}
    day = today.day
    if day not in days:
        logger.info("[%s] %s", netsvc.LOG_DEBUG, 'Error retrieving info from SUNAT. Day number %s not found in data!' % day)
    else:
        res['current_sale_ratio'] = days[today.day]['Sale']
        res['current_purchase_ratio'] = days[today.day]['Purchase']

    return res

class res_currency(osv.osv):
    _inherit = "res.currency"

    # Method to be subclassed by plugins
    def get_update_selection(self, cr, uid, context=None):
        return [('sunat', 'SUNAT')] + super(res_currency, self).get_update_selection(cr, uid, context=context)
        
    def update_rate(self, cr, uid, ids, context=None):
        if ids:
            sunat_ids = [c.id for c in self.browse(cr, uid, ids, context=context) if c.update_method=='sunat']
            for sunat_id in sunat_ids:
                try:
                    sunat_rates = get_sunat_rates()
                    if not (sunat_rates.has_key('current_sale_ratio') and sunat_rates.has_key('current_purchase_ratio')):
                        continue 
                    
                    usd_rate = self.get_usd_rate(cr, uid, context=context)
                    
                    sale_type_id = self.get_sale_type_id(cr, uid, context=context)
                    purchase_type_id = self.get_purchase_type_id(cr, uid, context=context)
                
                    for c in self.browse(cr, uid, [sunat_id], context=context):
                        if c.name == 'PEN':
                            #Only Peruvian Sol is supported
                            self.rate_add(cr, uid, [c.id], sale_type_id, sunat_rates['current_sale_ratio'] * usd_rate, context=context)
                            self.rate_add(cr, uid, [c.id], purchase_type_id, sunat_rates['current_purchase_ratio'] * usd_rate, context=context)
                            self.rate_add(cr, uid, [c.id], False, sunat_rates['current_sale_ratio'] * usd_rate, context=context)
                            c.write({'last_update_on': fields.date.context_today(self, cr, uid, context=context),
                                     'log_buffer':'OK'}, context=context)
                            logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT sucessfull update on currency %s" % c.name)
                        else:
                            logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT does not support currency %s" % c.name)
                            c.log_add(cr, uid, [c.id], "SUNAT does not support %s" % c.name)
                                                            
                except Exception, e:
                    logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT unexpected exception: %s" % unicode(e))
                    self.log_add(cr, uid, ids, _("Exception on %s: %s") % (fields.datetime.now(), unicode(e)), context=context)
        return super(res_currency, self).update_rate(cr, uid, ids, context=context)    

    def batch_update_rate(self, cr, uid, ids, context=None):
        currency_rate_obj = self.pool.get('res.currency.rate')
        for currency in self.browse(cr, uid, ids, context=context):
            if currency.update_method != 'sunat':
                continue
            if currency.name != 'PEN':
                logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT does not support currency %s" % currency.name)
                c.log_add(cr, uid, [c.id], "SUNAT does not support %s" % currency.name)
                continue
            try:
                usd_rate = self.get_usd_rate(cr, uid, context=context)
                sale_type_id = self.get_sale_type_id(cr, uid, context=context)
                purchase_type_id = self.get_purchase_type_id(cr, uid, context=context)
                values = []
                date_fin = datetime.strptime(fields.date.context_today(self, cr, uid, context=context) ,'%Y-%m-%d')
                if currency.update_from:
                    date_ini = datetime.strptime(currency.update_from ,'%Y-%m-%d')
                    while date_ini < date_fin:
                        values.append((('anho',str(date_ini.year)), ('mes','%02d'%date_ini.month), ('accion','init')))
                        date_ini += relativedelta(months=1)
                values.append((('anho',str(date_fin.year)), ('mes','%02d'%date_fin.month), ('accion','init')))
                values = [dict(i) for i in set(values)]
                for value in values:
                    days = get_sunat_rates(values=currency.update_from and value or {}).get('days',{})
                    for k in days.keys():
                        date = '%s-%s-%02d'%(value['anho'],value['mes'],k)
                        self.rate_add(cr, uid, [currency.id], sale_type_id, days[k]['Sale'] * usd_rate, date=date, context=context)
                        self.rate_add(cr, uid, [currency.id], purchase_type_id, days[k]['Purchase'] * usd_rate, date=date, context=context)
                        self.rate_add(cr, uid, [currency.id], False, days[k]['Sale'] * usd_rate, date=date, context=context)
           
            except Exception, e:
                logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT unexpected exception: %s" % unicode(e))
                self.log_add(cr, uid, ids, _("Exception on %s: %s") % (fields.datetime.now(), unicode(e)), context=context)

            currency.write({'last_update_on': fields.date.context_today(self, cr, uid, context=context),
                                     'log_buffer':'OK'}, context=context)
            logger.info("[%s] %s", netsvc.LOG_DEBUG, "SUNAT sucessfull update on currency %s" % currency.name)
        return super(res_currency, self).batch_update_rate(cr, uid, ids, context=context)
    # End of plugins

    def get_usd_rate(self, cr, uid, context=None):
        base_currency_ids = self.search(cr, uid, [('base','=',True)], context=context)
        usd_currency_ids = self.search(cr, uid, [('name','=','USD')], context=context)
        if not base_currency_ids:
            raise Exception('Error retrieving info for SUNAT: No base currency found!')
        if not usd_currency_ids:
            raise Exception('Error retrieving info for SUNAT: No USD currency found!')
        return self.compute(cr, uid, base_currency_ids[0], usd_currency_ids[0], 1.0) or 1.0 

    def get_sale_type_id(self, cr, uid, context=None):
        rcrt_obj = self.pool.get('res.currency.rate.type')
        sale_ids = rcrt_obj.search(cr, uid, [('name','=','sunat.ask')], context=context)
        return sale_ids[0]
        
    def get_purchase_type_id(self, cr, uid, context=None):
        rcrt_obj = self.pool.get('res.currency.rate.type')
        purchase_ids = rcrt_obj.search(cr, uid, [('name','=','sunat.bid')], context=context)
        return purchase_ids[0]
        
