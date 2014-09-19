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
import urllib
import urllib2
from lxml import etree
import re
from StringIO import StringIO

class res_partner(osv.Model):
    _inherit = "res.partner"
    _columns = {
        'sunat_state': fields.char('Sunat State', 32, select=1, help="Must be ACTIVO, BAJA DE OFICIO, SUSPENSION TEMPORAL, ..."),
        'sunat_retention_agent': fields.boolean('Sunat Retention Agent'),
        'sunat_retention': fields.char('Retention Description',1024),
	}

    def get_company_details(self, cr, uid, ruc, context=None):
        res = {}
        if not ruc or not self.pool.get('res.company').browse(cr, uid, self.pool.get('res.users')._get_company(cr, uid, context=context), context=context).sunat_search_vat:
            return res
        data = urllib.urlencode({'ruc' : ruc})
        req = urllib2.Request('http://www.sunat.gob.pe/w/wapS01Alias', data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        parser = etree.HTMLParser()
        tree   = etree.parse(StringIO(the_page), parser)
        for _sm in tree.findall("//small"):
            flag_direccion = False
            flag_telefono = False
            flag_retencion = False
            for _e in _sm.iter():
                if _e.tag == 'b' and re.findall(re.compile('N.mero Ruc.'), _e.text):
                    res['name'] = _e.tail.split(' - ')[1]
                    names = res['name'].split('-')
                    if len(names) > 1:
                        res['name'] = names[len(names) - 1]
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA CERRADA','S.A.C.')
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA ABIERTA','S.A.A.')
                    res['name'] = res['name'].replace('SOCIEDAD ANONIMA','S.A.')
                elif _e.tag == 'b' and re.findall(re.compile('Direcci.n.'), _e.text):
                    flag_direccion = True
                elif _e.tag == 'b' and re.findall(re.compile('Estado.'), _e.text):
                    res['sunat_state'] = _e.tail
                elif _e.tag == 'strong' and re.findall(re.compile('Agente Retenci.n IGV.'), _e.text):
                    flag_retencion = True
                elif _e.tag == 'strong' and flag_retencion:
                    flag_retencion = False
                    res['sunat_retention_agent'] = _e.text == 'SI' and True or False
                    if res['sunat_retention_agent']: 
                        res['sunat_retention'] = _e.tail
                elif _e.tag == 'br' and flag_direccion:
                    flag_direccion = False
                    res['street'] = _e.tail
                    res['country_id'] = self.pool.get('res.country').search(cr, uid, [('code','=','PE')], context=context)[0]
                elif _e.tag == 'b' and re.findall(re.compile('Tel.fono\(s\).'), _e.text):
                    flag_telefono = True
                elif _e.tag == 'br' and flag_telefono:
                    res['phone'] = _e.tail
        return res

