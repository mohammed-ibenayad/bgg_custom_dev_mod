# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleCommissionPayment(models.Model):
    _name = 'sale.commission.payment'
    _description = 'Commission Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    commission_ids = fields.Many2many(
        'sale.commission',
        string='Commissions',
        domain="[('payment_status', 'in', ['unpaid', 'claimed', 'processing']), ('can_be_paid', '=', True), ('user_id', '=', user_id)]",
        help='Commissions included in this payment'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Beneficiary',
        required=True,
        tracking=True,
        help='The user receiving this payment'
    )

    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('other', 'Other')
    ], string='Payment Method', required=True, default='bank_transfer', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', required=True, tracking=True)

    notes = fields.Text(string='Notes')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence for payment reference"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission.payment') or _('New')
        return super(SaleCommissionPayment, self).create(vals_list)

    @api.depends('commission_ids', 'commission_ids.commission_amount')
    def _compute_total_amount(self):
        """Compute total payment amount"""
        for payment in self:
            payment.total_amount = sum(payment.commission_ids.mapped('commission_amount'))

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        """Count commissions in this payment"""
        for payment in self:
            payment.commission_count = len(payment.commission_ids)

    def action_confirm(self):
        """Confirm the payment"""
        for payment in self:
            if not payment.commission_ids:
                raise UserError(_('Please add at least one commission to this payment.'))
            payment.state = 'confirmed'
            payment.commission_ids.write({'payment_status': 'processing'})

    def action_mark_paid(self):
        """Mark payment as paid and update commissions"""
        for payment in self:
            if payment.state != 'confirmed':
                raise UserError(_('Only confirmed payments can be marked as paid.'))

            payment.state = 'paid'
            payment.commission_ids.write({
                'payment_status': 'paid',
                'payment_date': payment.payment_date,
                'payment_id': payment.id
            })

    def action_cancel(self):
        """Cancel the payment"""
        for payment in self:
            if payment.state == 'paid':
                raise UserError(_('Cannot cancel a payment that is already marked as paid.'))

            payment.state = 'cancelled'
            # Reset commissions to unpaid if they were in processing
            payment.commission_ids.filtered(
                lambda c: c.payment_status == 'processing'
            ).write({'payment_status': 'unpaid'})

    def action_view_commissions(self):
        """View commissions in this payment"""
        self.ensure_one()
        return {
            'name': _('Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.commission_ids.ids)],
            'context': {'default_payment_id': self.id}
        }
