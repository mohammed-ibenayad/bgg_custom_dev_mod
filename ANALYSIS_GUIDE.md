# Commission Models Analysis Guide

This guide helps you analyze and extract data from commission-related models in your Odoo database.

## 📁 Available Scripts

### 1. `analyze_commission_models.py` - Full Model Analysis
Complete analysis of all commission models with field details and categorization.

**Features:**
- Analyzes all 14 commission-related models
- Shows field types, relationships, and properties
- Categorizes fields (basic, relational, computed, functional)
- Displays sample records
- Exports detailed field information to text files
- Identifies which models are relevant to hierarchical development

**Run in Odoo Shell:**
```bash
./odoo-bin shell -d your_database
>>> exec(open('analyze_commission_models.py').read())
```

**Output:**
- Console analysis with formatted sections
- Text files exported to `/tmp/` for each hierarchical model

---

### 2. `extract_hierarchical_data.py` - Quick Data Extraction
Focused extraction of data from hierarchical commission models.

**Features:**
- Extracts hierarchical commission plans
- Shows role configurations with percentages
- Displays recent commissions with amounts
- Lists commission payments and claims
- Shows user hierarchy (salesperson → team leader → director)
- Provides statistics summary
- Includes helper functions for JSON export

**Run in Odoo Shell:**
```bash
./odoo-bin shell -d your_database
>>> exec(open('extract_hierarchical_data.py').read())
```

**Helper Functions Available After Running:**
```python
# Export unpaid commissions to JSON
export_to_json('sale.commission', [('payment_status', '=', 'unpaid')], '/tmp/unpaid_commissions.json')

# Export all hierarchical plans
export_to_json('sale.commission.plan', [('type', '=', 'hierarchical')], '/tmp/hierarchical_plans.json')

# Export role configurations
export_to_json('hr.commission.role.config', [], '/tmp/role_configs.json')
```

---

## 🏗️ Commission Model Categories

### **Hierarchical Commission Models (Our Custom Development)**

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `sale.commission` | Store individual commission records | user_id, role, commission_amount, payment_status |
| `sale.commission.plan` | Commission plans (extended with 'hierarchical' type) | type, periodicity, require_invoice_paid, role_config_ids |
| `sale.commission.payment` | Payment batch processing | user_id, commission_ids, total_amount, state |
| `sale.commission.claim` | User commission claims | user_id, commission_ids, total_amount, state |
| `hr.commission.role.config` | Role-based percentage configuration | plan_id, role, default_percentage |

### **Base Commission Models (Original Odoo - Reference Only)**

These models are from the base `sale_commission` module and are used for achievement/target-based commissions. **We don't directly use these**, but they coexist with our hierarchical system.

| Model | Purpose |
|-------|---------|
| `sale.commission.plan.user` | User assignment to commission plans |
| `sale.commission.plan.user.wizard` | Wizard for bulk user assignment |
| `sale.commission.plan.target` | Sales targets for commission calculation |
| `sale.commission.plan.target.commission` | Commission rates per target tier |
| `sale.commission.plan.target.forecast` | Target forecasting |
| `sale.commission.plan.achievement` | Achievement-based commission config |
| `sale.commission.achievement` | Manual achievement entries |
| `sale.commission.achievement.report` | Achievement reporting |
| `sale.commission.report` | General commission reports |

---

## 🔍 Key Relationships

```
Hierarchical Commission Flow:
└── sale.commission.plan (type='hierarchical')
    └── hr.commission.role.config (role percentages)
        ├── Salesperson: 5%
        ├── Team Leader: 3%
        └── Sales Director: 2%
            └── sale.commission (generated commissions)
                ├── sale.commission.claim (user claims payment)
                └── sale.commission.payment (manager processes payment)
```

---

## 📊 Critical Fields Reference

### `sale.commission.plan`
- **`type`**: 'target', 'achievement', or 'hierarchical' (we added this)
- **`periodicity`**: 'monthly', 'quarterly', 'yearly', or 'not_applicable' (we added this)
- **`require_invoice_paid`**: Boolean - only generate commissions when invoice is paid
- **`is_hierarchical`**: Computed field (True when type='hierarchical')
- **`role_config_ids`**: One2many to hr.commission.role.config

### `sale.commission`
- **`role`**: 'salesperson', 'team_leader', or 'sales_director'
- **`base_amount`**: Amount on which commission is calculated
- **`commission_percentage`**: Effective percentage applied
- **`commission_amount`**: Calculated commission amount
- **`payment_status`**: 'unpaid', 'claimed', 'processing', 'paid', 'cancelled'
- **`state`**: 'draft', 'confirmed', 'cancelled'
- **`can_be_paid`**: Computed - True if invoice paid and commission unpaid

