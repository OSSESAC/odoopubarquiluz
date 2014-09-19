# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
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

class purchase_requisition(osv.osv):
    _name = 'purchase.requisition'
    _inherit = 'purchase.requisition'
    _columns = {
            'account_analytic_id':fields.many2one('account.analytic.account', 
                                                  'Analytic Account',
                                                  domain=[('type','in',['normal','contract'])]),
            'chief_project_id': fields.related('account_analytic_id','chief_project_id',type='many2one',obj='res.users',string='Chief Project', readonly=True),
            'state': fields.selection([('draft','New'),
                                       ('approve','Approve'),
                                       ('in_progress','Valued by suppliers'),
                                       ('cancel','Cancelled'),
                                       ('done','Purchase Done')], 'Status', track_visibility='onchange', required=True),
        }
    _defaults = {
            'exclusive': 'exclusive',
        }
    _order = "name desc"
    _track = {
        'state': {
            'purchase_requisition_analytic.mt_rfq_in_progress': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'in_progress',
            'purchase_requisition_analytic.mt_rfq_approved': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approved',
        },
    }
    
    def _seller_details(self, cr, uid, requisition_line, supplier, context=None):
        product_uom = self.pool.get('product.uom')
        pricelist = self.pool.get('product.pricelist')
        supplier_info = self.pool.get("product.supplierinfo")
        product = requisition_line.product_id
        default_uom_po_id = product and product.uom_po_id.id or 1 #YT 2012/01/06 
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)
        seller_delay = 0.0
        seller_price = False
        seller_qty = False
        for product_supplier in product and product.seller_ids or []:
            if supplier.id ==  product_supplier.name and qty >= product_supplier.qty:
                seller_delay = product_supplier.delay
                seller_qty = product_supplier.qty
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        #YT 2012/01/06
        seller_price = product and pricelist.price_get(cr, uid, [supplier_pricelist.id], product.id, qty, False, {'uom': default_uom_po_id})[supplier_pricelist.id] or 0.0
        
        if seller_qty:
            qty = max(qty,seller_qty)
        date_planned = self._planned_date(requisition_line.requisition_id, seller_delay)
        return seller_price, qty, default_uom_po_id, date_planned

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                        'origin': requisition.name,
                        'partner_id': supplier.id,
                        'pricelist_id': supplier_pricelist.id,
                        'location_id': location_id,
                        'company_id': requisition.company_id.id,
                        'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                        'requisition_id':requisition.id,
                        'notes':requisition.description,
                        'warehouse_id':requisition.warehouse_id.id ,
            })
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref or line.description, #YT 2012/01/06: product.partner_ref,
                    'account_analytic_id': requisition.account_analytic_id and requisition.account_analytic_id.id, #YT 2012/01/06
                    'product_qty': qty,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'taxes_id': [(6, 0, taxes)],
                }, context=context)
                
        return res

    def onchange_user(self, cr, uid, ids, user_id):
        res = {'value':{'account_analytic_id':False}}
        if not user_id:
            return res
        user = self.pool.get('res.users').browse(cr, uid, user_id)
        for employee in user.employee_ids:
            if not employee.department_id: continue
            for analytic in employee.department_id.analytic_account_ids:
                res['value']['account_analytic_id'] = analytic.id
        return res

    def tender_approve(self, cr, uid, ids, context=None):
        for req in self.browse(cr, uid, ids, context=context):
            if not req.line_ids:
                raise osv.except_osv(_('Error'),_('The requisition must be have almost one product'))
            if not req.account_analytic_id:
                raise osv.except_osv(_('Error'),_('The requisition must be have an account analytic'))
            if not self.pool.get('account.analytic.account').is_user_chief(cr, uid, req.account_analytic_id.id, context=context):
                raise osv.except_osv(_('Error'),_('This user is not allowed to approve this requisition'))
            follower_ids = [uid]
            if req.chief_project_id:
                follower_ids.append(req.chief_project_id.id)
            self.message_subscribe_users(cr, uid, [req.id], user_ids=follower_ids, context=context)
        return self.write(cr, uid, ids, {'state':'approve'} ,context=context)

    def tender_cancel(self, cr, uid, ids, context=None):
        purchase_order_obj = self.pool.get('purchase.order')
        for purchase in self.browse(cr, uid, ids, context=context):
            for purchase_id in purchase.purchase_ids:
                if str(purchase_id.state) in('draft'):
                    purchase_order_obj.action_cancel(cr,uid,[purchase_id.id])
                elif str(purchase_id.state) not in ('cancel'):
                    raise osv.except_osv(_('Error'),_('All purchase orders must be in draft or cancel states'))
        return super(purchase_requisition,self).tender_cancel(cr, uid, ids, context=context)

    def tender_in_progress(self, cr, uid, ids, context=None):
        for req in self.browse(cr, uid, ids, context=context):
            if not req.purchase_ids:
                raise osv.except_osv(_('Error'),_('The requisition must be have almost one product'))
            for purchase in req.purchase_ids:
                if purchase.state in ('draft'):
                    raise osv.except_osv(_('Error'),_('The purchase order must be different than draft state'))
        return super(purchase_requisition,self).tender_in_progress(cr, uid, ids, context=context)

#    def tender_reset(self, cr, uid, ids, context=None):
#        return super(purchase_requisition,self).tender_reset(cr, uid, ids, context=context)

    def tender_done(self, cr, uid, ids, context=None):
        for requisition in self.browse(cr, uid, ids, context=context):
            is_approved = False
            for purchase in requisition.purchase_ids:
                if str(purchase.state) in('approved','confirmed','done'):
                    is_approved = True
            if not is_approved:
                raise osv.except_osv(_('Error'),_('Al least one purchase order must be in approved, confirmed or done states'))
            if not self.pool.get('account.analytic.account').is_user_chief(cr, uid, requisition.account_analytic_id.id, context=context):
                raise osv.except_osv(_('Error'),_('This user is not allowed to approve this requisition'))
        return super(purchase_requisition,self).tender_done(cr, uid, ids, context=context)


class purchase_requisition_line(osv.osv):
    _name = 'purchase.requisition.line'
    _inherit = 'purchase.requisition.line'
    _columns = {
        'description': fields.text('Description'),
        }

purchase_requisition_line()