# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleCommission(models.Model):
    _name = 'sale.commission'
    _description = 'Sales Commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        tracking=True,
        help='The user receiving this commission'
    )

    role_id = fields.Many2one(
        'sale.commission.role',
        string='Role',
        required=True,
        tracking=True,
        help='The role of the user in this commission'
    )

    commission_type = fields.Selection([
        ('direct', 'Direct Sale'),
        ('override', 'Override Commission')
    ], string='Commission Type', required=True, default='direct', tracking=True,
       help='Direct = user made the sale, Override = commission on subordinate\'s sale')

    # Related Sale and Invoice
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='cascade',
        help='The sale order this commission is based on'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice')],
        help='The invoice this commission is based on'
    )

    # Commission Plan
    plan_id = fields.Many2one(
        'sale.commission.plan',
        string='Commission Plan',
        required=True
    )

    # Dates
    date = fields.Date(
        string='Commission Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    period = fields.Char(
        string='Period',
        help='Period this commission belongs to (e.g., 2025-Q1, 2025-11)'
    )

    # Amounts
    base_amount = fields.Monetary(
        string='Base Amount',
        required=True,
        currency_field='currency_id',
        help='The amount on which commission is calculated'
    )

    commission_percentage = fields.Float(
        string='Commission %',
        compute='_compute_commission_percentage',
        store=True,
        digits=(5, 2),
        help='The effective commission percentage applied'
    )

    percentage_override = fields.Float(
        string='Manual % Override',
        digits=(5, 2),
        tracking=True,
        help='Set a custom percentage for this commission (leave empty to use default)'
    )

    commission_amount = fields.Monetary(
        string='Commission Amount',
        compute='_compute_commission_amount',
        store=True,
        currency_field='currency_id',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    # Payment Status
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('claimed', 'Claimed'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Payment Status', default='unpaid', required=True, tracking=True)

    payment_date = fields.Date(
        string='Payment Date',
        tracking=True
    )

    payment_id = fields.Many2one(
        'sale.commission.payment',
        string='Payment Record',
        help='The payment batch this commission belongs to'
    )

    can_be_paid = fields.Boolean(
        string='Can Be Paid',
        compute='_compute_can_be_paid',
        store=True,
        help='True if invoice is paid and commission is unpaid'
    )

    claimable_together_count = fields.Integer(
        string='Claimable Together',
        compute='_compute_claimable_together_count',
        help='Number of other commissions that can be claimed together with this one'
    )

    # Additional Info
    notes = fields.Text(string='Notes')

    is_adjustment = fields.Boolean(
        string='Is Adjustment',
        default=False,
        help='True if this is a manual adjustment commission'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence for commission reference"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission') or _('New')
        return super(SaleCommission, self).create(vals_list)

    @api.depends('percentage_override', 'plan_id', 'role_id', 'commission_type')
    def _compute_commission_percentage(self):
        """
        Compute the effective commission percentage based on:
        - Manual override (if set)
        - Commission type (direct vs override)
        - Role configuration
        """
        for commission in self:
            if commission.percentage_override:
                commission.commission_percentage = commission.percentage_override
            else:
                # Get role configuration for this plan and role
                config = self.env['hr.commission.role.config'].search([
                    ('plan_id', '=', commission.plan_id.id),
                    ('role_id', '=', commission.role_id.id)
                ], limit=1)

                if config:
                    # Use appropriate percentage based on commission type
                    if commission.commission_type == 'direct':
                        commission.commission_percentage = config.direct_sale_percentage
                    else:  # override
                        commission.commission_percentage = config.override_percentage
                else:
                    commission.commission_percentage = 0.0

    @api.depends('base_amount', 'commission_percentage')
    def _compute_commission_amount(self):
        """Compute commission amount based on base amount and percentage"""
        for commission in self:
            commission.commission_amount = (commission.base_amount * commission.commission_percentage) / 100.0

    @api.depends('invoice_id.payment_state', 'payment_status', 'state')
    def _compute_can_be_paid(self):
        """Check if commission can be paid"""
        for commission in self:
            if commission.plan_id.require_invoice_paid:
                commission.can_be_paid = (
                    commission.invoice_id and
                    commission.invoice_id.payment_state in ['paid', 'in_payment'] and
                    commission.payment_status in ['unpaid', 'claimed', 'processing'] and
                    commission.state == 'confirmed'
                )
            else:
                commission.can_be_paid = (
                    commission.payment_status in ['unpaid', 'claimed', 'processing'] and
                    commission.state == 'confirmed'
                )

    @api.depends('user_id', 'payment_status', 'state', 'can_be_paid')
    def _compute_claimable_together_count(self):
        """Count other commissions that can be claimed together"""
        for commission in self:
            if commission.user_id and commission.payment_status == 'unpaid' and commission.state == 'confirmed':
                # Count other claimable commissions for the same user
                commission.claimable_together_count = self.search_count([
                    ('user_id', '=', commission.user_id.id),
                    ('payment_status', '=', 'unpaid'),
                    ('state', '=', 'confirmed'),
                    ('can_be_paid', '=', True),
                    ('id', '!=', commission.id)  # Exclude current commission
                ])
            else:
                commission.claimable_together_count = 0

    def action_confirm(self):
        """Confirm commission"""
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        """Cancel commission"""
        self.write({
            'state': 'cancelled',
            'payment_status': 'cancelled'
        })

    def action_claim_payment(self):
        """Claim this commission along with all other claimable commissions for the user"""
        self.ensure_one()

        # Find all claimable commissions for this user (including current one)
        all_claimable = self.env['sale.commission'].search([
            ('user_id', '=', self.user_id.id),
            ('payment_status', '=', 'unpaid'),
            ('state', '=', 'confirmed'),
            ('can_be_paid', '=', True)
        ])

        # Mark all as claimed
        all_claimable.write({'payment_status': 'claimed'})

        # Calculate total amount
        total_amount = sum(all_claimable.mapped('commission_amount'))

        # Create claim with all commissions
        claim_notes = _('Batch claim for %s commission(s)') % len(all_claimable) if len(all_claimable) > 1 else _('Claim for commission %s') % self.name

        claim = self.env['sale.commission.claim'].create({
            'user_id': self.user_id.id,
            'commission_ids': [(6, 0, all_claimable.ids)],
            'notes': claim_notes
        })

        # Show notification if multiple commissions were included
        if len(all_claimable) > 1:
            message = _('Successfully claimed %s commissions together (Total: %s %s)') % (
                len(all_claimable),
                total_amount,
                self.currency_id.symbol
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Commissions Claimed'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': 'sale.commission.claim',
                        'res_id': claim.id,
                        'view_mode': 'form',
                        'target': 'current',
                    }
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission.claim',
            'res_id': claim.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_claimable_together(self):
        """View all commissions that can be claimed together"""
        self.ensure_one()

        # Find all claimable commissions for this user (including current one)
        all_claimable = self.env['sale.commission'].search([
            ('user_id', '=', self.user_id.id),
            ('payment_status', '=', 'unpaid'),
            ('state', '=', 'confirmed'),
            ('can_be_paid', '=', True)
        ])

        return {
            'name': _('Claimable Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('id', 'in', all_claimable.ids)],
            'context': {
                'default_user_id': self.user_id.id,
            },
            'help': """<p class="o_view_nocontent_smiling_face">
                No claimable commissions found
            </p>"""
        }

    def action_create_payment(self):
        """Create a payment record for this commission"""
        self.ensure_one()
        if not self.can_be_paid:
            raise UserError(_('This commission cannot be paid yet.'))

        # Create a payment record with this commission
        payment = self.env['sale.commission.payment'].create({
            'user_id': self.user_id.id,
            'commission_ids': [(6, 0, [self.id])],
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }
