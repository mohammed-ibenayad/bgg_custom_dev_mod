# Dynamic Roles Implementation Analysis
## Belgogreen Sales Commission Module

**Date:** December 5, 2025
**Objective:** Convert hardcoded 3-tier role system to dynamic, manager-configurable roles

---

## Executive Summary

The current system uses **3 hardcoded roles** (Salesperson, Team Leader, Sales Director) defined as Selection fields across multiple models. Converting to dynamic roles requires:

- Creating a new `sale.commission.role` master model
- Replacing all Selection fields with Many2one references
- Updating hierarchy logic to support N-level hierarchies
- Modifying commission calculation to work with dynamic roles
- Extensive data migration for existing records

**Estimated Complexity:** HIGH
**Risk Level:** MEDIUM-HIGH (affects core commission calculation logic)

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

### 1.3 Hierarchy Management

**Current Implementation:**
- Fixed 3-level hierarchy enforced in code
- Specific fields for each level:
  - `team_leader_id` → Points to users with role='team_leader'
  - `sales_director_id` → Points to users with role='sales_director'
- Domains hardcoded: `domain=[('commission_role', '=', 'team_leader')]`

**Commission Flow:**
```
Sale Order (Salesperson)
    ↓
Commission #1: Salesperson (role='salesperson')
Commission #2: Team Leader (team_leader_id, role='team_leader')
Commission #3: Sales Director (sales_director_id, role='sales_director')
```

---

## 2. Required Changes for Dynamic Roles

### 2.1 New Master Data Model

**Create: `sale.commission.role`**

```python
class SaleCommissionRole(models.Model):
    _name = 'sale.commission.role'
    _description = 'Commission Role'
    _order = 'sequence, name'

    name = fields.Char(string='Role Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, help='Unique identifier (e.g., SP, TL, SD)')
    sequence = fields.Integer(string='Hierarchy Level', default=10,
                              help='Lower numbers = bottom of hierarchy')
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    color = fields.Integer(string='Color', help='Color for kanban view')

    # Hierarchy configuration
    allow_subordinates = fields.Boolean(string='Can Have Subordinates', default=True)
    requires_manager = fields.Boolean(string='Requires Manager', default=True)
    is_top_level = fields.Boolean(string='Is Top Level', default=False,
                                   help='Top-level roles do not need a manager')

    _sql_constraints = [
        ('code_unique', 'unique(code, company_id)', 'Role code must be unique per company!'),
        ('name_unique', 'unique(name, company_id)', 'Role name must be unique per company!')
    ]
```

### 2.2 Model Field Changes

#### A. `res.users` (res_users.py)

**Current:**
```python
commission_role = fields.Selection([...], ...)
team_leader_id = fields.Many2one('res.users', domain=[('commission_role', '=', 'team_leader')])
sales_director_id = fields.Many2one('res.users', domain=[('commission_role', '=', 'sales_director')])
```

**Proposed:**
```python
# Replace Selection with Many2one
commission_role_id = fields.Many2one(
    'sale.commission.role',
    string='Commission Role',
    domain="[('company_id', '=', company_id)]"
)

# Replace hardcoded hierarchy with generic manager field
commission_manager_id = fields.Many2one(
    'res.users',
    string='Commission Manager',
    domain="[('commission_role_id', '!=', False), ('id', '!=', id)]",
    help='Direct manager in the commission hierarchy'
)

# Add computed/related fields for backward compatibility
commission_subordinate_ids = fields.One2many(
    'res.users',
    'commission_manager_id',
    string='Direct Subordinates'
)
```

**Impact:**
- 🔴 **BREAKING**: Removes `team_leader_id` and `sales_director_id`
- 🔴 Existing views showing these fields will break
- 🔴 Requires data migration

#### B. `hr.commission.role.config` (hr_commission_role_config.py)

**Current:**
```python
role = fields.Selection([...], required=True)
```

**Proposed:**
```python
role_id = fields.Many2one(
    'sale.commission.role',
    string='Role',
    required=True,
    domain="[('company_id', '=', company_id)]"
)

_sql_constraints = [
    ('unique_plan_role', 'unique(plan_id, role_id)',
     'Only one percentage per role per plan!')
]
```

