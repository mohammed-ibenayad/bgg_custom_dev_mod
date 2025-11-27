# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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

    role = fields.Selection([
        ('salesperson', 'Salesperson'),
        ('team_leader', 'Team Leader'),
        ('sales_director', 'Sales Director')
    ], string='Role', required=True, tracking=True,
       help='The role of the user in this commission')

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

    @api.model
    def create(self, vals):
        """Generate sequence for commission reference"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission') or _('New')
        return super(SaleCommission, self).create(vals)

    @api.depends('percentage_override', 'plan_id', 'role')
    def _compute_commission_percentage(self):
        """Compute the effective commission percentage"""
        for commission in self:
            if commission.percentage_override:
                commission.commission_percentage = commission.percentage_override
            else:
                # Get default percentage from role configuration
                config = self.env['hr.commission.role.config'].search([
                    ('plan_id', '=', commission.plan_id.id),
                    ('role', '=', commission.role)
                ], limit=1)
                commission.commission_percentage = config.default_percentage if config else 0.0

    @api.depends('base_amount', 'commission_percentage')
    def _compute_commission_amount(self):
        """Compute commission amount based on base amount and percentage"""
        for commission in self:
            commission.commission_amount = (commission.base_amount * commission.commission_percentage) / 100.0

    @api.depends('invoice_id.payment_state', 'payment_status')
    def _compute_can_be_paid(self):
        """Check if commission can be paid"""
        for commission in self:
            if commission.plan_id.require_invoice_paid:
                commission.can_be_paid = (
                    commission.invoice_id and
                    commission.invoice_id.payment_state in ['paid', 'in_payment'] and
                    commission.payment_status == 'unpaid' and
                    commission.state == 'confirmed'
                )
            else:
                commission.can_be_paid = (
                    commission.payment_status == 'unpaid' and
                    commission.state == 'confirmed'
                )

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
        """Allow user to claim their commission"""
        self.ensure_one()
        if self.payment_status == 'unpaid':
            self.payment_status = 'claimed'
            # Create a claim record
            claim = self.env['sale.commission.claim'].create({
                'user_id': self.user_id.id,
                'commission_ids': [(6, 0, [self.id])],
                'notes': f'Claim for commission {self.name}'
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.commission.claim',
                'res_id': claim.id,
                'view_mode': 'form',
                'target': 'current',
            }
