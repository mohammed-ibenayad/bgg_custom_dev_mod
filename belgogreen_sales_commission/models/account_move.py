# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_ids = fields.One2many(
        'sale.commission',
        'invoice_id',
        string='Commissions',
        help='Commissions generated from this invoice'
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count'
    )

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        """Count commissions for this invoice"""
        for move in self:
            move.commission_count = len(move.commission_ids)

    def _create_hierarchical_commissions(self):
        """
        Create commissions for salesperson, team leader, and sales director
        when invoice is paid
        """
        self.ensure_one()

        # Only process customer invoices
        if self.move_type != 'out_invoice':
            return

        # Only process if invoice is paid (or in payment)
        if self.payment_state not in ['paid', 'in_payment']:
            return

        # Get the sale order(s) linked to this invoice
        sale_orders = self.invoice_line_ids.mapped('sale_line_ids.order_id')

        if not sale_orders:
            return

        # Process each sale order
        for sale_order in sale_orders:
            self._create_commission_for_sale(sale_order)

    def _create_commission_for_sale(self, sale_order):
        """Create commissions for a specific sale order"""
        # Get the salesperson
        salesperson = sale_order.user_id
        if not salesperson:
            return

        # Find applicable commission plan
        # For now, we'll use the first active hierarchical plan
        # In production, this should be more sophisticated (e.g., based on product, team, etc.)
        commission_plan = self.env['sale.commission.plan'].search([
            ('is_hierarchical', '=', True),
            ('state', '=', 'approved'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not commission_plan:
            return

        # Check if plan requires paid invoice
        if commission_plan.require_invoice_paid and self.payment_state not in ['paid', 'in_payment']:
            return

        # Calculate base amount for commissions
        # This could be total, margin, etc. - for now using invoice total
        base_amount = self.amount_total

        # Check if commissions already exist for this invoice and sale order
        existing = self.env['sale.commission'].search([
            ('invoice_id', '=', self.id),
            ('sale_order_id', '=', sale_order.id)
        ])

        if existing:
            # Commissions already created
            return

        # Create commission hierarchy
        users_to_commission = []

        # 1. Salesperson
        if salesperson.commission_role:
            users_to_commission.append((salesperson, salesperson.commission_role))

        # 2. Team Leader
        if salesperson.team_leader_id:
            users_to_commission.append((salesperson.team_leader_id, 'team_leader'))

        # 3. Sales Director
        if salesperson.sales_director_id:
            users_to_commission.append((salesperson.sales_director_id, 'sales_director'))
        elif salesperson.team_leader_id and salesperson.team_leader_id.sales_director_id:
            users_to_commission.append((salesperson.team_leader_id.sales_director_id, 'sales_director'))

        # Calculate period (YYYY-MM format)
        period = self.invoice_date.strftime('%Y-%m') if self.invoice_date else fields.Date.today().strftime('%Y-%m')

        # Create commission records for each user in the hierarchy
        for user, role in users_to_commission:
            # Check if user is in the plan's allowed users list
            if commission_plan.user_ids and user.id not in commission_plan.user_ids.ids:
                # User not in plan's user list, skip
                continue

            # Check if there's a role configuration
            role_config = self.env['hr.commission.role.config'].search([
                ('plan_id', '=', commission_plan.id),
                ('role', '=', role)
            ], limit=1)

            if not role_config:
                continue

            # Create commission record
            self.env['sale.commission'].create({
                'user_id': user.id,
                'role': role,
                'sale_order_id': sale_order.id,
                'invoice_id': self.id,
                'plan_id': commission_plan.id,
                'date': self.invoice_date or fields.Date.today(),
                'period': period,
                'base_amount': base_amount,
                'payment_status': 'unpaid',
                'state': 'confirmed',
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
            })

    def write(self, vals):
        """Override write to trigger commission creation on payment"""
        result = super(AccountMove, self).write(vals)

        # If payment_state changed to paid, create commissions
        if 'payment_state' in vals:
            for move in self:
                if move.payment_state in ['paid', 'in_payment']:
                    move._create_hierarchical_commissions()

        return result

    def action_view_commissions(self):
        """View commissions for this invoice"""
        self.ensure_one()
        return {
            'name': _('Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('invoice_id', '=', self.id)],
            'context': {'default_invoice_id': self.id}
        }