**Impact:**
- 🔴 **BREAKING**: Changes SQL constraint
- 🟡 Requires data migration
- ✅ More flexible for new roles

#### C. `sale.commission` (sale_commission.py)

**Current:**
```python
role = fields.Selection([...], required=True, tracking=True)
```

**Proposed:**
```python
role_id = fields.Many2one(
    'sale.commission.role',
    string='Role',
    required=True,
    tracking=True
)
```

**Impact:**
- 🟡 Historical commission records need migration
- 🟡 Reports filtering by role need update
- ✅ Supports any future roles automatically

---

## 3. Commission Calculation Logic Changes

### 3.1 Current Hierarchical Commission Creation

**File:** `sale_order.py:145-161`

**Current Logic:**
```python
# Hardcoded 3-tier hierarchy traversal
users_to_commission = []

# 1. Salesperson
if salesperson.commission_role:
    users_to_commission.append((salesperson, 'salesperson'))

# 2. Team Leader (hardcoded field)
if salesperson.team_leader_id:
    users_to_commission.append((salesperson.team_leader_id, 'team_leader'))

# 3. Sales Director (hardcoded field)
if salesperson.sales_director_id:
    users_to_commission.append((salesperson.sales_director_id, 'sales_director'))
elif salesperson.team_leader_id and salesperson.team_leader_id.sales_director_id:
    users_to_commission.append((salesperson.team_leader_id.sales_director_id, 'sales_director'))
```

### 3.2 Proposed Dynamic Logic

```python
def _get_commission_hierarchy(self, salesperson):
    """
    Traverse hierarchy upwards to collect all managers who should receive commission
    Returns: [(user, role_id), ...]
    """
    users_to_commission = []
    current_user = salesperson
    processed_ids = set()  # Prevent infinite loops

    while current_user and current_user.id not in processed_ids:
        if current_user.commission_role_id:
            users_to_commission.append((current_user, current_user.commission_role_id))
            processed_ids.add(current_user.id)

        # Move up the hierarchy
        current_user = current_user.commission_manager_id

    return users_to_commission

# Usage in _create_commissions_for_invoice
users_to_commission = self._get_commission_hierarchy(salesperson)

for user, role_id in users_to_commission:
    # Create commission with role_id instead of role
    self.env['sale.commission'].create({
        'user_id': user.id,
        'role_id': role_id.id,  # Changed from 'role': role
        # ... rest of fields
    })
```

**Benefits:**
- ✅ Supports N-level hierarchies automatically
- ✅ No code changes needed when adding new roles
- ✅ Cycle detection built-in
- ⚠️ Requires thorough testing for edge cases

---

## 4. Anomaly Detection Changes

### 4.1 Current Anomaly Types

**File:** `res_users.py:122-128`

```python
anomaly_type = fields.Selection([
    ('salesperson_no_team_leader', ...),      # Hardcoded role check
    ('salesperson_bypass_team_leader', ...),  # Hardcoded role check
    ('team_leader_no_director', ...),         # Hardcoded role check
    ('director_has_manager', ...),            # Hardcoded role check
    ('no_role_with_assignments', ...),
])
```

### 4.2 Proposed Generic Anomaly Detection

```python
anomaly_type = fields.Selection([
    ('missing_manager', 'Missing Required Manager'),
    ('has_manager_top_level', 'Top-level role should not have manager'),
    ('no_role_with_manager', 'No role assigned but has manager'),
    ('circular_hierarchy', 'Circular reference in hierarchy'),
], ...)

@api.depends('commission_role_id', 'commission_manager_id')
def _compute_hierarchy_anomalies(self):
    for user in self:
        anomaly = False
        anomaly_type = False
        description = ''

        if user.commission_role_id:
            # Check if role requires manager but user has none
            if user.commission_role_id.requires_manager and not user.commission_manager_id:
                anomaly = True
                anomaly_type = 'missing_manager'
                description = _("User with role '%s' requires a manager but none is assigned") % user.commission_role_id.name

            # Check if top-level role has a manager assigned
            if user.commission_role_id.is_top_level and user.commission_manager_id:
                anomaly = True
                anomaly_type = 'has_manager_top_level'
                description = _("User with top-level role '%s' should not have a manager") % user.commission_role_id.name

        # Check for role assignment without manager field
        elif not user.commission_role_id and user.commission_manager_id:
            anomaly = True
            anomaly_type = 'no_role_with_manager'
            description = _("User has manager assigned but no commission role defined")

        user.has_hierarchy_anomaly = anomaly
        user.anomaly_type = anomaly_type
        user.anomaly_description = description
```

