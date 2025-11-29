# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    commission_role = fields.Selection([
        ('salesperson', 'Salesperson'),
        ('team_leader', 'Team Leader'),
        ('sales_director', 'Sales Director')
    ], string='Commission Role', help='Role in the commission hierarchy')

    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        domain=[('commission_role', '=', 'team_leader')],
        help='The team leader for this salesperson'
    )

    sales_director_id = fields.Many2one(
        'res.users',
        string='Sales Director',
        domain=[('commission_role', '=', 'sales_director')],
        help='The sales director for this user'
    )

    team_member_ids = fields.One2many(
        'res.users',
        'team_leader_id',
        string='Team Members',
        help='Salespeople reporting to this team leader'
    )

    my_commission_ids = fields.One2many(
        'sale.commission',
        'user_id',
        string='My Commissions'
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_stats'
    )

    commission_unpaid_total = fields.Monetary(
        string='Unpaid Commissions',
        compute='_compute_commission_stats',
        currency_field='company_currency_id'
    )

    commission_paid_total = fields.Monetary(
        string='Paid Commissions',
        compute='_compute_commission_stats',
        currency_field='company_currency_id'
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        string='Company Currency',
        related='company_id.currency_id',
        readonly=True
    )

    @api.depends('my_commission_ids', 'my_commission_ids.payment_status', 'my_commission_ids.commission_amount')
    def _compute_commission_stats(self):
        """Compute commission statistics for the user"""
        for user in self:
            commissions = user.my_commission_ids
            user.commission_count = len(commissions)
            user.commission_unpaid_total = sum(
                commissions.filtered(lambda c: c.payment_status == 'unpaid').mapped('commission_amount')
            )
            user.commission_paid_total = sum(
                commissions.filtered(lambda c: c.payment_status == 'paid').mapped('commission_amount')
            )

    def action_view_my_commissions(self):
        """Open the user's commissions"""
        self.ensure_one()
        return {
            'name': _('My Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        }
