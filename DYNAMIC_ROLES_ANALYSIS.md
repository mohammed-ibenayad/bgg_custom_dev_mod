# Dynamic Roles Implementation Analysis
## Belgogreen Sales Commission Module - Development Environment

**Date:** December 5, 2025
**Environment:** Development (No Production Data)
**Objective:** Convert hardcoded 3-tier role system to dynamic, manager-configurable roles

---

## Executive Summary

Since we're in **development mode with no production data**, we can implement a clean, optimal solution without migration concerns. The current system uses **3 hardcoded roles** defined as Selection fields. We'll convert this to a fully dynamic system where sales managers can create and configure unlimited roles.

### What We'll Do:
- ✅ Create new `sale.commission.role` master model
- ✅ Replace all Selection fields with Many2one references
- ✅ Replace dual hierarchy fields (`team_leader_id`, `sales_director_id`) with single generic `commission_manager_id`
- ✅ Update hierarchy logic to support N-level hierarchies
- ✅ Modify commission calculation to work dynamically
- ✅ Update all views and UI components

### Key Benefits:
- **No data migration** - Clean slate implementation
- **No backward compatibility** - Optimal design choices
- **Lower risk** - No production data to corrupt
- **Faster delivery** - Skip all migration complexity

**Estimated Effort:** 15-20 developer days (3-4 weeks)
**Risk Level:** LOW-MEDIUM (thorough testing still required for commission logic)

---

## 1. Current State Analysis

### 1.1 Hardcoded Role Locations

| File | Lines | Field Type | Usage |
|------|-------|-----------|--------|
| `res_users.py` | 10-14 | Selection | User role assignment |
| `hr_commission_role_config.py` | 20-24 | Selection | Role percentage config |
| `sale_commission.py` | 30-35 | Selection | Commission role tracking |
| `res_users.py` | 122-128 | Selection | Anomaly type tracking |

### 1.2 Current Role Structure

```python
HARDCODED_ROLES = [
    ('salesperson', 'Salesperson'),       # Level 1: Bottom of hierarchy
    ('team_leader', 'Team Leader'),       # Level 2: Middle management
    ('sales_director', 'Sales Director')  # Level 3: Top of hierarchy
]
```

### 1.3 Current Hierarchy Implementation

**Problems with Current Design:**
```python
# res_users.py - Hardcoded hierarchy fields
team_leader_id = fields.Many2one('res.users', domain=[('commission_role', '=', 'team_leader')])
sales_director_id = fields.Many2one('res.users', domain=[('commission_role', '=', 'sales_director')])
```

**Issues:**
- 🔴 Limited to exactly 3 levels - cannot add 4th tier
- 🔴 Hardcoded field names require code changes for new roles
- 🔴 Commission calculation has hardcoded hierarchy traversal
- 🔴 Anomaly detection checks for specific role names
- 🔴 UI shows separate fields for each level

---

## 2. Proposed Dynamic Solution

### 2.1 New Master Data Model

**Create: `models/sale_commission_role.py`**

```python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
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

    _sql_constraints = [
        ('code_company_unique',
         'unique(code, company_id)',
         'Role code must be unique per company!'),
        ('name_company_unique',
         'unique(name, company_id)',
         'Role name must be unique per company!')
    ]

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
```

### 2.2 Model Field Changes

#### A. `res_users.py` - User Model

**REMOVE:**
```python
commission_role = fields.Selection([...])      # DELETE
team_leader_id = fields.Many2one(...)          # DELETE
sales_director_id = fields.Many2one(...)       # DELETE
team_member_ids = fields.One2many(...)         # DELETE
director_team_ids = fields.One2many(...)       # DELETE
```

