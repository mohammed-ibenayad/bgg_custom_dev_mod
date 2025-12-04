# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


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
        compute='_compute_commission_stats',
        store=True
    )

    commission_unpaid_total = fields.Monetary(
        string='Unpaid Commissions',
        compute='_compute_commission_stats',
        store=True,
        currency_field='company_currency_id'
    )

    commission_paid_total = fields.Monetary(
        string='Paid Commissions',
        compute='_compute_commission_stats',
        store=True,
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

    active_commission_count = fields.Integer(
        string='Active Commissions',
        compute='_compute_active_commissions',
        help='Number of unpaid or claimed commissions'
    )

    has_subordinates = fields.Boolean(
        string='Has Subordinates',
        compute='_compute_has_subordinates',
        help='True if user has team members reporting to them'
    )

    subordinate_count = fields.Integer(
        string='Number of Subordinates',
        compute='_compute_has_subordinates',
        help='Total number of subordinates (direct and indirect)'
    )

    hierarchy_warnings = fields.Text(
        string='Hierarchy Warnings',
        compute='_compute_hierarchy_warnings',
        help='Warnings about hierarchy structure issues'
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

    @api.depends('my_commission_ids', 'my_commission_ids.payment_status')
    def _compute_active_commissions(self):
        """Compute count of active (unpaid/claimed) commissions"""
        for user in self:
            active_commissions = user.my_commission_ids.filtered(
                lambda c: c.payment_status in ['unpaid', 'claimed', 'processing']
            )
            user.active_commission_count = len(active_commissions)

    @api.depends('team_member_ids', 'director_team_ids')
    def _compute_has_subordinates(self):
        """Check if user has any subordinates"""
        for user in self:
            subordinate_ids = user._get_all_subordinate_ids()
            user.has_subordinates = bool(subordinate_ids)
            user.subordinate_count = len(subordinate_ids)

    @api.depends('commission_role', 'team_leader_id', 'sales_director_id', 'team_member_ids', 'director_team_ids')
    def _compute_hierarchy_warnings(self):
        """Generate warnings about hierarchy issues"""
        for user in self:
            warnings = []

            # Check if role matches hierarchy position
            if user.commission_role == 'salesperson':
                if user.team_member_ids or user.director_team_ids:
                    warnings.append(_("Warning: Salesperson has team members assigned"))
                if not user.team_leader_id:
                    warnings.append(_("Warning: Salesperson should have a team leader"))

            elif user.commission_role == 'team_leader':
                if user.team_leader_id:
                    warnings.append(_("Warning: Team leader shouldn't have a team leader assigned"))
                if not user.sales_director_id:
                    warnings.append(_("Warning: Team leader should have a sales director"))
                if user.director_team_ids:
                    warnings.append(_("Warning: Team leader has director team members (should use team_member_ids)"))

            elif user.commission_role == 'sales_director':
                if user.team_leader_id or user.sales_director_id:
                    warnings.append(_("Warning: Sales director shouldn't report to anyone"))
                if user.team_member_ids:
                    warnings.append(_("Warning: Sales director has team members (should use director_team_ids)"))

            user.hierarchy_warnings = '\n'.join(warnings) if warnings else ''

    def write(self, vals):
        """Override write to validate role changes"""
        # Check if commission_role is being changed
        if 'commission_role' in vals:
            for user in self:
                old_role = user.commission_role
                new_role = vals['commission_role']

                # Skip if role is not actually changing
                if old_role == new_role:
                    continue

                # Build warning message
                warnings = []
                blocking_issues = []

                # Check for active commissions
                if user.active_commission_count > 0:
                    warnings.append(
                        _("• User has %s active commission(s) with role '%s'") % (
                            user.active_commission_count,
                            dict(user._fields['commission_role'].selection).get(old_role, old_role)
                        )
                    )

                # Check for subordinates
                if user.has_subordinates:
                    subordinate_count = user.subordinate_count
                    if new_role == 'salesperson':
                        # Blocking: Can't change to salesperson if has subordinates
                        blocking_issues.append(
                            _("• Cannot change to Salesperson: User has %s subordinate(s) who would be orphaned") % subordinate_count
                        )
                    else:
                        warnings.append(
                            _("• User manages %s subordinate(s) in the hierarchy") % subordinate_count
                        )

                # Check for team members pointing to this user
                if new_role == 'salesperson':
                    # Check if anyone has this user as team_leader_id
                    team_members = self.env['res.users'].search([('team_leader_id', '=', user.id)])
                    if team_members:
                        blocking_issues.append(
                            _("• Cannot change to Salesperson: %s user(s) have this user as their team leader") % len(team_members)
                        )

                    # Check if anyone has this user as sales_director_id
                    director_members = self.env['res.users'].search([('sales_director_id', '=', user.id)])
                    if director_members:
                        blocking_issues.append(
                            _("• Cannot change to Salesperson: %s user(s) have this user as their sales director") % len(director_members)
                        )

                elif new_role == 'team_leader':
                    # Check if anyone has this user as sales_director_id
                    director_members = self.env['res.users'].search([('sales_director_id', '=', user.id)])
                    if director_members:
                        blocking_issues.append(
                            _("• Cannot change to Team Leader: %s user(s) have this user as their sales director") % len(director_members)
                        )

                # If there are blocking issues, prevent the change
                if blocking_issues:
                    raise UserError(
                        _("Cannot change commission role from '%s' to '%s' for user %s:\n\n%s\n\nPlease reassign subordinates first.") % (
                            dict(user._fields['commission_role'].selection).get(old_role, old_role),
                            dict(user._fields['commission_role'].selection).get(new_role, new_role),
                            user.name,
                            '\n'.join(blocking_issues)
                        )
                    )

                # If there are warnings (but not blocking), log them
                if warnings:
                    # In Odoo, we can't show a confirmation dialog in write(),
                    # but we can log a warning message
                    message = _("Changing commission role from '%s' to '%s':\n\n%s\n\nPlease ensure commission plans are updated accordingly.") % (
                        dict(user._fields['commission_role'].selection).get(old_role, old_role),
                        dict(user._fields['commission_role'].selection).get(new_role, new_role),
                        '\n'.join(warnings)
                    )
                    # Post message to user's chatter
                    user.message_post(body=message, subject=_("Commission Role Changed"))

        return super(ResUsers, self).write(vals)