**Benefits:**
- ✅ Generic rules work for any role configuration
- ✅ Role-specific rules defined in role master data
- ⚠️ May need custom validation rules for specific business needs

---

## 5. View and UI Changes

### 5.1 Forms Requiring Updates

| View File | Elements to Change | Complexity |
|-----------|-------------------|------------|
| `res_users_views.xml` | commission_role field → commission_role_id | LOW |
| `res_users_views.xml` | team_leader_id, sales_director_id → commission_manager_id | MEDIUM |
| `sale_commission_plan_views.xml` | Role percentages tab tree view | LOW |
| `sale_commission_views.xml` | Role filters and grouping | LOW |
| `team_management_views.xml` | Hierarchy views (kanban/tree) | HIGH |
| `team_management_views.xml` | Role-specific filters | MEDIUM |

### 5.2 Critical View Changes

#### A. User Form - Commission Hierarchy Tab

**Current:** Shows separate fields for team_leader_id and sales_director_id

**Proposed:**
```xml
<group name="hierarchy" string="Commission Hierarchy">
    <field name="commission_role_id"
           options="{'no_create': True}"/>
    <field name="commission_manager_id"
           domain="[('commission_role_id.sequence', '>', commission_role_id.sequence), ('id', '!=', id)]"
           context="{'show_commission_role': True}"/>
    <field name="commission_subordinate_ids" widget="many2many_tags" readonly="1"/>
</group>
```

#### B. Team Management Views

**Current:** Separate tree views for each role level

**Proposed:** Unified tree view with dynamic grouping by role

```xml
<tree string="Team Hierarchy"
      decoration-info="commission_role_id.sequence == 1"
      decoration-warning="commission_role_id.sequence == 2"
      decoration-success="commission_role_id.sequence == 3">
    <field name="name"/>
    <field name="commission_role_id"/>
    <field name="commission_manager_id"/>
    <field name="subordinate_count"/>
</tree>
```

### 5.3 New Configuration Menu

Add menu item for Sales Managers to manage roles:

```
Configuration > Commission Roles
```

Form view for `sale.commission.role`:
- Name, Code, Sequence
- Hierarchy settings (allow_subordinates, requires_manager, is_top_level)
- Active users count with this role
- Active commissions count with this role

---

## 6. Impact Assessment

### 6.1 Database Schema Changes

| Model | Field Changes | Type | Risk |
|-------|--------------|------|------|
| `res.users` | Add `commission_role_id` M2o | New field | LOW |
| `res.users` | Add `commission_manager_id` M2o | New field | LOW |
| `res.users` | Remove `commission_role` Selection | Breaking | HIGH |
| `res.users` | Remove `team_leader_id` M2o | Breaking | HIGH |
| `res.users` | Remove `sales_director_id` M2o | Breaking | HIGH |
| `sale.commission` | Add `role_id` M2o | New field | LOW |
| `sale.commission` | Remove `role` Selection | Breaking | HIGH |
| `hr.commission.role.config` | Add `role_id` M2o | New field | LOW |
| `hr.commission.role.config` | Remove `role` Selection | Breaking | MEDIUM |

### 6.2 Data Migration Requirements

#### Phase 1: Create Role Master Data
```python
def migrate_create_roles(cr):
    """Create default roles matching old selection values"""
    roles = [
        ('salesperson', 'Salesperson', 10, False),      # sequence=10, not top level
        ('team_leader', 'Team Leader', 20, False),      # sequence=20, not top level
        ('sales_director', 'Sales Director', 30, True), # sequence=30, IS top level
    ]

    for code, name, sequence, is_top_level in roles:
        cr.execute("""
            INSERT INTO sale_commission_role (code, name, sequence, is_top_level,
                                               allow_subordinates, requires_manager,
                                               active, create_date, write_date)
            VALUES (%s, %s, %s, %s, TRUE, %s, TRUE, NOW(), NOW())
        """, (code, name, sequence, is_top_level, not is_top_level))
```

