# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2011 Cubic ERP - Teradata SAC. (http://cubicerp.com).
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

import string

from osv import osv, fields
from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def check_vat_cl (self,vat ):
        body, vdig = '', ''
        if len(vat) > 9:
            vat = vat.replace('-','',1).replace('.','',2)
        if len(vat) != 9:
            return False
        else:
            body, vdig = vat[:-1], vat[-1]
        try:
            operar = (range(10) + ['k'])[11-sum([int(digit)*factor for digit,factor in zip(body[::-1],2*range(2,8))])%11]
            try:
                if operar == int(vdig):
                    return True
                else:
                    return False
            except ValueError:
                if operar == vdig.lower():
                    return True
                else:
                    return False
        except IndexError:
            return False
    
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