**ADD:**
```python
# Replace Selection with Many2one to dynamic role
commission_role_id = fields.Many2one(
    'sale.commission.role',
    string='Commission Role',
    domain="[('company_id', '=', company_id), ('active', '=', True)]",
    help='The role of this user in the commission hierarchy'
)

# Replace dual hierarchy fields with single generic manager field
commission_manager_id = fields.Many2one(
    'res.users',
    string='Commission Manager',
    domain="[('commission_role_id', '!=', False), ('id', '!=', id), ('company_id', '=', company_id)]",
    help='Direct manager in the commission hierarchy'
)

# Reverse relation for subordinates
commission_subordinate_ids = fields.One2many(
    'res.users',
    'commission_manager_id',
    string='Direct Subordinates',
    help='Users who report directly to this user in commission hierarchy'
)
```

#### B. `hr_commission_role_config.py` - Role Configuration

**CHANGE:**
```python
# OLD
role = fields.Selection([...], required=True)

# NEW
role_id = fields.Many2one(
    'sale.commission.role',
    string='Role',
    required=True,
    domain="[('company_id', '=', company_id)]",
    help='The role this percentage applies to'
)

_sql_constraints = [
    ('unique_plan_role',
     'unique(plan_id, role_id)',  # Changed from role to role_id
     'Only one percentage per role per plan!')
]
```

**UPDATE display_name:**
```python
def _compute_display_name(self):
    for record in self:
        record.display_name = _('%(plan)s - %(role)s (%(percentage)s%%)') % {
            'plan': record.plan_id.name,
            'role': record.role_id.name,  # Changed from dict lookup
            'percentage': record.default_percentage
        }
```

#### C. `sale_commission.py` - Commission Records

**CHANGE:**
```python
# OLD
role = fields.Selection([...], required=True, tracking=True)

# NEW
role_id = fields.Many2one(
    'sale.commission.role',
    string='Role',
    required=True,
    tracking=True,
    help='The role of the user receiving this commission'
)
```

**UPDATE percentage computation:**
```python
@api.depends('percentage_override', 'plan_id', 'role_id')  # Changed from 'role'
def _compute_commission_percentage(self):
    for commission in self:
        if commission.percentage_override:
            commission.commission_percentage = commission.percentage_override
        else:
            config = self.env['hr.commission.role.config'].search([
                ('plan_id', '=', commission.plan_id.id),
                ('role_id', '=', commission.role_id.id)  # Changed from 'role'
            ], limit=1)
            commission.commission_percentage = config.default_percentage if config else 0.0
```

---

## 3. Commission Calculation Logic - Dynamic Hierarchy

### 3.1 NEW Hierarchy Traversal Method

**Add to `sale_order.py`:**

```python
def _get_commission_hierarchy(self, base_user):
    """
    Traverse hierarchy upwards from base user to collect all managers who should receive commission.

    Supports unlimited hierarchy levels by following commission_manager_id chain.
    Includes cycle detection to prevent infinite loops.

    Args:
        base_user: res.users record (typically the salesperson)

    Returns:
        list of tuples: [(user, role), ...] ordered from bottom to top of hierarchy
    """
    hierarchy = []
    current_user = base_user
    seen_ids = set()  # Cycle detection

    while current_user and current_user.id not in seen_ids:
        # Only include users with a commission role
        if current_user.commission_role_id:
            hierarchy.append((current_user, current_user.commission_role_id))
            seen_ids.add(current_user.id)

        # Move up to manager
        current_user = current_user.commission_manager_id

        # Safety check: prevent infinite loops
        if len(seen_ids) > 20:
            _logger.warning("Hierarchy depth exceeds 20 levels for user %s. Possible circular reference.", base_user.name)
            break

    return hierarchy
```

### 3.2 UPDATE Commission Creation

**Replace in `sale_order.py:135-161`:**

