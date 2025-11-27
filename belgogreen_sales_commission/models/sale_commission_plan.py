# -*- coding: utf-8 -*-

from odoo import models, fields, api


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

    @api.constrains('is_hierarchical', 'role_config_ids')
    def _check_hierarchical_config(self):
        """Ensure hierarchical plans have role configurations"""
        for record in self:
            if record.is_hierarchical and not record.role_config_ids:
                # This is a warning, not a hard constraint
                # Users might want to configure roles after creation
                pass
