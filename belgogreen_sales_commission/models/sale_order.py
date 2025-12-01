# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_ids = fields.One2many(
        'sale.commission',
        'sale_order_id',
        string='Commissions',
        help='Commissions generated from this sale order'
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count'
    )

    commissions_generated = fields.Boolean(
        string='Commissions Generated',
        default=False,
        help='Indicates if commissions have been generated for this order'
    )

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        """Count commissions for this sale order"""
        for order in self:
            order.commission_count = len(order.commission_ids)

    def action_generate_commissions(self):
        """
        Manual action to generate commissions for this sale order
        Can be called from a button or scheduled action
        """
        self.ensure_one()
        result = self._generate_commissions()

        # Show notification to user
        if result['success']:
            message_type = 'success'
            title = _('Commissions Generated')
        else:
            message_type = 'warning'
            title = _('Commission Generation')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': result['message'],
                'type': message_type,
                'sticky': False,
            }
        }

    def _generate_commissions(self):
        """
        Generate commissions for this sale order if conditions are met
        Returns: dict with result information
        """
        self.ensure_one()

        result = {
            'success': False,
            'message': '',
            'commissions_created': 0
        }

        # Check if order is confirmed
        if self.state not in ['sale', 'done']:
            result['message'] = _("Order %s is not confirmed (state: %s)") % (self.name, self.state)
            return result

        # Check if salesperson is assigned
        if not self.user_id:
            result['message'] = _("No salesperson assigned to order %s") % self.name
            return result

        # Check if salesperson has commission role
        if not self.user_id.commission_role:
            result['message'] = _("Salesperson %s has no commission role set") % self.user_id.name
            return result

        # Get paid invoices for this sale order
        paid_invoices = self.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice'
            and inv.state == 'posted'
            and inv.payment_state in ['paid', 'in_payment']
        )

        if not paid_invoices:
            result['message'] = _("No paid invoices found for order %s") % self.name
            return result

        # Find applicable commission plan
        commission_plan = self.env['sale.commission.plan'].search([
            ('is_hierarchical', '=', True),
            ('state', '=', 'approved'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not commission_plan:
            result['message'] = _("No approved hierarchical commission plan found")
            return result

        # Check if plan requires paid invoice
        if commission_plan.require_invoice_paid and not paid_invoices:
            result['message'] = _("Commission plan requires paid invoices, but none found for order %s") % self.name
            return result

        # Process each paid invoice
        commissions_created = 0
        for invoice in paid_invoices:
            created = self._create_commissions_for_invoice(invoice, commission_plan)
            commissions_created += created

        if commissions_created > 0:
            self.commissions_generated = True
            result['success'] = True
            result['message'] = _("Successfully created %s commission(s) for order %s") % (commissions_created, self.name)
            result['commissions_created'] = commissions_created
        else:
            result['message'] = _("No new commissions created for order %s (may already exist)") % self.name

        return result

    def _create_commissions_for_invoice(self, invoice, commission_plan):
        """
        Create commission records for a specific invoice
        Returns: number of commissions created
        """
        self.ensure_one()

        salesperson = self.user_id
        base_amount = invoice.amount_total

        # Build commission hierarchy
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
        period = invoice.invoice_date.strftime('%Y-%m') if invoice.invoice_date else fields.Date.today().strftime('%Y-%m')

        # Create commission records
        commissions_created = 0
        for user, role in users_to_commission:
            # Check if user is in the plan's allowed users list
            if commission_plan.user_ids and user.id not in commission_plan.user_ids.mapped('user_id').ids:
                # User not in plan's user list, skip
                _logger.info(_("Skipping %s (%s) - not in plan's user list") % (user.name, role))
                continue

            # Check if commission already exists for this specific user
            existing_commission = self.env['sale.commission'].search([
                ('invoice_id', '=', invoice.id),
                ('sale_order_id', '=', self.id),
                ('user_id', '=', user.id),
                ('role', '=', role)
            ], limit=1)

            if existing_commission:
                _logger.info(_("Commission already exists for %s (%s) on order %s") % (user.name, role, self.name))
                continue

            # Get role configuration
            role_config = self.env['hr.commission.role.config'].search([
                ('plan_id', '=', commission_plan.id),
                ('role', '=', role),
                ('active', '=', True)
            ], limit=1)

            if not role_config:
                _logger.warning(_("No active role config found for %s in plan %s") % (role, commission_plan.name))
                continue

            # Create commission record
            try:
                self.env['sale.commission'].create({
                    'user_id': user.id,
                    'role': role,
                    'sale_order_id': self.id,
                    'invoice_id': invoice.id,
                    'plan_id': commission_plan.id,
                    'date': invoice.invoice_date or fields.Date.today(),
                    'period': period,
                    'base_amount': base_amount,
                    'payment_status': 'unpaid',
                    'state': 'confirmed',
                    'company_id': self.company_id.id,
                    'currency_id': self.currency_id.id,
                })
                commissions_created += 1
                _logger.info(_("Created commission for %s (%s) - Order: %s, Invoice: %s") % (user.name, role, self.name, invoice.name))
            except Exception as e:
                _logger.error(_("Error creating commission for %s: %s") % (user.name, str(e)))

        return commissions_created

    def action_view_commissions(self):
        """View commissions for this sale order"""
        self.ensure_one()
        return {
            'name': _('Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id}
        }

    @api.model
    def cron_generate_commissions(self):
        """
        Scheduled action to generate commissions for all eligible sale orders
        Runs nightly to process any orders with paid invoices
        """
        _logger.info("Starting scheduled commission generation...")

        # Find confirmed sale orders with paid invoices that haven't had commissions generated
        orders = self.search([
            ('state', 'in', ['sale', 'done']),
            ('user_id', '!=', False),
        ])

        total_orders_processed = 0
        total_commissions_created = 0
        errors = []

        for order in orders:
            try:
                # Check if order has paid invoices
                has_paid_invoices = order.invoice_ids.filtered(
                    lambda inv: inv.move_type == 'out_invoice'
                    and inv.state == 'posted'
                    and inv.payment_state in ['paid', 'in_payment']
                )

                if has_paid_invoices:
                    result = order._generate_commissions()
                    if result['success']:
                        total_orders_processed += 1
                        total_commissions_created += result['commissions_created']
                        _logger.info(_("Processed order %s: %s") % (order.name, result['message']))
                    elif result['message'] and 'already exist' not in result['message']:
                        # Only log if it's not about existing commissions
                        _logger.debug(_("Skipped order %s: %s") % (order.name, result['message']))

            except Exception as e:
                error_msg = _("Error processing order %s: %s") % (order.name, str(e))
                _logger.error(error_msg)
                errors.append(error_msg)

        _logger.info(
            _("Scheduled commission generation completed. Processed %s orders, created %s commissions.") % (total_orders_processed, total_commissions_created)
        )

        if errors:
            _logger.warning(_("Encountered %s errors during commission generation") % len(errors))

        return {
            'orders_processed': total_orders_processed,
            'commissions_created': total_commissions_created,
            'errors': errors
        }