```python
def _create_commissions_for_invoice(self, invoice, commission_plan):
    """
    Create commission records for a specific invoice.
    Now supports dynamic N-level hierarchies.
    """
    self.ensure_one()

    salesperson = self.user_id
    base_amount = invoice.amount_total

    # Build commission hierarchy dynamically
    users_to_commission = self._get_commission_hierarchy(salesperson)

    if not users_to_commission:
        _logger.info("No commission hierarchy found for user %s", salesperson.name)
        return 0

    # Calculate period
    period = invoice.invoice_date.strftime('%Y-%m') if invoice.invoice_date else fields.Date.today().strftime('%Y-%m')

    # Create commission records
    commissions_created = 0
    for user, role in users_to_commission:
        # Check if user is in plan's allowed users list
        if commission_plan.user_ids and user.id not in commission_plan.user_ids.mapped('user_id').ids:
            _logger.info("Skipping %s (%s) - not in plan's user list", user.name, role.name)
            continue

        # Check if commission already exists
        existing = self.env['sale.commission'].search([
            ('invoice_id', '=', invoice.id),
            ('sale_order_id', '=', self.id),
            ('user_id', '=', user.id),
            ('role_id', '=', role.id)
        ], limit=1)

        if existing:
            _logger.info("Commission already exists for %s (%s) on order %s", user.name, role.name, self.name)
            continue

        # Get role configuration
        role_config = self.env['hr.commission.role.config'].search([
            ('plan_id', '=', commission_plan.id),
            ('role_id', '=', role.id),
            ('active', '=', True)
        ], limit=1)

        if not role_config:
            _logger.warning("No active role config found for %s in plan %s", role.name, commission_plan.name)
            continue

        # Create commission record
        try:
            self.env['sale.commission'].create({
                'user_id': user.id,
                'role_id': role.id,
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
            _logger.info("Created commission for %s (%s) - Order: %s, Invoice: %s",
                        user.name, role.name, self.name, invoice.name)
        except Exception as e:
            _logger.error("Error creating commission for %s: %s", user.name, str(e))

    return commissions_created
```

---

## 4. Anomaly Detection - Dynamic Version

### 4.1 REPLACE Anomaly Detection Logic

**In `res_users.py`, replace lines 122-340:**

```python
# New generic anomaly types
anomaly_type = fields.Selection([
    ('missing_manager', 'Missing Required Manager'),
    ('top_role_has_manager', 'Top-level role should not have manager'),
    ('no_role_with_manager', 'Manager assigned without commission role'),
    ('manager_lower_level', 'Manager has lower hierarchy level than subordinate'),
    ('circular_hierarchy', 'Circular reference in hierarchy'),
], string='Anomaly Type', compute='_compute_hierarchy_anomalies', store=True)

@api.depends('commission_role_id', 'commission_manager_id',
             'commission_manager_id.commission_role_id')
def _compute_hierarchy_anomalies(self):
    """Detect hierarchy anomalies using dynamic role configuration"""
    for user in self:
        anomaly = False
        anomaly_type = False
        description = ''

        if user.commission_role_id:
            role = user.commission_role_id

            # ANOMALY 1: Role requires manager but none assigned
            if role.requires_manager and not user.commission_manager_id:
                anomaly = True
                anomaly_type = 'missing_manager'
                description = _("User with role '%s' requires a manager but none is assigned. "
                              "Please assign a manager in the commission hierarchy.") % role.name

            # ANOMALY 2: Role shouldn't have manager (is_base_role=False, requires_manager=False)
            elif not role.requires_manager and user.commission_manager_id:
                anomaly = True
                anomaly_type = 'top_role_has_manager'
                description = _("User with role '%s' is a top-level role and should not have a manager. "
                              "Current manager: %s") % (role.name, user.commission_manager_id.name)

            # ANOMALY 3: Manager has lower hierarchy level (sequence) than subordinate
            elif user.commission_manager_id and user.commission_manager_id.commission_role_id:
                manager_level = user.commission_manager_id.commission_role_id.sequence
                user_level = role.sequence

                if manager_level <= user_level:
                    anomaly = True
                    anomaly_type = 'manager_lower_level'
                    description = _("Hierarchy issue: Manager '%s' (level %d - %s) has same or lower hierarchy level "
                                  "than subordinate '%s' (level %d - %s). Manager should have higher level.") % (
                                      user.commission_manager_id.name, manager_level,
                                      user.commission_manager_id.commission_role_id.name,
                                      user.name, user_level, role.name
                                  )

        # ANOMALY 4: Manager assigned but no role
        elif not user.commission_role_id and user.commission_manager_id:
            anomaly = True
            anomaly_type = 'no_role_with_manager'
            description = _("User has manager '%s' assigned but no commission role defined. "
                          "Please assign a commission role first.") % user.commission_manager_id.name

        # ANOMALY 5: Detect circular hierarchy
        if user.commission_manager_id and not anomaly:
            if user._has_circular_hierarchy():
                anomaly = True
                anomaly_type = 'circular_hierarchy'
                description = _("Circular reference detected in commission hierarchy. "
                              "User is in their own management chain.")

        user.has_hierarchy_anomaly = anomaly
        user.anomaly_type = anomaly_type
        user.anomaly_description = description

def _has_circular_hierarchy(self):
    """Check if user's hierarchy contains a circular reference"""
    self.ensure_one()
    visited = set()
    current = self

    while current.commission_manager_id:
        if current.id in visited:
            return True  # Circular reference found
        visited.add(current.id)
        current = current.commission_manager_id

        if len(visited) > 50:  # Safety limit
            return True

    return False
```

