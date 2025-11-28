# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleCommissionClaim(models.Model):
    _name = 'sale.commission.claim'
    _description = 'Commission Payment Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'claim_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    commission_ids = fields.Many2many(
        'sale.commission',
        string='Claimed Commissions',
        help='Commissions being claimed for payment'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Claimant',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        help='The user claiming the commissions'
    )

    claim_date = fields.Datetime(
        string='Claim Date',
        required=True,
        default=fields.Datetime.now,
        readonly=True
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
        default=lambda self: self.env.company.currency_id
    )

    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], string='State', default='pending', required=True, tracking=True)

    notes = fields.Text(
        string='Claimant Notes',
        help='Notes from the salesperson about this claim'
    )

    admin_notes = fields.Text(
        string='Admin Notes',
        tracking=True,
        help='Internal notes from the administrator'
    )

    processed_by = fields.Many2one(
        'res.users',
        string='Processed By',
        readonly=True,
        help='The admin who processed this claim'
    )

    processed_date = fields.Datetime(
        string='Processed Date',
        readonly=True
    )

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
        """Generate sequence and notify admins"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission.claim') or _('New')

        results = super(SaleCommissionClaim, self).create(vals_list)
        for result in results:
            result._notify_admins()
        return results

    @api.depends('commission_ids', 'commission_ids.commission_amount')
    def _compute_total_amount(self):
        """Compute total claimed amount"""
        for claim in self:
            claim.total_amount = sum(claim.commission_ids.mapped('commission_amount'))

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        """Count commissions in this claim"""
        for claim in self:
            claim.commission_count = len(claim.commission_ids)

    def action_approve(self):
        """Approve the claim"""
        for claim in self:
            claim.write({
                'state': 'approved',
                'processed_by': self.env.user.id,
                'processed_date': fields.Datetime.now()
            })
            claim.commission_ids.write({'payment_status': 'processing'})
            # Send notification to claimant
            claim._notify_claimant('approved')

    def action_reject(self):
        """Reject the claim"""
        for claim in self:
            claim.write({
                'state': 'rejected',
                'processed_by': self.env.user.id,
                'processed_date': fields.Datetime.now()
            })
            claim.commission_ids.write({'payment_status': 'unpaid'})
            # Send notification to claimant
            claim._notify_claimant('rejected')

    def _notify_admins(self):
        """Notify administrators about new claim"""
        try:
            admin_group = self.env.ref('sales_team.group_sale_manager')
            admins = self.env['res.users'].search([
                ('groups_id', 'in', admin_group.ids),
                ('company_ids', 'in', self.company_id.ids)
            ])

            for admin in admins:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=admin.id,
                    summary=_('New commission claim: %s') % self.name,
                    note=_('User %(user)s has claimed %(count)s commission(s) totaling %(amount)s %(currency)s') % {
                        'user': self.user_id.name,
                        'count': self.commission_count,
                        'amount': self.total_amount,
                        'currency': self.currency_id.name
                    }
                )
        except Exception:
            # If group doesn't exist or other error, continue without notification
            pass

    def _notify_claimant(self, decision):
        """Notify claimant about claim decision"""
        message = _('Your commission claim %s has been %s.') % (self.name, decision)
        if self.admin_notes:
            message += _('\n\nAdmin notes: %s') % self.admin_notes

        self.message_post(
            body=message,
            subject=_('Commission Claim %s') % decision.title(),
            partner_ids=[self.user_id.partner_id.id],
            message_type='notification'
        )

    def action_view_commissions(self):
        """View commissions in this claim"""
        self.ensure_one()
        return {
            'name': _('Claimed Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.commission_ids.ids)],
            'context': {'default_user_id': self.user_id.id}
        }
