# Demo Data Setup Guide

This guide explains how to create demo data for testing the Belgogreen Sales Commission module.

## Quick Start

### Method 1: Using Odoo Shell (Recommended for Development)

```bash
# Navigate to your Odoo directory
cd /path/to/odoo

# Run the script using Odoo shell
./odoo-bin shell -d your_database --addons-path=/path/to/addons < /path/to/belgogreen_sales_commission_mod/create_demo_data.py
```

### Method 2: Interactive Odoo Shell

```bash
# Start Odoo shell
./odoo-bin shell -d your_database --addons-path=/path/to/addons

# In the shell, run:
>>> exec(open('/path/to/belgogreen_sales_commission_mod/create_demo_data.py').read())
```

### Method 3: Copy-Paste Method

1. Start Odoo shell:
   ```bash
   ./odoo-bin shell -d your_database --addons-path=/path/to/addons
   ```

2. Copy the entire content of `create_demo_data.py` and paste it into the shell

## What Gets Created

### 👥 Users Hierarchy (9 users total)

**Sales Director (1):**
- Robert Johnson
  - Login: `director.demo`
  - Password: `demo`

**Team Leaders (2):**
- Mary Wilson - North TL
  - Login: `teamleader.north`
  - Password: `demo`
- Sarah Martinez - South TL
  - Login: `teamleader.south`
  - Password: `demo`

**Salespeople - North Team (3):**
- John Anderson - Login: `salesperson.north.1`
- Emily Thompson - Login: `salesperson.north.2`
- Michael Brown - Login: `salesperson.north.3`

**Salespeople - South Team (3):**
- Jennifer Davis - Login: `salesperson.south.1`
- David Garcia - Login: `salesperson.south.2`
- Lisa Rodriguez - Login: `salesperson.south.3`

All passwords: `demo`

### 📊 Commission Plans (2)

**North Team Commission Plan:**
- Hierarchical: ✅ Yes
- Require Paid Invoice: ✅ Yes
- Salesperson: 5%
- Team Leader: 3%
- Sales Director: 2%

**South Team Commission Plan:**
- Hierarchical: ✅ Yes
- Require Paid Invoice: ✅ Yes
- Salesperson: 6%
- Team Leader: 2.5%
- Sales Director: 1.5%

## Testing the Commission System

After creating the demo data, you can test the system:

### 1. Login as a Salesperson
```
Username: salesperson.north.1
Password: demo
```

### 2. Create a Sales Order
- Go to Sales → Orders → Quotations
- Create a new quotation
- Add products
- Confirm the sale

### 3. View Hierarchy
- Go to Settings → Users & Companies → Users
- Open any user profile
- Go to "Commission Hierarchy" tab
- Verify the relationships

### 4. Test Commission Generation
- Create an invoice from the sales order
- Post the invoice
- Register payment
- Go to Commissions menu
- Verify commissions were created for all 3 levels

### 5. View Team Members
- Login as `teamleader.north`
- Go to Settings → Users → Open Mary Wilson's profile
- Go to "Commission Hierarchy" tab
- See the 3 North team salespeople listed

## Idempotent Script

The script is **safe to run multiple times**. It will:
- ✅ Check if data already exists
- ✅ Skip creation if found
- ✅ Update role configurations if commission plans exist
- ✅ Never create duplicates

## Troubleshooting

### Issue: "env is not defined"
**Solution:** You must run this script inside Odoo shell, not regular Python

### Issue: "Module not installed"
**Solution:** First install the module:
```bash
./odoo-bin -d your_database -i belgogreen_sales_commission --addons-path=/path/to/addons
```

### Issue: "Access Denied"
**Solution:** Make sure you have admin rights in the database

## Clean Up Demo Data

To remove demo data:

```python
# In Odoo shell
ResUsers = env['res.users']
CommissionPlan = env['sale.commission.plan']

# Delete demo users
demo_logins = [
    'director.demo', 'teamleader.north', 'teamleader.south',
    'salesperson.north.1', 'salesperson.north.2', 'salesperson.north.3',
    'salesperson.south.1', 'salesperson.south.2', 'salesperson.south.3'
]
ResUsers.search([('login', 'in', demo_logins)]).unlink()

# Delete demo commission plans
CommissionPlan.search([('name', 'in', ['North Team Commission Plan', 'South Team Commission Plan'])]).unlink()

env.cr.commit()
```

## Next Steps

After creating demo data:
1. Explore the commission hierarchy in user profiles
2. Create test sales orders
3. Generate commissions
4. Test the commission claim and payment workflow
5. Review commission reports

For more information, see the module documentation.