### 4.2 UPDATE Search Method

```python
def _search_has_hierarchy_anomaly(self, operator, value):
    """Search method for has_hierarchy_anomaly field"""
    # Trigger recomputation for all users with roles
    users = self.search([
        '|',
        ('commission_role_id', '!=', False),
        ('commission_manager_id', '!=', False)
    ])

    # Get users with anomalies after computation
    if operator == '=' and value:
        return [('id', 'in', users.filtered('has_hierarchy_anomaly').ids)]
    elif operator == '=' and not value:
        return [('id', 'in', users.filtered(lambda u: not u.has_hierarchy_anomaly).ids)]

    return []
```

---

## 5. View Updates

### 5.1 User Form View

**File: `views/res_users_views.xml`**

**REPLACE hierarchy section:**

```xml
<group name="commission_hierarchy" string="Commission Hierarchy">
    <field name="commission_role_id"
           options="{'no_create': True, 'no_open': True}"/>

    <field name="commission_manager_id"
           domain="[('commission_role_id.sequence', '>', commission_role_id.sequence),
                    ('id', '!=', id),
                    ('company_id', '=', company_id)]"
           options="{'no_create': True}"
           context="{'show_commission_role': True}"
           attrs="{'invisible': [('commission_role_id', '=', False)]}"/>

    <field name="commission_subordinate_ids"
           widget="many2many_tags"
           readonly="1"
           attrs="{'invisible': [('commission_subordinate_ids', '=', [])]}"/>

    <!-- Anomaly warnings -->
    <field name="has_hierarchy_anomaly" invisible="1"/>
    <field name="anomaly_type" invisible="1"/>
    <div class="alert alert-warning" role="alert"
         attrs="{'invisible': [('has_hierarchy_anomaly', '=', False)]}">
        <field name="anomaly_description" readonly="1" nolabel="1"/>
    </div>
</group>
```

### 5.2 Team Management Views

**File: `views/team_management_views.xml`**

**UPDATE tree view for dynamic roles:**

```xml
<tree string="Commission Hierarchy"
      decoration-muted="not active"
      decoration-danger="has_hierarchy_anomaly">
    <field name="name"/>
    <field name="commission_role_id"/>
    <field name="commission_manager_id"/>
    <field name="subordinate_count" string="Subordinates"/>
    <field name="commission_count" string="Commissions"/>
    <field name="commission_unpaid_total" string="Unpaid" widget="monetary"/>
    <field name="has_hierarchy_anomaly" invisible="1"/>
    <field name="active" invisible="1"/>
</tree>
```

**ADD dynamic filters:**

```xml
<search>
    <field name="name"/>
    <field name="commission_role_id"/>
    <field name="commission_manager_id"/>

    <filter name="has_anomaly"
            string="With Anomalies"
            domain="[('has_hierarchy_anomaly', '=', True)]"/>

    <filter name="has_subordinates"
            string="Managers"
            domain="[('has_subordinates', '=', True)]"/>

    <group expand="0" string="Group By">
        <filter name="group_by_role"
                string="Role"
                context="{'group_by': 'commission_role_id'}"/>
        <filter name="group_by_manager"
                string="Manager"
                context="{'group_by': 'commission_manager_id'}"/>
    </group>
</search>
```

