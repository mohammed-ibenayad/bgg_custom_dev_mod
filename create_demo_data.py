#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Data Creation Script for Belgogreen Sales Commission Module

Usage:
    odoo-bin shell -d your_database --addons-path=/path/to/addons < create_demo_data.py

Or interactively:
    odoo-bin shell -d your_database --addons-path=/path/to/addons
    >>> exec(open('create_demo_data.py').read())
"""

print("\n" + "="*70)
print("Creating Demo Data for Belgogreen Sales Commission Module")
print("="*70 + "\n")

# Get environment and models
ResUsers = env['res.users']
CommissionPlan = env['sale.commission.plan']
RoleConfig = env['hr.commission.role.config']

# ============================================
# STEP 1: Create Sales Director
# ============================================
print("Step 1: Creating Sales Director...")

director = ResUsers.search([('login', '=', 'director.demo')], limit=1)
if director:
    print(f"  ✓ Sales Director already exists: {director.name}")
else:
    director = ResUsers.create({
        'name': 'Robert Johnson',
        'login': 'director.demo',
        'password': 'demo',
        'commission_role': 'sales_director',
        'groups_id': [(4, env.ref('sales_team.group_sale_salesman').id)],
    })
    print(f"  ✓ Created Sales Director: {director.name}")

# ============================================
# STEP 2: Create Team Leaders
# ============================================
print("\nStep 2: Creating Team Leaders...")

# Team Leader - North
tl_north = ResUsers.search([('login', '=', 'teamleader.north')], limit=1)
if tl_north:
    print(f"  ✓ North Team Leader already exists: {tl_north.name}")
else:
    tl_north = ResUsers.create({
        'name': 'Mary Wilson - North TL',
        'login': 'teamleader.north',
        'password': 'demo',
        'commission_role': 'team_leader',
        'sales_director_id': director.id,
        'groups_id': [(4, env.ref('sales_team.group_sale_salesman').id)],
    })
    print(f"  ✓ Created North Team Leader: {tl_north.name}")

# Team Leader - South
tl_south = ResUsers.search([('login', '=', 'teamleader.south')], limit=1)
if tl_south:
    print(f"  ✓ South Team Leader already exists: {tl_south.name}")
else:
    tl_south = ResUsers.create({
        'name': 'Sarah Martinez - South TL',
        'login': 'teamleader.south',
        'password': 'demo',
        'commission_role': 'team_leader',
        'sales_director_id': director.id,
        'groups_id': [(4, env.ref('sales_team.group_sale_salesman').id)],
    })
    print(f"  ✓ Created South Team Leader: {tl_south.name}")

# ============================================
# STEP 3: Create Salespeople - North Team
# ============================================
print("\nStep 3: Creating Salespeople - North Team...")

north_salespeople = [
    {'name': 'John Anderson - North SP', 'login': 'salesperson.north.1'},
    {'name': 'Emily Thompson - North SP', 'login': 'salesperson.north.2'},
    {'name': 'Michael Brown - North SP', 'login': 'salesperson.north.3'},
]

north_sp_records = []
for sp_data in north_salespeople:
    sp = ResUsers.search([('login', '=', sp_data['login'])], limit=1)
    if sp:
        print(f"  ✓ Salesperson already exists: {sp.name}")
        north_sp_records.append(sp)
    else:
        sp = ResUsers.create({
            'name': sp_data['name'],
            'login': sp_data['login'],
            'password': 'demo',
            'commission_role': 'salesperson',
            'team_leader_id': tl_north.id,
            'sales_director_id': director.id,
            'groups_id': [(4, env.ref('sales_team.group_sale_salesman').id)],
        })
        print(f"  ✓ Created Salesperson: {sp.name}")
        north_sp_records.append(sp)

# ============================================
# STEP 4: Create Salespeople - South Team
# ============================================
print("\nStep 4: Creating Salespeople - South Team...")

south_salespeople = [
    {'name': 'Jennifer Davis - South SP', 'login': 'salesperson.south.1'},
    {'name': 'David Garcia - South SP', 'login': 'salesperson.south.2'},
    {'name': 'Lisa Rodriguez - South SP', 'login': 'salesperson.south.3'},
]

south_sp_records = []
for sp_data in south_salespeople:
    sp = ResUsers.search([('login', '=', sp_data['login'])], limit=1)
    if sp:
        print(f"  ✓ Salesperson already exists: {sp.name}")
        south_sp_records.append(sp)
    else:
        sp = ResUsers.create({
            'name': sp_data['name'],
            'login': sp_data['login'],
            'password': 'demo',
            'commission_role': 'salesperson',
            'team_leader_id': tl_south.id,
            'sales_director_id': director.id,
            'groups_id': [(4, env.ref('sales_team.group_sale_salesman').id)],
        })
        print(f"  ✓ Created Salesperson: {sp.name}")
        south_sp_records.append(sp)

# ============================================
# STEP 5: Create Commission Plan - North Team
# ============================================
print("\nStep 5: Creating Commission Plan - North Team...")

plan_north = CommissionPlan.search([('name', '=', 'North Team Commission Plan')], limit=1)
if plan_north:
    print(f"  ✓ North Team Commission Plan already exists")
    # Clean up existing role configs
    plan_north.role_config_ids.unlink()
else:
    plan_north = CommissionPlan.create({
        'name': 'North Team Commission Plan',
        'is_hierarchical': True,
        'require_invoice_paid': True,
    })
    print(f"  ✓ Created North Team Commission Plan")

# Create role configurations for North Team
role_configs_north = [
    {'role': 'salesperson', 'percentage': 5.00, 'label': 'Salesperson'},
    {'role': 'team_leader', 'percentage': 3.00, 'label': 'Team Leader'},
    {'role': 'sales_director', 'percentage': 2.00, 'label': 'Sales Director'},
]

for config in role_configs_north:
    RoleConfig.create({
        'plan_id': plan_north.id,
        'role': config['role'],
        'default_percentage': config['percentage'],
        'active': True,
    })
    print(f"  ✓ Added {config['label']}: {config['percentage']}%")

# ============================================
# STEP 6: Create Commission Plan - South Team
# ============================================
print("\nStep 6: Creating Commission Plan - South Team...")

plan_south = CommissionPlan.search([('name', '=', 'South Team Commission Plan')], limit=1)
if plan_south:
    print(f"  ✓ South Team Commission Plan already exists")
    # Clean up existing role configs
    plan_south.role_config_ids.unlink()
else:
    plan_south = CommissionPlan.create({
        'name': 'South Team Commission Plan',
        'is_hierarchical': True,
        'require_invoice_paid': True,
    })
    print(f"  ✓ Created South Team Commission Plan")

# Create role configurations for South Team
role_configs_south = [
    {'role': 'salesperson', 'percentage': 6.00, 'label': 'Salesperson'},
    {'role': 'team_leader', 'percentage': 2.50, 'label': 'Team Leader'},
    {'role': 'sales_director', 'percentage': 1.50, 'label': 'Sales Director'},
]

for config in role_configs_south:
    RoleConfig.create({
        'plan_id': plan_south.id,
        'role': config['role'],
        'default_percentage': config['percentage'],
        'active': True,
    })
    print(f"  ✓ Added {config['label']}: {config['percentage']}%")

# ============================================
# Summary
# ============================================
print("\n" + "="*70)
print("DEMO DATA CREATION COMPLETE!")
print("="*70)

print("\n📊 Users Created:")
print(f"  • Sales Director: {director.name} (login: director.demo)")
print(f"  • Team Leader North: {tl_north.name} (login: teamleader.north)")
print(f"  • Team Leader South: {tl_south.name} (login: teamleader.south)")
print(f"  • North Team: {len(north_sp_records)} salespeople")
for sp in north_sp_records:
    print(f"    - {sp.name} (login: {sp.login})")
print(f"  • South Team: {len(south_sp_records)} salespeople")
for sp in south_sp_records:
    print(f"    - {sp.name} (login: {sp.login})")

print("\n📈 Commission Plans Created:")
print(f"  • {plan_north.name}")
print(f"    - Salesperson: 5% | Team Leader: 3% | Sales Director: 2%")
print(f"  • {plan_south.name}")
print(f"    - Salesperson: 6% | Team Leader: 2.5% | Sales Director: 1.5%")

print("\n🔑 All passwords: demo")

print("\n✅ You can now:")
print("  1. Login as any user (password: demo)")
print("  2. Create sales orders as salespeople")
print("  3. Assign commission plans to sales orders")
print("  4. Post and pay invoices to generate commissions")
print("  5. View team members in team leader/director profiles")

print("\n" + "="*70 + "\n")

# Commit the transaction
env.cr.commit()
print("✅ Transaction committed!\n")
