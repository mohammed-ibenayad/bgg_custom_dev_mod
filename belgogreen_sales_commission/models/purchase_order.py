# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Deprecated - kept for backwards compatibility, use claim_ids instead
    commission_claim_id = fields.Many2one(
        'sale.commission.claim',
        string='Commission Claim',
        readonly=True,
        compute='_compute_commission_claim_id',
        store=True,
        help='Commission claim that generated this purchase order (deprecated, use claim_ids)'
    )

    claim_ids = fields.One2many(
        'sale.commission.claim',
        'purchase_order_id',
        string='Commission Claims',
        readonly=True,
        help='Commission claims associated with this purchase order'
    )

    @api.depends('claim_ids')
    def _compute_commission_claim_id(self):
        """Compute single claim for backwards compatibility"""
        for po in self:
            po.commission_claim_id = po.claim_ids[0] if po.claim_ids else False

    def write(self, vals):
        """Prevent editing commission PO lines"""
        for po in self:
            if po.claim_ids and po.state == 'draft':
                # Prevent editing PO lines for commission payments
                if 'order_line' in vals:
                    raise UserError(_(
                        'Cannot modify purchase order lines for commission payments.\n\n'
                        'This PO is generated from commission claims and contains:\n'
                        '- Gross commission amounts\n'
                        '- Deduction lines\n\n'
                        'If you need to make changes:\n'
                        '1. Cancel this PO\n'
                        '2. Adjust the claim deductions\n'
                        '3. Recreate the claim approval'
                    ))
        return super(PurchaseOrder, self).write(vals)

    def button_confirm(self):
        """Override to update claim state and auto-create payment when PO is confirmed by employee"""
        res = super(PurchaseOrder, self).button_confirm()

        for po in self:
            if po.claim_ids:
                # Update all claims to po_confirmed
                po.claim_ids.write({'state': 'po_confirmed'})

                # Get all commissions from all claims
                all_commissions = po.claim_ids.mapped('commission_ids')

                # Check if payment already exists
                existing_payment = self.env['sale.commission.payment'].search([
                    ('purchase_order_id', '=', po.id)
                ], limit=1)

                if existing_payment:
                    raise UserError(_(
                        'Payment %s already exists for this purchase order.\n\n'
                        'PO: %s\n'
                        'Payment: %s'
                    ) % (existing_payment.name, po.name, existing_payment.name))

                # Auto-create payment in draft state
                payment = self.env['sale.commission.payment'].create({
                    'user_id': po.claim_ids[0].user_id.id,  # Get user from claim, not PO partner
                    'purchase_order_id': po.id,
                    'commission_ids': [(6, 0, all_commissions.ids)],
                    'payment_amount': po.amount_total,  # Net amount from PO
                    'payment_date': fields.Date.context_today(self),
                    'state': 'draft',
                    'notes': _('Auto-generated from Purchase Order %s\nClaims: %s\n\n'
                               'This payment was automatically created when the employee confirmed the PO.\n'
                               'Please review and confirm to proceed with payment.') % (
                        po.name,
                        ', '.join(po.claim_ids.mapped('name'))
                    )
                })

                # Update commission status to processing
                all_commissions.write({'payment_status': 'processing'})

                # Notify manager about auto-created payment
                po.message_post(
                    body=_('Payment %s was automatically created and is ready for processing.') % payment.name,
                    subject=_('Payment Ready'),
                )

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