### 5.3 Commission Plan - Role Percentages

**File: `views/sale_commission_plan_views.xml`**

**UPDATE role configuration tree:**

```xml
<tree string="Role Percentages" editable="bottom">
    <field name="role_id"
           domain="[('company_id', '=', parent.company_id)]"
           options="{'no_create': True}"/>
    <field name="default_percentage" widget="percentage"/>
    <field name="active"/>
</tree>
```

### 5.4 Commission Filters

**File: `views/sale_commission_views.xml`**

**UPDATE search view:**

```xml
<search>
    <field name="name"/>
    <field name="user_id"/>
    <field name="role_id"/>
    <field name="plan_id"/>

    <filter name="unpaid"
            string="Unpaid"
            domain="[('payment_status', '=', 'unpaid')]"/>

    <group expand="0" string="Group By">
        <filter name="group_by_role"
                string="Role"
                context="{'group_by': 'role_id'}"/>
        <filter name="group_by_user"
                string="User"
                context="{'group_by': 'user_id'}"/>
        <filter name="group_by_period"
                string="Period"
                context="{'group_by': 'period'}"/>
    </group>
</search>
```

---

## 6. New Configuration Interface

### 6.1 Role Management Views

**Create: `views/sale_commission_role_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Form View -->
    <record id="view_sale_commission_role_form" model="ir.ui.view">
        <field name="name">sale.commission.role.form</field>
        <field name="model">sale.commission.role</field>
        <field name="arch" type="xml">
            <form string="Commission Role">
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_users"
                                type="object"
                                class="oe_stat_button"
                                icon="fa-users">
                            <field name="user_count" widget="statinfo" string="Users"/>
                        </button>
                        <button name="action_view_commissions"
                                type="object"
                                class="oe_stat_button"
                                icon="fa-money">
                            <field name="commission_count" widget="statinfo" string="Commissions"/>
                        </button>
                    </div>

                    <widget name="web_ribbon" title="Archived" bg_color="bg-danger"
                            attrs="{'invisible': [('active', '=', True)]}"/>

                    <group>
                        <group>
                            <field name="name"/>
                            <field name="code"/>
                            <field name="sequence"
                                   help="Lower numbers = bottom of hierarchy (e.g., 10=Salesperson, 20=Team Leader, 30=Director)"/>
                            <field name="color" widget="color_picker"/>
                        </group>
                        <group>
                            <field name="company_id" groups="base.group_multi_company"/>
                            <field name="active" widget="boolean_toggle"/>
                            <field name="is_base_role"
                                   help="Check if this is the base role that creates commissions from sales"/>
                            <field name="requires_manager"
                                   help="Users with this role must have a manager assigned"/>
                            <field name="can_manage_subordinates"
                                   help="Users with this role can have team members"/>
                        </group>
                    </group>

                    <group>
                        <field name="description" placeholder="Describe this role's responsibilities..."/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Tree View -->
    <record id="view_sale_commission_role_tree" model="ir.ui.view">
        <field name="name">sale.commission.role.tree</field>
        <field name="model">sale.commission.role</field>
        <field name="arch" type="xml">
            <tree string="Commission Roles"
                  decoration-muted="not active">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="code"/>
                <field name="sequence" invisible="1"/>
                <field name="is_base_role"/>
                <field name="requires_manager"/>
                <field name="can_manage_subordinates"/>
                <field name="user_count"/>
                <field name="commission_count"/>
                <field name="active" widget="boolean_toggle"/>
            </tree>
        </field>
    </record>

    <!-- Action -->
    <record id="action_sale_commission_role" model="ir.actions.act_window">
        <field name="name">Commission Roles</field>
        <field name="res_model">sale.commission.role</field>
        <field name="view_mode">tree,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Create your first commission role!
            </p>
            <p>
                Define roles in your sales commission hierarchy (e.g., Salesperson, Team Leader, Sales Director).
                Set the hierarchy level (sequence) to determine who reports to whom.
            </p>
        </field>
    </record>

    <!-- Menu -->
    <menuitem id="menu_sale_commission_role"
              name="Commission Roles"
              parent="sale.sale_menu_root"
              action="action_sale_commission_role"
              sequence="90"
              groups="belgogreen_sales_commission.group_commission_manager"/>
</odoo>
```

