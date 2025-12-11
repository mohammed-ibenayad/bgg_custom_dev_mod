# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Constraint
from odoo.exceptions import ValidationError


class SaleCommissionRole(models.Model):
    _name = 'sale.commission.role'
    _description = 'Commission Role'
    _order = 'sequence, name'

    name = fields.Char(
        string='Role Name',
        required=True,
        translate=True,
        help='Name of the commission role (e.g., Salesperson, Team Leader)'
    )

    code = fields.Char(
        string='Code',
        required=True,
        help='Unique identifier for technical use (e.g., SP, TL, SD)'
    )

    sequence = fields.Integer(
        string='Hierarchy Level',
        default=10,
        required=True,
        help='Defines position in hierarchy. Lower = bottom, Higher = top (e.g., 10=Salesperson, 20=Team Leader, 30=Director)'
    )

    description = fields.Text(
        string='Description',
        translate=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    color = fields.Integer(
        string='Color',
        help='Color for UI display (kanban, etc.)'
    )

    # Hierarchy configuration
    is_base_role = fields.Boolean(
        string='Is Base Role',
        default=False,
        help='Base roles are at the bottom of hierarchy (e.g., Salesperson). They create commissions from sales.'
    )

    requires_manager = fields.Boolean(
        string='Requires Manager',
        default=True,
        help='If True, users with this role must have a manager assigned'
    )

    can_manage_subordinates = fields.Boolean(
        string='Can Manage Subordinates',
        default=True,
        help='If True, users with this role can have team members reporting to them'
    )

    # Statistics
    user_count = fields.Integer(
        string='Active Users',
        compute='_compute_user_count'
    )

    commission_count = fields.Integer(
        string='Commissions',
        compute='_compute_commission_count'
    )

    # Odoo 19: SQL constraints using new Constraint format
    Constraint('code_company_unique', 'unique(code, company_id)', 'Role code must be unique per company!')
    Constraint('name_company_unique', 'unique(name, company_id)', 'Role name must be unique per company!')

    @api.depends('user_count')
    def _compute_user_count(self):
        """Count active users with this role"""
        for role in self:
            role.user_count = self.env['res.users'].search_count([
                ('commission_role_id', '=', role.id),
                ('active', '=', True)
            ])

    @api.depends('commission_count')
    def _compute_commission_count(self):
        """Count commissions with this role"""
        for role in self:
            role.commission_count = self.env['sale.commission'].search_count([
                ('role_id', '=', role.id)
            ])

    @api.constrains('sequence')
    def _check_sequence(self):
        """Ensure sequence is positive"""
        for role in self:
            if role.sequence < 0:
                raise ValidationError(_('Hierarchy level must be a positive number'))

    def unlink(self):
        """Prevent deletion of roles with active users or commissions"""
        for role in self:
            if role.user_count > 0:
                raise ValidationError(
                    _('Cannot delete role "%s" because %d user(s) are assigned to it. '
                      'Please reassign users first.') % (role.name, role.user_count)
                )
            if role.commission_count > 0:
                raise ValidationError(
                    _('Cannot delete role "%s" because %d commission(s) exist with it. '
                      'You can deactivate the role instead.') % (role.name, role.commission_count)
                )
        return super().unlink()

    def action_view_users(self):
        """View users with this role"""
        self.ensure_one()
        return {
            'name': _('Users - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('commission_role_id', '=', self.id)],
            'context': {'default_commission_role_id': self.id}
        }

    def action_view_commissions(self):
        """View commissions with this role"""
        self.ensure_one()
        return {
            'name': _('Commissions - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.commission',
            'view_mode': 'tree,form',
            'domain': [('role_id', '=', self.id)],
            'context': {'default_role_id': self.id}
        }
