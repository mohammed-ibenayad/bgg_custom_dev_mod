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

    def _get_commission_hierarchy(self, base_user):
        """
        Traverse hierarchy upwards from base user to collect all managers who should receive commission.

        Supports unlimited hierarchy levels by following commission_manager_id chain.
        Includes cycle detection to prevent infinite loops.

        Args:
            base_user: res.users record (typically the salesperson who made the sale)

        Returns:
            list of tuples: [(user, role, commission_type), ...] ordered from bottom to top of hierarchy
        """
        hierarchy = []
        current_user = base_user
        seen_ids = set()  # Cycle detection

        while current_user and current_user.id not in seen_ids:
            # Only include users with a commission role
            if current_user.commission_role_id:
                # Determine commission type
                is_direct_sale = (current_user.id == base_user.id)  # First person in chain = made the sale
                commission_type = 'direct' if is_direct_sale else 'override'

                hierarchy.append((current_user, current_user.commission_role_id, commission_type))
                seen_ids.add(current_user.id)

            # Move up to manager
            current_user = current_user.commission_manager_id

            # Safety check: prevent infinite loops
            if len(seen_ids) > 20:
                break

        return hierarchy

    def _create_commission_for_sale(self, sale_order):
        """
        Create commissions for a specific sale order.
        Now supports dynamic N-level hierarchies with dual percentage (direct vs override).
        """
        # Get the salesperson
        salesperson = sale_order.user_id
        if not salesperson:
            return

        # Find applicable commission plan
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
        base_amount = self.amount_total

        # Build commission hierarchy dynamically - SUPPORTS ANY NUMBER OF LEVELS
        users_to_commission = self._get_commission_hierarchy(salesperson)

        if not users_to_commission:
            return

        # Calculate period (YYYY-MM format)
        period = self.invoice_date.strftime('%Y-%m') if self.invoice_date else fields.Date.today().strftime('%Y-%m')

        # Create commission records for each user in the hierarchy
        for user, role, commission_type in users_to_commission:
            # Check if user is in the plan's allowed users list
            if commission_plan.user_ids and user.id not in commission_plan.user_ids.mapped('user_id').ids:
                continue

            # Check if commission already exists for this specific user
            existing_commission = self.env['sale.commission'].search([
                ('invoice_id', '=', self.id),
                ('sale_order_id', '=', sale_order.id),
                ('user_id', '=', user.id),
                ('role_id', '=', role.id),
                ('commission_type', '=', commission_type)
            ], limit=1)

            if existing_commission:
                continue

            # Check if there's a role configuration
            role_config = self.env['hr.commission.role.config'].search([
                ('plan_id', '=', commission_plan.id),
                ('role_id', '=', role.id),
                ('active', '=', True)
            ], limit=1)

            if not role_config:
                continue

            # Create commission record with role_id and commission_type
            self.env['sale.commission'].create({
                'user_id': user.id,
                'role_id': role.id,
                'commission_type': commission_type,  # NEW: direct or override
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
        """Override write to trigger commission creation on payment and auto-confirm commission payments"""
        result = super(AccountMove, self).write(vals)

        # If payment_state changed to paid
        if 'payment_state' in vals:
            for move in self:
                if move.payment_state in ['paid', 'in_payment']:
                    # Create commissions for customer invoices
                    if move.move_type == 'out_invoice':
                        move._create_hierarchical_commissions()

                    # Auto-confirm commission payments for vendor bills
                    elif move.move_type == 'in_invoice':
                        move._auto_confirm_commission_payment()

        return result

    def _auto_confirm_commission_payment(self):
        """Auto-confirm and mark commission payment as paid when vendor bill is paid"""
        self.ensure_one()

        # Check if this bill is from a commission PO
        if not self.invoice_origin:
            return

        # Find the PO
        po = self.env['purchase.order'].search([
            ('name', '=', self.invoice_origin)
        ], limit=1)

        if not po or not po.claim_ids:
            return

        # Find the related payment
        payment = self.env['sale.commission.payment'].search([
            ('purchase_order_id', '=', po.id)
        ], limit=1)

        if not payment:
            return

        # Auto-confirm and mark as paid
        try:
            if payment.state == 'draft':
                payment.action_confirm()

            if payment.state == 'confirmed':
                payment.action_mark_paid()

                # Log in the invoice that payment was auto-completed
                self.message_post(
                    body=_('Commission payment %s was automatically confirmed and marked as paid.') % payment.name,
                    subject=_('Commission Payment Completed'),
                )
        except Exception as e:
            # Log error but don't fail the invoice payment
            self.message_post(
                body=_('Failed to auto-complete commission payment %s: %s') % (payment.name, str(e)),
                subject=_('Commission Payment Error'),
            )

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