### 6.2 Security Rules

**Update: `security/ir.model.access.csv`**

Add these lines:
```csv
access_sale_commission_role_user,sale.commission.role.user,model_sale_commission_role,group_commission_user,1,0,0,0
access_sale_commission_role_manager,sale.commission.role.manager,model_sale_commission_role,group_commission_manager,1,1,1,1
```

---

## 7. Data Setup

### 7.1 Default Roles

**Create: `data/sale_commission_role_data.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Base Salesperson Role -->
        <record id="role_salesperson" model="sale.commission.role">
            <field name="name">Salesperson</field>
            <field name="code">SP</field>
            <field name="sequence">10</field>
            <field name="is_base_role">True</field>
            <field name="requires_manager">True</field>
            <field name="can_manage_subordinates">False</field>
            <field name="description">Front-line sales representatives who close deals and generate commissions</field>
            <field name="color">1</field>
        </record>

        <!-- Team Leader Role -->
        <record id="role_team_leader" model="sale.commission.role">
            <field name="name">Team Leader</field>
            <field name="code">TL</field>
            <field name="sequence">20</field>
            <field name="is_base_role">False</field>
            <field name="requires_manager">True</field>
            <field name="can_manage_subordinates">True</field>
            <field name="description">Manages a team of salespeople and receives commissions on team sales</field>
            <field name="color">3</field>
        </record>

        <!-- Sales Director Role -->
        <record id="role_sales_director" model="sale.commission.role">
            <field name="name">Sales Director</field>
            <field name="code">SD</field>
            <field name="sequence">30</field>
            <field name="is_base_role">False</field>
            <field name="requires_manager">False</field>
            <field name="can_manage_subordinates">True</field>
            <field name="description">Top-level sales management overseeing multiple teams</field>
            <field name="color">2</field>
        </record>
    </data>
</odoo>
```

---

## 8. Implementation Checklist

### Phase 1: Foundation (Days 1-3)
- [ ] Create `sale_commission_role.py` model
- [ ] Create role views XML
- [ ] Add security rules
- [ ] Create default role data
- [ ] Update `__manifest__.py` with new files
- [ ] Test role creation/management

### Phase 2: Model Updates (Days 4-7)
- [ ] Update `res_users.py`:
  - [ ] Replace `commission_role` Selection with `commission_role_id` M2o
  - [ ] Replace `team_leader_id`/`sales_director_id` with `commission_manager_id`
  - [ ] Update `commission_subordinate_ids`
  - [ ] Remove old One2many fields (`team_member_ids`, `director_team_ids`)
- [ ] Update `sale_commission.py`:
  - [ ] Replace `role` Selection with `role_id` M2o
  - [ ] Update `_compute_commission_percentage` method
- [ ] Update `hr_commission_role_config.py`:
  - [ ] Replace `role` Selection with `role_id` M2o
  - [ ] Update SQL constraint
  - [ ] Update `_compute_display_name` method

### Phase 3: Logic Updates (Days 8-12)
- [ ] Update `sale_order.py`:
  - [ ] Add `_get_commission_hierarchy()` method
  - [ ] Replace hardcoded hierarchy in `_create_commissions_for_invoice()`
  - [ ] Update logging to use `role.name` instead of hardcoded values
- [ ] Update `account_move.py`:
  - [ ] Apply same hierarchy changes as sale_order.py
- [ ] Update `res_users.py` anomaly detection:
  - [ ] Replace hardcoded anomaly types
  - [ ] Implement `_compute_hierarchy_anomalies()` with dynamic logic
  - [ ] Add `_has_circular_hierarchy()` method
  - [ ] Update `_search_has_hierarchy_anomaly()`
- [ ] Update role validation in `write()` method

