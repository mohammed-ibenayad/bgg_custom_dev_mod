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

    has_hierarchy_anomaly = fields.Boolean(
        string='Has Hierarchy Anomaly',
        compute='_compute_hierarchy_anomalies',
        search='_search_has_hierarchy_anomaly',
        help='True if user has hierarchical assignment issues that need review'
    )

    anomaly_type = fields.Selection([
        ('salesperson_no_team_leader', 'Commercial sans chef d\'équipe'),
        ('salesperson_bypass_team_leader', 'Commercial rattaché directement au directeur'),
        ('team_leader_no_director', 'Chef d\'équipe sans directeur'),
        ('director_has_manager', 'Directeur avec manager assigné'),
        ('no_role_with_assignments', 'Pas de rôle avec assignations'),
    ], string='Type d\'anomalie', compute='_compute_hierarchy_anomalies', store=True)

    anomaly_description = fields.Text(
        string='Description de l\'anomalie',
        compute='_compute_hierarchy_anomalies',
        store=True,
        help='Description détaillée de l\'anomalie hiérarchique'
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
            'name': _('Mes commissions'),
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
            list: List of unique user IDs for all active subordinates (no duplicates)
        """
        self.ensure_one()
        subordinate_ids = set()  # Use set to avoid duplicates

        # Get direct reports via team_leader_id (for Team Leaders → Salespeople)
        # Filter only active users
        direct_reports = self.team_member_ids.filtered(lambda u: u.active)

        # Get direct reports via sales_director_id (for Sales Directors → Team Leaders/Salespeople)
        # Filter only active users
        director_reports = self.director_team_ids.filtered(lambda u: u.active)

        # Combine both types of direct reports
        all_direct_reports = direct_reports | director_reports

        # Add direct reports to the set
        subordinate_ids.update(all_direct_reports.ids)

        # Recursively get subordinates of direct reports
        for member in all_direct_reports:
            subordinate_ids.update(member._get_all_subordinate_ids())

        return list(subordinate_ids)  # Convert back to list for compatibility

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
            'name': _('Commissions de l\'équipe'),
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
                    warnings.append(_("Attention : Un commercial a des membres d'équipe assignés"))
                if not user.team_leader_id:
                    warnings.append(_("Attention : Un commercial doit avoir un chef d'équipe"))

            elif user.commission_role == 'team_leader':
                if user.team_leader_id:
                    warnings.append(_("Attention : Un chef d'équipe ne doit pas avoir de chef d'équipe assigné"))
                if not user.sales_director_id:
                    warnings.append(_("Attention : Un chef d'équipe doit avoir un directeur commercial"))
                if user.director_team_ids:
                    warnings.append(_("Attention : Un chef d'équipe a des membres d'équipe de directeur (utiliser team_member_ids)"))

            elif user.commission_role == 'sales_director':
                if user.team_leader_id or user.sales_director_id:
                    warnings.append(_("Attention : Un directeur commercial ne doit rapporter à personne"))
                if user.team_member_ids:
                    warnings.append(_("Attention : Un directeur commercial a des membres d'équipe (utiliser director_team_ids)"))

            user.hierarchy_warnings = '\n'.join(warnings) if warnings else ''

    @api.depends('commission_role', 'team_leader_id', 'sales_director_id')
    def _compute_hierarchy_anomalies(self):
        """Detect hierarchy anomalies that need business verification"""
        for user in self:
            anomaly = False
            anomaly_type = False
            description = ''

            # Only check users with a commission role
            if user.commission_role:
                if user.commission_role == 'salesperson':
                    # ANOMALY 1: Salesperson without team leader at all
                    if not user.team_leader_id and not user.sales_director_id:
                        anomaly = True
                        anomaly_type = 'salesperson_no_team_leader'
                        description = _("Ce commercial n'a ni chef d'équipe ni directeur commercial assigné. "
                                      "Il doit être rattaché à la hiérarchie.")

                    # ANOMALY 2: Salesperson reporting directly to director (bypassing team leader)
                    elif not user.team_leader_id and user.sales_director_id:
                        anomaly = True
                        anomaly_type = 'salesperson_bypass_team_leader'
                        description = _("Ce commercial est rattaché directement au directeur commercial '%s' "
                                      "sans passer par un chef d'équipe. "
                                      "Vérifiez si cela correspond à l'organisation souhaitée.") % user.sales_director_id.name

                elif user.commission_role == 'team_leader':
                    # ANOMALY 3: Team leader without sales director
                    if not user.sales_director_id:
                        anomaly = True
                        anomaly_type = 'team_leader_no_director'
                        description = _("Ce chef d'équipe n'a pas de directeur commercial assigné. "
                                      "Il doit être rattaché à un directeur commercial.")

                elif user.commission_role == 'sales_director':
                    # ANOMALY 4: Sales director with manager assigned
                    if user.team_leader_id or user.sales_director_id:
                        anomaly = True
                        anomaly_type = 'director_has_manager'
                        managers = []
                        if user.team_leader_id:
                            managers.append(_("chef d'équipe: %s") % user.team_leader_id.name)
                        if user.sales_director_id:
                            managers.append(_("directeur commercial: %s") % user.sales_director_id.name)
                        description = _("Ce directeur commercial a des managers assignés (%s). "
                                      "Un directeur commercial ne doit rapporter à personne.") % ', '.join(managers)

            # ANOMALY 5: User with hierarchy assignments but no role
            elif not user.commission_role and (user.team_leader_id or user.sales_director_id):
                anomaly = True
                anomaly_type = 'no_role_with_assignments'
                assignments = []
                if user.team_leader_id:
                    assignments.append(_("chef d'équipe: %s") % user.team_leader_id.name)
                if user.sales_director_id:
                    assignments.append(_("directeur commercial: %s") % user.sales_director_id.name)
                description = _("Cet utilisateur a des assignations hiérarchiques (%s) "
                              "mais n'a pas de rôle de commission défini.") % ', '.join(assignments)

            user.has_hierarchy_anomaly = anomaly
            user.anomaly_type = anomaly_type
            user.anomaly_description = description

    def _search_has_hierarchy_anomaly(self, operator, value):
        """Search method for has_hierarchy_anomaly field"""
        # Get all users and check for anomalies
        if operator == '=' and value:
            # Find users with anomalies
            all_users = self.search([('commission_role', '!=', False)])
            users_with_anomalies = []

            for user in all_users:
                if user.commission_role == 'salesperson':
                    if not user.team_leader_id:
                        users_with_anomalies.append(user.id)
                elif user.commission_role == 'team_leader':
                    if not user.sales_director_id:
                        users_with_anomalies.append(user.id)
                elif user.commission_role == 'sales_director':
                    if user.team_leader_id or user.sales_director_id:
                        users_with_anomalies.append(user.id)

            # Also check users with assignments but no role
            users_no_role = self.search([
                ('commission_role', '=', False),
                '|',
                ('team_leader_id', '!=', False),
                ('sales_director_id', '!=', False)
            ])
            users_with_anomalies.extend(users_no_role.ids)

            return [('id', 'in', users_with_anomalies)]

        elif operator == '=' and not value:
            # Find users without anomalies
            all_users = self.search([('commission_role', '!=', False)])
            users_with_anomalies = []

            for user in all_users:
                if user.commission_role == 'salesperson':
                    if not user.team_leader_id:
                        users_with_anomalies.append(user.id)
                elif user.commission_role == 'team_leader':
                    if not user.sales_director_id:
                        users_with_anomalies.append(user.id)
                elif user.commission_role == 'sales_director':
                    if user.team_leader_id or user.sales_director_id:
                        users_with_anomalies.append(user.id)

            users_no_role = self.search([
                ('commission_role', '=', False),
                '|',
                ('team_leader_id', '!=', False),
                ('sales_director_id', '!=', False)
            ])
            users_with_anomalies.extend(users_no_role.ids)

            return [('id', 'not in', users_with_anomalies)]

        return []

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
                        _("• L'utilisateur a %s commission(s) active(s) avec le rôle '%s'") % (
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
                            _("• Impossible de changer en Commercial : L'utilisateur a %s subordonné(s) qui seront orphelins") % subordinate_count
                        )
                    else:
                        warnings.append(
                            _("• L'utilisateur gère %s subordonné(s) dans la hiérarchie") % subordinate_count
                        )

                # Check for team members pointing to this user
                if new_role == 'salesperson':
                    # Check if anyone has this user as team_leader_id
                    team_members = self.env['res.users'].search([('team_leader_id', '=', user.id)])
                    if team_members:
                        blocking_issues.append(
                            _("• Impossible de changer en Commercial : %s utilisateur(s) ont cet utilisateur comme chef d'équipe") % len(team_members)
                        )

                    # Check if anyone has this user as sales_director_id
                    director_members = self.env['res.users'].search([('sales_director_id', '=', user.id)])
                    if director_members:
                        blocking_issues.append(
                            _("• Impossible de changer en Commercial : %s utilisateur(s) ont cet utilisateur comme directeur commercial") % len(director_members)
                        )

                elif new_role == 'team_leader':
                    # Check if anyone has this user as sales_director_id
                    director_members = self.env['res.users'].search([('sales_director_id', '=', user.id)])
                    if director_members:
                        blocking_issues.append(
                            _("• Impossible de changer en Chef d'équipe : %s utilisateur(s) ont cet utilisateur comme directeur commercial") % len(director_members)
                        )

                # If there are blocking issues, prevent the change
                if blocking_issues:
                    raise UserError(
                        _("Impossible de changer le rôle de commission de '%s' à '%s' pour l'utilisateur %s:\n\n%s\n\nVeuillez réassigner les subordonnés d'abord.") % (
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
                    message = _("Changement du rôle de commission de '%s' à '%s':\n\n%s\n\nVeuillez vous assurer que les plans de commission sont mis à jour en conséquence.") % (
                        dict(user._fields['commission_role'].selection).get(old_role, old_role),
                        dict(user._fields['commission_role'].selection).get(new_role, new_role),
                        '\n'.join(warnings)
                    )
                    # Post message to user's chatter
                    user.message_post(body=message, subject=_("Rôle de commission modifié"))

        return super(ResUsers, self).write(vals)
