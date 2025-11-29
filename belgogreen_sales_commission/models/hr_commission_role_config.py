# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrCommissionRoleConfig(models.Model):
    _name = 'hr.commission.role.config'
    _description = 'Commission Configuration by Role'
    _order = 'plan_id, role'

    plan_id = fields.Many2one(
        'sale.commission.plan',
        string=_('Commission Plan'),
        required=True,
        ondelete='cascade',
        help=_('The commission plan this configuration applies to')
    )

    role = fields.Selection([
        ('salesperson', _('Salesperson')),
        ('team_leader', _('Team Leader')),
        ('sales_director', _('Sales Director'))
    ], string=_('Role'), required=True, help=_('The role this percentage applies to'))

    default_percentage = fields.Float(
        string=_('Default Percentage'),
        required=True,
        digits=(5, 2),
        help=_('Default commission percentage for this role (e.g., 5.00 for 5%)')
    )

    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        related='plan_id.company_id',
        store=True,
        readonly=True
    )

    active = fields.Boolean(
        string=_('Active'),
        default=True
    )

    _sql_constraints = [
        ('unique_plan_role',
         'unique(plan_id, role)',
         'Only one percentage configuration per role per plan is allowed!')
    ]

    @api.constrains('default_percentage')
    def _check_percentage(self):
        """Validate that percentage is between 0 and 100"""
        for record in self:
            if record.default_percentage < 0 or record.default_percentage > 100:
                raise ValidationError(
                    _('Commission percentage must be between 0 and 100. Got: %s') % record.default_percentage
                )

    def _compute_display_name(self):
        """Custom display name for Odoo 18"""
        for record in self:
            role_label = dict(record._fields['role'].selection).get(record.role, record.role)
            record.display_name = _('%(plan)s - %(role)s (%(percentage)s%%)') % {
                'plan': record.plan_id.name,
                'role': role_label,
                'percentage': record.default_percentage
            }