### Phase 4: View Updates (Days 13-15)
- [ ] Update `res_users_views.xml`:
  - [ ] Replace role/hierarchy fields in form view
  - [ ] Update filters to use `commission_role_id`
- [ ] Update `team_management_views.xml`:
  - [ ] Update tree/kanban views for dynamic roles
  - [ ] Update filters and grouping
- [ ] Update `sale_commission_plan_views.xml`:
  - [ ] Update role percentages tab tree view
- [ ] Update `sale_commission_views.xml`:
  - [ ] Update filters to use `role_id`
  - [ ] Update group_by contexts

### Phase 5: Testing (Days 16-18)
- [ ] Create test data:
  - [ ] 3+ roles with different hierarchy levels
  - [ ] Users assigned to each role
  - [ ] Commission plans with role percentages
- [ ] Test scenarios:
  - [ ] 2-level hierarchy (Salesperson → Team Leader)
  - [ ] 3-level hierarchy (SP → TL → Director)
  - [ ] 4-level hierarchy (add Regional Manager)
  - [ ] Orphaned user (no manager)
  - [ ] Circular hierarchy detection
  - [ ] Manager with lower sequence than subordinate
- [ ] Test commission generation:
  - [ ] Verify all hierarchy levels get commissions
  - [ ] Verify percentages calculated correctly
  - [ ] Verify no duplicate commissions
- [ ] Test anomaly detection:
  - [ ] Missing manager
  - [ ] Top role with manager
  - [ ] Hierarchy level violations

### Phase 6: Documentation (Days 19-20)
- [ ] User guide for creating roles
- [ ] User guide for assigning hierarchy
- [ ] Admin guide for commission plan setup
- [ ] Developer notes for future customization

---

## 9. Testing Scenarios

### 9.1 Role Management Tests

```python
# Test 1: Create new role
role = env['sale.commission.role'].create({
    'name': 'Regional Manager',
    'code': 'RM',
    'sequence': 25,  # Between TL (20) and SD (30)
    'requires_manager': True,
    'can_manage_subordinates': True
})

# Test 2: Delete role with users (should fail)
try:
    role.unlink()  # Should raise ValidationError if users assigned
except ValidationError:
    pass  # Expected

# Test 3: Deactivate role
role.active = False  # Should work
```

### 9.2 Hierarchy Tests

```python
# Test 1: 4-level hierarchy
salesperson = env['res.users'].create({
    'name': 'John Doe',
    'login': 'john@test.com',
    'commission_role_id': role_salesperson.id,
    'commission_manager_id': team_leader.id
})

team_leader = env['res.users'].create({
    'name': 'Jane Manager',
    'login': 'jane@test.com',
    'commission_role_id': role_team_leader.id,
    'commission_manager_id': regional_manager.id
})

regional_manager = env['res.users'].create({
    'name': 'Bob Regional',
    'login': 'bob@test.com',
    'commission_role_id': role_regional_manager.id,
    'commission_manager_id': director.id
})

director = env['res.users'].create({
    'name': 'Alice Director',
    'login': 'alice@test.com',
    'commission_role_id': role_director.id,
    'commission_manager_id': False  # Top level
})

# Test 2: Verify hierarchy traversal
hierarchy = sale_order._get_commission_hierarchy(salesperson)
assert len(hierarchy) == 4
assert hierarchy[0][0] == salesperson
assert hierarchy[1][0] == team_leader
assert hierarchy[2][0] == regional_manager
assert hierarchy[3][0] == director
```

### 9.3 Commission Calculation Tests

```python
# Test 1: Commission generation for 4-level hierarchy
sale_order = env['sale.order'].create({...})
sale_order.action_confirm()
invoice = sale_order._create_invoices()
invoice.action_post()
# Mark as paid...

commissions = env['sale.commission'].search([('sale_order_id', '=', sale_order.id)])
assert len(commissions) == 4  # One for each level

# Test 2: Verify percentages
for comm in commissions:
    config = env['hr.commission.role.config'].search([
        ('plan_id', '=', comm.plan_id.id),
        ('role_id', '=', comm.role_id.id)
    ])
    assert comm.commission_percentage == config.default_percentage
```

