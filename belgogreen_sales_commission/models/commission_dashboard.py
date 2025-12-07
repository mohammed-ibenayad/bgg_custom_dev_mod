# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CommissionDashboard(models.TransientModel):
    _name = 'commission.dashboard'
    _description = 'Commission Dashboard'

    @api.model
    def get_dashboard_data(self):
        """Get all dashboard data for the current user"""
        user = self.env.user

        # Get date ranges
        today = fields.Date.today()
        first_day_month = today.replace(day=1)
        last_month = first_day_month - timedelta(days=1)
        first_day_last_month = last_month.replace(day=1)
        six_months_ago = today - relativedelta(months=6)

        # Get user's commissions
        my_commissions = self.env['sale.commission'].search([
            ('salesperson_id', '=', user.id)
        ])

        # Get team commissions (if user is a manager)
        team_commissions = self.env['sale.commission'].search([
            ('salesperson_id.commission_manager_id', '=', user.id)
        ])

        # Calculate KPIs
        kpis = self._compute_kpis(my_commissions, team_commissions, first_day_month)

        # Get chart data
        chart_data = self._compute_chart_data(user, six_months_ago, today)

        # Get recent data
        recent_data = self._compute_recent_data(user)

        # Get team data
        team_data = self._compute_team_data(user)

        return {
            'kpis': kpis,
            'charts': chart_data,
            'recent': recent_data,
            'team': team_data,
            'user_info': {
                'name': user.name,
                'role': user.commission_role_id.name if user.commission_role_id else 'No Role',
                'manager': user.commission_manager_id.name if user.commission_manager_id else None,
            }
        }

    def _compute_kpis(self, my_commissions, team_commissions, first_day_month):
        """Compute KPI metrics"""
        # My Commissions
        my_total = sum(my_commissions.mapped('amount'))
        my_pending = sum(my_commissions.filtered(lambda c: c.state == 'pending').mapped('amount'))
        my_paid = sum(my_commissions.filtered(lambda c: c.state == 'paid').mapped('amount'))

        # This Month
        my_month_comms = my_commissions.filtered(lambda c: c.commission_date >= first_day_month)
        my_month_total = sum(my_month_comms.mapped('amount'))

        # Team metrics
        team_total = sum(team_commissions.mapped('amount'))
        team_pending = sum(team_commissions.filtered(lambda c: c.state == 'pending').mapped('amount'))
        team_members_count = len(set(team_commissions.mapped('salesperson_id')))

        # Pending actions (claims to approve)
        pending_claims = self.env['sale.commission.claim'].search_count([
            ('state', '=', 'submitted'),
            ('user_id.commission_manager_id', '=', self.env.user.id)
        ])

        return {
            'my_total': my_total,
            'my_pending': my_pending,
            'my_paid': my_paid,
            'my_count': len(my_commissions),
            'my_month_total': my_month_total,
            'my_month_count': len(my_month_comms),
            'team_total': team_total,
            'team_pending': team_pending,
            'team_members': team_members_count,
            'pending_claims': pending_claims,
            'hierarchy_issues': self.env.user.subordinate_count if hasattr(self.env.user, 'has_hierarchy_anomaly') and self.env.user.has_hierarchy_anomaly else 0,
        }

    def _compute_chart_data(self, user, start_date, end_date):
        """Compute data for charts"""
        # Monthly trend for last 6 months
        monthly_data = []
        current_date = start_date.replace(day=1)

        while current_date <= end_date:
            next_month = current_date + relativedelta(months=1)

            month_commissions = self.env['sale.commission'].search([
                ('salesperson_id', '=', user.id),
                ('commission_date', '>=', current_date),
                ('commission_date', '<', next_month)
            ])

            monthly_data.append({
                'month': current_date.strftime('%b %Y'),
                'amount': sum(month_commissions.mapped('amount')),
                'count': len(month_commissions)
            })

            current_date = next_month

        # Team performance
        team_performance = []
        subordinates = self.env['res.users'].search([
            ('commission_manager_id', '=', user.id)
        ])

        for subordinate in subordinates[:10]:  # Top 10
            sub_commissions = self.env['sale.commission'].search([
                ('salesperson_id', '=', subordinate.id),
                ('commission_date', '>=', fields.Date.today().replace(day=1))
            ])
            team_performance.append({
                'name': subordinate.name,
                'amount': sum(sub_commissions.mapped('amount')),
                'count': len(sub_commissions)
            })

        team_performance = sorted(team_performance, key=lambda x: x['amount'], reverse=True)

        # Commission by state
        my_commissions = self.env['sale.commission'].search([
            ('salesperson_id', '=', user.id)
        ])

        state_distribution = {
            'pending': sum(my_commissions.filtered(lambda c: c.state == 'pending').mapped('amount')),
            'approved': sum(my_commissions.filtered(lambda c: c.state == 'approved').mapped('amount')),
            'paid': sum(my_commissions.filtered(lambda c: c.state == 'paid').mapped('amount')),
            'cancelled': sum(my_commissions.filtered(lambda c: c.state == 'cancelled').mapped('amount')),
        }

        return {
            'monthly_trend': monthly_data,
            'team_performance': team_performance,
            'state_distribution': state_distribution,
        }

    def _compute_recent_data(self, user):
        """Get recent commissions and claims"""
        recent_commissions = self.env['sale.commission'].search([
            ('salesperson_id', '=', user.id)
        ], limit=10, order='commission_date desc')

        recent_claims = self.env['sale.commission.claim'].search([
            ('user_id', '=', user.id)
        ], limit=5, order='create_date desc')

        return {
            'commissions': [{
                'id': c.id,
                'date': c.commission_date.strftime('%Y-%m-%d') if c.commission_date else '',
                'amount': c.amount,
                'state': c.state,
                'order': c.order_id.name if c.order_id else '',
            } for c in recent_commissions],
            'claims': [{
                'id': c.id,
                'date': c.create_date.strftime('%Y-%m-%d'),
                'amount': c.total_amount,
                'state': c.state,
                'count': c.commission_count,
            } for c in recent_claims],
        }

    def _compute_team_data(self, user):
        """Get team hierarchy and performance data"""
        subordinates = self.env['res.users'].search([
            ('commission_manager_id', '=', user.id)
        ])

        team_members = []
        for sub in subordinates:
            team_members.append({
                'id': sub.id,
                'name': sub.name,
                'role': sub.commission_role_id.name if sub.commission_role_id else 'No Role',
                'commission_count': sub.commission_count,
                'unpaid_total': sub.commission_unpaid_total,
                'subordinates': sub.subordinate_count,
            })

        # Sort by unpaid total
        team_members = sorted(team_members, key=lambda x: x['unpaid_total'], reverse=True)

        return {
            'members': team_members,
            'total_count': len(team_members),
        }
