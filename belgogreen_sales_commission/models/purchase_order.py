# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    commission_claim_id = fields.Many2one(
        'sale.commission.claim',
        string='Commission Claim',
        readonly=True,
        help='Commission claim that generated this purchase order'
    )

    def button_confirm(self):
        """Override to update claim state when PO is confirmed"""
        res = super(PurchaseOrder, self).button_confirm()

        # Update related commission claim
        for po in self:
            if po.commission_claim_id and po.commission_claim_id.state == 'po_sent':
                po.commission_claim_id.write({'state': 'po_confirmed'})
                po.commission_claim_id.commission_ids.write({'payment_status': 'processing'})

        return res

    def button_cancel(self):
        """Override to handle claim cancellation"""
        res = super(PurchaseOrder, self).button_cancel()

        # Update related commission claim
        for po in self:
            if po.commission_claim_id and po.commission_claim_id.state in ['approved', 'po_sent']:
                # Optionally reset claim or notify manager
                po.commission_claim_id.message_post(
                    body=_('Purchase Order %s was cancelled.') % po.name,
                    subject=_('PO Cancelled'),
                )

        return res
