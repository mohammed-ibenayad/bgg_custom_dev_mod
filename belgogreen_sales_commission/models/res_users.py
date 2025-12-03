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

    director_team_ids = fields.One2many(
        'res.users',
        'sales_director_id',
        string='Director Team',
        help='Team leaders and salespeople reporting to this sales director'
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

    team_commission_count = fields.Integer(
        string='Team Commission Count',
        compute='_compute_team_commission_stats',
        help='Total commissions for all subordinates'
    )

    team_unpaid_total = fields.Monetary(
        string='Team Unpaid Commissions',
        compute='_compute_team_commission_stats',
        currency_field='company_currency_id',
        help='Total unpaid commissions for all subordinates'
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

    def _get_all_subordinate_ids(self):
        """
        Get all subordinate user IDs recursively.

        This method traverses the hierarchy tree downwards to find all users
        who report to this user, directly or indirectly.

        For Team Leaders: Returns salespeople (via team_member_ids)
        For Sales Directors: Returns team leaders + their salespeople (via director_team_ids)

        Returns:
            list: List of user IDs for all subordinates
        """
        self.ensure_one()
        subordinate_ids = []

        # Get direct reports via team_leader_id (for Team Leaders → Salespeople)
        direct_reports = self.team_member_ids

        # Get direct reports via sales_director_id (for Sales Directors → Team Leaders/Salespeople)
        director_reports = self.director_team_ids

        # Combine both types of direct reports
        all_direct_reports = direct_reports | director_reports

        # Add direct reports to the list
        subordinate_ids.extend(all_direct_reports.ids)

        # Recursively get subordinates of direct reports
        for member in all_direct_reports:
            subordinate_ids.extend(member._get_all_subordinate_ids())

        return subordinate_ids

    def _compute_team_commission_stats(self):
        """Compute commission statistics for all subordinates"""
        for user in self:
            subordinate_ids = user._get_all_subordinate_ids()

            if not subordinate_ids:
                user.team_commission_count = 0
                user.team_unpaid_total = 0.0
            else:
                # Get all commissions for subordinates
                team_commissions = self.env['sale.commission'].search([
                    ('user_id', 'in', subordinate_ids)
                ])

                user.team_commission_count = len(team_commissions)
                user.team_unpaid_total = sum(
                    team_commissions.filtered(lambda c: c.payment_status == 'unpaid').mapped('commission_amount')
                )

    def action_view_team_commissions(self):
        """Open commissions for all subordinates"""
        self.ensure_one()
        subordinate_ids = self._get_all_subordinate_ids()

        return {
            'name': _('Team Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('user_id', 'in', subordinate_ids)],
            'context': {
                'search_default_group_by_user': 1,
            }
        }