### `hr.commission.role.config`
- **`plan_id`**: Many2one to sale.commission.plan
- **`role`**: 'salesperson', 'team_leader', or 'sales_director'
- **`default_percentage`**: Float - default percentage for this role

---

## 🎯 Common Queries

### Get all hierarchical plans:
```python
plans = env['sale.commission.plan'].search([('type', '=', 'hierarchical')])
```

### Get unpaid commissions:
```python
unpaid = env['sale.commission'].search([('payment_status', '=', 'unpaid')])
```

### Get commissions for a specific user:
```python
user = env['res.users'].search([('login', '=', 'username')], limit=1)
commissions = env['sale.commission'].search([('user_id', '=', user.id)])
```

### Get role configurations for a plan:
```python
plan = env['sale.commission.plan'].browse(PLAN_ID)
configs = plan.role_config_ids
for config in configs:
    print(f"{config.role}: {config.default_percentage}%")
```

### Get commission statistics by role:
```python
for role in ['salesperson', 'team_leader', 'sales_director']:
    commissions = env['sale.commission'].search([('role', '=', role)])
    total = sum(c.commission_amount for c in commissions)
    print(f"{role}: {len(commissions)} commissions, Total: {total}")
```

### Get user hierarchy:
```python
user = env['res.users'].browse(USER_ID)
print(f"User: {user.name}")
print(f"Role: {user.commission_role}")
if user.team_leader_id:
    print(f"Team Leader: {user.team_leader_id.name}")
if user.sales_director_id:
    print(f"Sales Director: {user.sales_director_id.name}")
```

---

## 📈 Export Examples

### Export all data to JSON files:
```python
# Run the extract script first
exec(open('extract_hierarchical_data.py').read())

# Then use the export function
export_to_json('sale.commission.plan', [('type', '=', 'hierarchical')], '/tmp/plans.json')
export_to_json('hr.commission.role.config', [], '/tmp/roles.json')
export_to_json('sale.commission', [('state', '=', 'confirmed')], '/tmp/commissions.json')
```

### Manual export using ORM:
```python
import json

# Get data
plans = env['sale.commission.plan'].search([('type', '=', 'hierarchical')])

# Format for export
data = []
for plan in plans:
    data.append({
        'id': plan.id,
        'name': plan.name,
        'type': plan.type,
        'require_invoice_paid': plan.require_invoice_paid,
        'roles': [{
            'role': c.role,
            'percentage': c.default_percentage
        } for c in plan.role_config_ids]
    })

# Export
with open('/tmp/my_plans.json', 'w') as f:
    json.dump(data, f, indent=2)
```

---

## 🚀 Quick Start

**Step 1:** Start Odoo shell
```bash
cd /path/to/odoo
./odoo-bin shell -d your_database --addons-path=/path/to/addons
```

**Step 2:** Run the extraction script
```python
>>> exec(open('/path/to/extract_hierarchical_data.py').read())
```

**Step 3:** Review the output and use helper functions as needed

**Step 4:** For detailed analysis, run the full analysis script
```python
>>> exec(open('/path/to/analyze_commission_models.py').read())
```

---

## 📝 Notes

- **Demo Data**: The `demo/demo.xml` file has been cleared to avoid installation errors. Use `create_demo_data.py` to create demo data programmatically if needed.

- **Model Isolation**: Our hierarchical commission models are properly isolated from the base achievement/target models. The `_compute_targets()` method filters out hierarchical plans to prevent interference.

- **Field Access**: All fields are accessed via ORM. Some computed fields may not be available in all contexts.

- **Performance**: When exporting large datasets, use `limit` parameter or add specific domain filters.

---

## 🛠️ Troubleshooting

**Issue:** "Model does not exist"
- **Solution:** Check if the module is installed: `env['ir.module.module'].search([('name', '=', 'belgogreen_sales_commission')])`

**Issue:** "Field does not exist"
- **Solution:** The field might be computed and not stored. Check `analyze_commission_models.py` output.

**Issue:** Access denied
- **Solution:** Run the shell with admin rights or use `env(su=True)` for specific operations.

---

## 📚 Additional Resources

- Module README: `README.md`
- Demo Data Setup: `README_DEMO_DATA.md`
- Demo Data Script: `create_demo_data.py`
- Model Files: `belgogreen_sales_commission/models/`
- View Files: `belgogreen_sales_commission/views/`
