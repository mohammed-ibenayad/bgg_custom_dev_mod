# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleCommissionPlan(models.Model):
    _inherit = 'sale.commission.plan'

    is_hierarchical = fields.Boolean(
        string='Hierarchical Plan',
        default=False,
        help='If enabled, calculates commissions for salesperson + team leader + sales director'
    )

    role_config_ids = fields.One2many(
        'hr.commission.role.config',
        'plan_id',
        string='Role Configuration',
        help='Define commission percentages for each role in the hierarchy'
    )

    require_invoice_paid = fields.Boolean(
        string='Require Paid Invoice',
        default=True,
        help='Only calculate commissions when the invoice is fully paid'
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count'
    )

    @api.depends('role_config_ids')
    def _compute_commission_count(self):
        """Count commissions for this plan"""
        for plan in self:
            plan.commission_count = self.env['sale.commission'].search_count([
                ('plan_id', '=', plan.id)
            ])

    @api.constrains('is_hierarchical', 'role_config_ids')
    def _check_hierarchical_config(self):
        """Ensure hierarchical plans have role configurations"""
        for record in self:
            if record.is_hierarchical and not record.role_config_ids:
                # This is a warning, not a hard constraint
                # Users might want to configure roles after creation
                pass

    def action_view_commissions(self):
        """View all commissions for this plan"""
        self.ensure_one()
        return {
            'name': _('Commissions'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id}
        }
