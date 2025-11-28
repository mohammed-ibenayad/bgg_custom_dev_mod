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
        return self._generate_commissions()

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
            result['message'] = f"Order {self.name} is not confirmed (state: {self.state})"
            return result

        # Check if salesperson is assigned
        if not self.user_id:
            result['message'] = f"No salesperson assigned to order {self.name}"
            return result

        # Check if salesperson has commission role
        if not self.user_id.commission_role:
            result['message'] = f"Salesperson {self.user_id.name} has no commission role set"
            return result

        # Get paid invoices for this sale order
        paid_invoices = self.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice'
            and inv.state == 'posted'
            and inv.payment_state in ['paid', 'in_payment']
        )

        if not paid_invoices:
            result['message'] = f"No paid invoices found for order {self.name}"
            return result

        # Find applicable commission plan
        commission_plan = self.env['sale.commission.plan'].search([
            ('is_hierarchical', '=', True),
            ('state', '=', 'approved'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not commission_plan:
            result['message'] = "No approved hierarchical commission plan found"
            return result

        # Check if plan requires paid invoice
        if commission_plan.require_invoice_paid and not paid_invoices:
            result['message'] = f"Commission plan requires paid invoices, but none found for order {self.name}"
            return result

        # Process each paid invoice
        commissions_created = 0
        for invoice in paid_invoices:
            created = self._create_commissions_for_invoice(invoice, commission_plan)
            commissions_created += created

        if commissions_created > 0:
            self.commissions_generated = True
            result['success'] = True
            result['message'] = f"Successfully created {commissions_created} commission(s) for order {self.name}"
            result['commissions_created'] = commissions_created
        else:
            result['message'] = f"No new commissions created for order {self.name} (may already exist)"

        return result

    def _create_commissions_for_invoice(self, invoice, commission_plan):
        """
        Create commission records for a specific invoice
        Returns: number of commissions created
        """
        self.ensure_one()

        # Check if commissions already exist for this invoice and sale order
        existing = self.env['sale.commission'].search([
            ('invoice_id', '=', invoice.id),
            ('sale_order_id', '=', self.id)
        ])

        if existing:
            _logger.info(f"Commissions already exist for invoice {invoice.name} and order {self.name}")
            return 0

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
            # Get role configuration
            role_config = self.env['hr.commission.role.config'].search([
                ('plan_id', '=', commission_plan.id),
                ('role', '=', role),
                ('active', '=', True)
            ], limit=1)

            if not role_config:
                _logger.warning(f"No active role config found for {role} in plan {commission_plan.name}")
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
                _logger.info(f"Created commission for {user.name} ({role}) - Order: {self.name}, Invoice: {invoice.name}")
            except Exception as e:
                _logger.error(f"Error creating commission for {user.name}: {str(e)}")

        return commissions_created

    def action_view_commissions(self):
        """View commissions for this sale order"""
        self.ensure_one()
        return {
            'name': _('Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'tree,form',
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
                        _logger.info(f"Processed order {order.name}: {result['message']}")
                    elif result['message'] and 'already exist' not in result['message']:
                        # Only log if it's not about existing commissions
                        _logger.debug(f"Skipped order {order.name}: {result['message']}")

            except Exception as e:
                error_msg = f"Error processing order {order.name}: {str(e)}"
                _logger.error(error_msg)
                errors.append(error_msg)

        _logger.info(
            f"Scheduled commission generation completed. "
            f"Processed {total_orders_processed} orders, "
            f"created {total_commissions_created} commissions."
        )

        if errors:
            _logger.warning(f"Encountered {len(errors)} errors during commission generation")

        return {
            'orders_processed': total_orders_processed,
            'commissions_created': total_commissions_created,
            'errors': errors
        }