### 9.4 Anomaly Detection Tests

```python
# Test 1: Missing manager
user = env['res.users'].create({
    'name': 'Test User',
    'commission_role_id': role_salesperson.id,  # Requires manager
    'commission_manager_id': False  # But none assigned
})
assert user.has_hierarchy_anomaly == True
assert user.anomaly_type == 'missing_manager'

# Test 2: Top role with manager
director = env['res.users'].create({
    'name': 'Test Director',
    'commission_role_id': role_director.id,  # Doesn't require manager
    'commission_manager_id': some_user.id  # But has one
})
assert director.has_hierarchy_anomaly == True
assert director.anomaly_type == 'top_role_has_manager'

# Test 3: Manager lower level than subordinate
subordinate = env['res.users'].create({
    'name': 'Subordinate',
    'commission_role_id': role_director.id,  # sequence=30
    'commission_manager_id': salesperson.id  # sequence=10 (lower!)
})
assert subordinate.has_hierarchy_anomaly == True
assert subordinate.anomaly_type == 'manager_lower_level'
```

---

## 10. Risk Assessment (Development Environment)

### 10.1 Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Commission calculation bugs | MEDIUM | Comprehensive testing with multiple scenarios |
| Circular hierarchy not detected | LOW | Built-in cycle detection in traversal |
| Performance issues with deep hierarchies | LOW | Depth limit (20 levels) and cycle detection |
| Missing role configurations | LOW | Validation on commission plan approval |
| UI confusion for users | LOW | Clear help text and tooltips |

### 10.2 What We Don't Need to Worry About

Since we're in development:
- ✅ No production data migration
- ✅ No backward compatibility required
- ✅ Can modify database schema freely
- ✅ Can change field names/types
- ✅ Can delete old fields immediately
- ✅ No user training until deployment

---

## 11. Files to Modify

### New Files
- `models/sale_commission_role.py` (new model)
- `views/sale_commission_role_views.xml` (new views)
- `data/sale_commission_role_data.xml` (default roles)

### Modified Files
- `models/res_users.py` - Replace role fields, update hierarchy logic
- `models/sale_commission.py` - Replace role field
- `models/hr_commission_role_config.py` - Replace role field
- `models/sale_order.py` - Update commission creation
- `models/account_move.py` - Update commission creation
- `views/res_users_views.xml` - Update form/tree views
- `views/team_management_views.xml` - Update hierarchy views
- `views/sale_commission_plan_views.xml` - Update role config
- `views/sale_commission_views.xml` - Update filters
- `security/ir.model.access.csv` - Add role model access
- `__manifest__.py` - Add new files

---

## 12. Estimated Timeline

| Phase | Duration | Details |
|-------|----------|---------|
| **Phase 1: Foundation** | 3 days | Create role model, views, security |
| **Phase 2: Model Updates** | 4 days | Update all models to use dynamic roles |
| **Phase 3: Logic Updates** | 5 days | Rewrite hierarchy traversal and anomaly detection |
| **Phase 4: View Updates** | 3 days | Update all XML views |
| **Phase 5: Testing** | 3 days | Create test data, run scenarios |
| **Phase 6: Documentation** | 2 days | User guides, developer notes |
| **Total** | **20 days** | ~4 weeks with 1 developer |

**Note:** This is a clean implementation timeline with no migration overhead.

---

## 13. Next Steps

### Immediate Actions

1. **Review & Approve Approach**
   - Confirm dynamic role model structure
   - Confirm single `commission_manager_id` field approach
   - Confirm anomaly detection logic

2. **Start Implementation**
   - Create `sale_commission_role.py` model
   - Add views and security
   - Load default role data
   - Test role management UI

3. **Iterative Development**
   - Complete one model at a time
   - Test after each change
   - Commit frequently

Would you like me to:
1. **Start implementing** the role model and views?
2. **Create a detailed migration script** for updating the models?
3. **Write test cases** for the new hierarchy logic?
4. **Something else**?