#### Phase 2: Migrate User Roles
```python
def migrate_user_roles(cr):
    """Migrate res.users commission_role Selection to commission_role_id M2o"""

    # Map old selection values to new role IDs
    cr.execute("""
        UPDATE res_users u
        SET commission_role_id = r.id
        FROM sale_commission_role r
        WHERE u.commission_role = r.code
          AND u.commission_role IS NOT NULL
    """)
```

#### Phase 3: Migrate User Hierarchy
```python
def migrate_user_hierarchy(cr):
    """Convert team_leader_id/sales_director_id to commission_manager_id"""

    # For salespeople: manager = team_leader_id (if exists) else sales_director_id
    cr.execute("""
        UPDATE res_users
        SET commission_manager_id = COALESCE(team_leader_id, sales_director_id)
        WHERE commission_role = 'salesperson'
    """)

    # For team leaders: manager = sales_director_id
    cr.execute("""
        UPDATE res_users
        SET commission_manager_id = sales_director_id
        WHERE commission_role = 'team_leader'
          AND sales_director_id IS NOT NULL
    """)

    # Sales directors have no manager (top level)
```

#### Phase 4: Migrate Commission Records
```python
def migrate_commission_roles(cr):
    """Migrate sale.commission role Selection to role_id M2o"""
    cr.execute("""
        UPDATE sale_commission c
        SET role_id = r.id
        FROM sale_commission_role r
        WHERE c.role = r.code
    """)
```

#### Phase 5: Migrate Role Configurations
```python
def migrate_role_configs(cr):
    """Migrate hr.commission.role.config"""
    cr.execute("""
        UPDATE hr_commission_role_config c
        SET role_id = r.id
        FROM sale_commission_role r
        WHERE c.role = r.code
    """)
```

### 6.3 Affected Business Logic

| Component | Location | Change Required | Complexity |
|-----------|----------|----------------|------------|
| Commission calculation | `sale_order.py:145-161` | Rewrite hierarchy traversal | HIGH |
| Commission calculation | `account_move.py:85-96` | Rewrite hierarchy traversal | HIGH |
| Anomaly detection | `res_users.py:279-340` | Rewrite all checks | HIGH |
| Role validation | `res_users.py:400-485` | Adapt to dynamic roles | MEDIUM |
| Subordinate retrieval | `res_users.py:162-196` | Simplify with generic field | MEDIUM |
| Hierarchy warnings | `res_users.py:250-277` | Rewrite all checks | MEDIUM |
| Record rules | `commission_security.xml` | Should work as-is | LOW |

---

## 7. Potential Blockers

### 7.1 Technical Blockers

#### 🔴 **CRITICAL: Data Migration Complexity**

**Issue:** Complex hierarchy mapping with edge cases
- What if salesperson has both team_leader_id AND sales_director_id? (bypass scenario)
- How to handle orphaned records?
- What if multiple people have conflicting hierarchy assignments?

**Solution:**
- Run pre-migration audit to identify all edge cases
- Create migration log table to track decisions
- Provide manual resolution UI for conflicts

#### 🔴 **CRITICAL: Commission Calculation Changes**

**Issue:** Core algorithm rewrite affects money calculations
- Any bugs could result in incorrect commission payments
- Need extensive testing with real data

**Solution:**
- Run parallel calculations (old vs new) for validation period
- Create comprehensive test cases covering all scenarios
- QA sign-off required before production

#### 🟡 **MEDIUM: View/Report Updates**

**Issue:** Many views filter/group by hardcoded role values
- Existing reports may break
- Custom filters in saved searches become invalid

**Solution:**
- Audit all XML views and update domains
- Provide migration script for user-saved filters
- Update documentation for report changes

#### 🟡 **MEDIUM: Backward Compatibility**

**Issue:** External integrations or customizations may reference old fields
- API calls using `commission_role` field
- Custom modules depending on `team_leader_id`/`sales_director_id`

**Solution:**
- Provide computed fields for backward compatibility
- Add deprecation warnings
- Document migration guide for customizations

### 7.2 Business Blockers

#### 🟡 **MEDIUM: Manager Training**

**Issue:** Sales managers need to understand new role management system
- How to create new roles
- How to set role hierarchy levels (sequence)
- Understanding role configuration options

**Solution:**
- Create user documentation with screenshots
- Provide training sessions
- Set up example role configurations

#### 🟡 **MEDIUM: Role Design Decisions**

**Issue:** Need to define business rules for dynamic roles
- Can roles be deleted if commissions exist?
- Can role sequence be changed after commissions are generated?
- What happens to existing commissions if role is deactivated?

**Solution:**
- Define clear business rules document
- Implement validation constraints in code
- Add warning messages for dangerous operations

#### 🟢 **LOW: Performance Impact**

**Issue:** Dynamic hierarchy traversal may be slower than hardcoded logic

**Solution:**
- Add indexes on new M2o fields
- Consider caching hierarchy paths
- Performance testing before go-live

---

## 8. Recommended Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Create `sale.commission.role` model
- [ ] Add views and security rules for role management
- [ ] Create default roles (Salesperson, Team Leader, Sales Director)
- [ ] Add new fields to models (keep old fields for compatibility)

### Phase 2: Logic Adaptation (Week 3-4)
- [ ] Rewrite `_get_commission_hierarchy()` method
- [ ] Update commission calculation logic to use new fields
- [ ] Adapt anomaly detection to use role configuration
- [ ] Update validation logic

### Phase 3: UI Updates (Week 5)
- [ ] Update all XML views to show new fields
- [ ] Create role configuration menu for managers
- [ ] Update team management views
- [ ] Update filters and search views

### Phase 4: Testing & Migration (Week 6-7)
- [ ] Create comprehensive test dataset
- [ ] Write and test migration scripts
- [ ] Run parallel calculation validation
- [ ] QA testing of all scenarios
- [ ] User acceptance testing

### Phase 5: Deployment (Week 8)
- [ ] Backup production database
- [ ] Run migration scripts
- [ ] Verify data integrity
- [ ] Remove deprecated fields after grace period
- [ ] Monitor for issues

---

## 9. Alternative Approaches

### Option A: Hybrid Approach (Recommended)
**Keep hardcoded roles but make them configurable**

- Keep 3-tier structure as default
- Allow managers to configure role names and percentages
- Maintain hardcoded fields but make labels dynamic
- Add ability to "activate" 4th or 5th tier if needed

**Pros:**
- ✅ Less risky - minimal code changes
- ✅ Faster implementation
- ✅ No complex data migration
- ✅ Existing logic mostly preserved

**Cons:**
- ⚠️ Still limited to predefined number of levels
- ⚠️ Not truly "dynamic"

### Option B: Full Dynamic System (High Effort)
**Complete rewrite as described in this document**

**Pros:**
- ✅ Unlimited flexibility
- ✅ No code changes needed for new roles
- ✅ Future-proof solution

**Cons:**
- ❌ High implementation cost
- ❌ High risk of bugs
- ❌ Complex migration

### Option C: Phased Hybrid Approach (Balanced)
**Start with Option A, migrate to Option B over time**

1. Phase 1: Make current 3 roles configurable (names, percentages)
2. Phase 2: Add optional 4th "Regional Manager" role
3. Phase 3: Generalize to fully dynamic system

**Pros:**
- ✅ Delivers value quickly
- ✅ Lower risk per phase
- ✅ Can pause if issues arise

**Cons:**
- ⚠️ Requires two migration efforts
- ⚠️ Longer total timeline

---

## 10. Recommendations

### Recommended Approach: **Option C - Phased Hybrid**

**Rationale:**
1. **Quick wins:** Sales managers can customize role names/labels immediately
2. **Lower risk:** Smaller changes per phase = easier testing
3. **Flexible:** Can stop at any phase if business needs are met
4. **Proven pattern:** Incremental refactoring reduces big-bang risk

### Immediate Next Steps

1. **Week 1: Requirements Gathering**
   - Interview sales managers about desired roles
   - Document current hierarchy anomalies
   - Identify must-have vs nice-to-have features

2. **Week 2: Technical Design**
   - Detail Phase 1 implementation (configurable 3-tier)
   - Create database migration plan
   - Set up test environment with production data copy

3. **Week 3-4: Phase 1 Implementation**
   - Create basic role master model
   - Add configuration UI
   - Keep all existing fields/logic intact

4. **Week 5: Testing & Validation**
   - User acceptance testing
   - Performance testing
   - Edge case validation

5. **Week 6: Phase 1 Deployment**
   - Deploy to production
   - Monitor for issues
   - Gather feedback

6. **Decide on Phase 2/3 based on feedback**

---

## 11. Risk Mitigation Strategies

### Data Integrity
- ✅ Run migration in transaction with rollback capability
- ✅ Create backup before migration
- ✅ Validate data after each migration step
- ✅ Keep old fields for 1-2 months as backup

### Commission Accuracy
- ✅ Run parallel calculations for 1 month (old + new logic)
- ✅ Alert if discrepancies found
- ✅ Manual review of first month's commissions
- ✅ Easy rollback procedure documented

### User Adoption
- ✅ Training materials and videos
- ✅ In-app help text and tooltips
- ✅ Gradual rollout (pilot team first)
- ✅ Dedicated support during transition

---

## 12. Success Metrics

### Technical Metrics
- Zero data loss during migration
- < 5% performance degradation in commission calculation
- Zero critical bugs in first month
- All automated tests passing

### Business Metrics
- Sales managers can create new role within 5 minutes
- 100% of existing commissions migrated correctly
- No incorrect commission payments
- Positive feedback from pilot users

---

## Appendices

### Appendix A: Files Requiring Changes

**High Priority (Core Logic):**
- `models/res_users.py` (486 lines) - Major refactoring
- `models/sale_order.py` (286 lines) - Commission creation logic
- `models/account_move.py` - Commission creation logic
- `models/sale_commission.py` (253 lines) - Role field changes
- `models/hr_commission_role_config.py` (70 lines) - Role field changes

**Medium Priority (Views):**
- `views/res_users_views.xml` - Form updates
- `views/team_management_views.xml` - Hierarchy views
- `views/sale_commission_plan_views.xml` - Role config tab
- `views/sale_commission_views.xml` - Filters

**Low Priority (Supporting):**
- `security/commission_security.xml` - May need review
- `data/cron_data.xml` - Should work as-is
- Various wizard/report files - Minor updates

### Appendix B: Test Scenarios Required

1. **Single-level commission** (just salesperson)
2. **Two-level commission** (salesperson + manager)
3. **Three-level commission** (full hierarchy)
4. **Four-level commission** (with new role)
5. **Orphaned salesperson** (no manager)
6. **Role change mid-period**
7. **Manager change mid-period**
8. **Circular hierarchy** (should be prevented)
9. **Duplicate role assignment** (should be prevented)
10. **Commission recalculation** after role changes

### Appendix C: Estimated Effort

| Phase | Tasks | Effort (Days) | Resources |
|-------|-------|---------------|-----------|
| Analysis | Requirements, Design | 5 | 1 Dev + 1 BA |
| Development | Coding, Unit Tests | 20 | 2 Devs |
| Testing | QA, UAT | 10 | 1 QA + Users |
| Migration | Scripts, Validation | 5 | 1 Dev |
| Deployment | Deploy, Monitor | 3 | 1 Dev + 1 Ops |
| **Total** | | **43 days** | |

**Note:** This is for Option C Phase 1 only. Full implementation would be 2-3x this estimate.

---

## Conclusion

Converting to dynamic roles is **technically feasible** but requires **significant effort** and carries **moderate risk**. The **phased hybrid approach (Option C)** provides the best balance of value delivery, risk management, and flexibility.

**Key Success Factors:**
1. ✅ Comprehensive testing with production-like data
2. ✅ Parallel validation of old vs new calculations
3. ✅ Clear rollback procedure
4. ✅ User training and documentation
5. ✅ Gradual rollout with monitoring

**Recommendation:** Proceed with **Phase 1 (Configurable 3-tier)** to deliver immediate value while minimizing risk. Evaluate need for full dynamic system after Phase 1 feedback.
