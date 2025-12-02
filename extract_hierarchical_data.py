#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Data Extraction Script for Hierarchical Commission Models
================================================================

Run in Odoo shell:
    ./odoo-bin shell -d your_database
    >>> exec(open('extract_hierarchical_data.py').read())
"""

import json
from pprint import pprint

print("="*80)
print(" HIERARCHICAL COMMISSION DATA EXTRACTION")
print("="*80)
print()

# ============================================
# 1. Extract Commission Plans (Hierarchical)
# ============================================
print("1. HIERARCHICAL COMMISSION PLANS")
print("-"*80)

CommissionPlan = env['sale.commission.plan']
hierarchical_plans = CommissionPlan.search([('type', '=', 'hierarchical')])

print(f"Found {len(hierarchical_plans)} hierarchical commission plan(s)")
print()

for plan in hierarchical_plans:
    print(f"📋 Plan: {plan.name} (ID: {plan.id})")
    print(f"   Type: {plan.type}")
    print(f"   Periodicity: {plan.periodicity}")
    print(f"   State: {plan.state}")
    print(f"   Require Paid Invoice: {plan.require_invoice_paid}")
    print(f"   Company: {plan.company_id.name if plan.company_id else 'N/A'}")

    # Show role configurations
    if plan.role_config_ids:
        print(f"   Role Configurations ({len(plan.role_config_ids)}):")
        for config in plan.role_config_ids:
            print(f"     - {config.role}: {config.default_percentage}%")
    else:
        print(f"   ⚠️  No role configurations defined")

    # Show associated users (if any)
    if hasattr(plan, 'user_ids') and plan.user_ids:
        print(f"   Users ({len(plan.user_ids)}):")
        for user_link in plan.user_ids[:5]:  # Show first 5
            if hasattr(user_link, 'user_id'):
                print(f"     - {user_link.user_id.name}")

    # Show commission count
    commission_count = env['sale.commission'].search_count([('plan_id', '=', plan.id)])
    print(f"   Generated Commissions: {commission_count}")
    print()

# ============================================
# 2. Extract Role Configurations
# ============================================
print()
print("2. ROLE CONFIGURATIONS")
print("-"*80)

RoleConfig = env['hr.commission.role.config']
all_configs = RoleConfig.search([])

print(f"Found {len(all_configs)} role configuration(s)")
print()

# Group by plan
configs_by_plan = {}
for config in all_configs:
    plan_name = config.plan_id.name if config.plan_id else "No Plan"
    if plan_name not in configs_by_plan:
        configs_by_plan[plan_name] = []
    configs_by_plan[plan_name].append(config)

for plan_name, configs in configs_by_plan.items():
    print(f"📊 {plan_name}:")
    for config in configs:
        status = "✅" if config.active else "❌"
        print(f"   {status} {config.role}: {config.default_percentage}%")
    print()

# ============================================
# 3. Extract Commissions
# ============================================
print()
print("3. COMMISSIONS (SAMPLE)")
print("-"*80)

Commission = env['sale.commission']
all_commissions = Commission.search([], limit=10, order='date desc')

print(f"Showing 10 most recent of {Commission.search_count([])} total commission(s)")
print()

for comm in all_commissions:
    print(f"💰 {comm.name}")
    print(f"   User: {comm.user_id.name} ({comm.role})")
    print(f"   Plan: {comm.plan_id.name if comm.plan_id else 'N/A'}")
    print(f"   Date: {comm.date}")
    print(f"   Base: {comm.base_amount} | Percentage: {comm.commission_percentage}% | Amount: {comm.commission_amount}")
    print(f"   Status: {comm.payment_status} | State: {comm.state}")
    if comm.sale_order_id:
        print(f"   Sale Order: {comm.sale_order_id.name}")
    if comm.invoice_id:
        print(f"   Invoice: {comm.invoice_id.name}")
    print()

# ============================================
# 4. Extract Payments
# ============================================
print()
print("4. COMMISSION PAYMENTS")
print("-"*80)

Payment = env['sale.commission.payment']
all_payments = Payment.search([], limit=10, order='create_date desc')

print(f"Found {Payment.search_count([])} payment record(s)")
print()

if all_payments:
    for payment in all_payments:
        print(f"💳 Payment {payment.name if hasattr(payment, 'name') else payment.id}")
        print(f"   User: {payment.user_id.name if payment.user_id else 'N/A'}")

        if hasattr(payment, 'state'):
            print(f"   State: {payment.state}")

        if hasattr(payment, 'commission_ids'):
            print(f"   Commissions: {len(payment.commission_ids)}")

        if hasattr(payment, 'total_amount'):
            print(f"   Total Amount: {payment.total_amount}")

        print()
else:
    print("⚠️  No payment records found")
    print()

# ============================================
# 5. Extract Claims
# ============================================
print()
print("5. COMMISSION CLAIMS")
print("-"*80)

Claim = env['sale.commission.claim']
all_claims = Claim.search([], limit=10, order='create_date desc')

print(f"Found {Claim.search_count([])} claim record(s)")
print()

if all_claims:
    for claim in all_claims:
        print(f"🎫 Claim {claim.name if hasattr(claim, 'name') else claim.id}")
        print(f"   User: {claim.user_id.name if claim.user_id else 'N/A'}")

        if hasattr(claim, 'state'):
            print(f"   State: {claim.state}")

        if hasattr(claim, 'commission_ids'):
            print(f"   Commissions: {len(claim.commission_ids)}")

        if hasattr(claim, 'total_amount'):
            print(f"   Total Amount: {claim.total_amount}")

        print()
else:
    print("⚠️  No claim records found")
    print()

# ============================================
# 6. User Commission Hierarchy
# ============================================
print()
print("6. USER COMMISSION HIERARCHY")
print("-"*80)

ResUsers = env['res.users']
users_with_roles = ResUsers.search([('commission_role', '!=', False)])

print(f"Found {len(users_with_roles)} user(s) with commission roles")
print()

# Group by role
users_by_role = {}
for user in users_with_roles:
    role = user.commission_role
    if role not in users_by_role:
        users_by_role[role] = []
    users_by_role[role].append(user)

for role, users in users_by_role.items():
    print(f"👤 {role.upper()} ({len(users)} users):")
    for user in users[:10]:  # Limit to 10 per role
        hierarchy = [user.name]
        if user.team_leader_id:
            hierarchy.append(f"TL: {user.team_leader_id.name}")
        if user.sales_director_id:
            hierarchy.append(f"Dir: {user.sales_director_id.name}")
        print(f"   - {' → '.join(hierarchy)}")
    print()

# ============================================
# 7. Statistics Summary
# ============================================
print()
print("7. STATISTICS SUMMARY")
print("-"*80)

stats = {
    'Hierarchical Plans': CommissionPlan.search_count([('type', '=', 'hierarchical')]),
    'Role Configurations': RoleConfig.search_count([]),
    'Total Commissions': Commission.search_count([]),
    'Unpaid Commissions': Commission.search_count([('payment_status', '=', 'unpaid')]),
    'Paid Commissions': Commission.search_count([('payment_status', '=', 'paid')]),
    'Commission Payments': Payment.search_count([]),
    'Commission Claims': Claim.search_count([]),
    'Users with Commission Role': ResUsers.search_count([('commission_role', '!=', False)]),
}

for key, value in stats.items():
    print(f"  {key}: {value}")

print()

# ============================================
# 8. Commission by Role Breakdown
# ============================================
print()
print("8. COMMISSION BREAKDOWN BY ROLE")
print("-"*80)

for role in ['salesperson', 'team_leader', 'sales_director']:
    count = Commission.search_count([('role', '=', role)])

    # Calculate total amount
    commissions = Commission.search([('role', '=', role)])
    total_amount = sum(comm.commission_amount for comm in commissions)

    print(f"  {role.upper()}:")
    print(f"    Count: {count}")
    print(f"    Total Amount: {total_amount:.2f}")
    print()

print("="*80)
print(" EXTRACTION COMPLETE")
print("="*80)
print()

# ============================================
# BONUS: Export Functions
# ============================================

def export_to_json(model_name, domain=[], filename=None):
    """
    Export model data to JSON

    Usage:
        export_to_json('sale.commission', [('payment_status', '=', 'unpaid')], '/tmp/unpaid_commissions.json')
    """
    Model = env[model_name]
    records = Model.search(domain)

    data = []
    for record in records:
        record_data = {'id': record.id}

        for field_name in record._fields:
            if field_name.startswith('__'):
                continue

            try:
                value = record[field_name]
                field_type = type(value).__name__

                if 'Many2one' in field_type and value:
                    record_data[field_name] = {'id': value.id, 'name': value.display_name}
                elif 'Many2many' in field_type or 'One2many' in field_type:
                    record_data[field_name] = [r.id for r in value]
                elif 'date' in field_type.lower():
                    record_data[field_name] = str(value) if value else None
                else:
                    record_data[field_name] = value
            except:
                pass

        data.append(record_data)

    if filename:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Exported {len(data)} records to {filename}")

    return data


print("AVAILABLE HELPER FUNCTIONS:")
print("-"*80)
print("""
# Export unpaid commissions to JSON:
export_to_json('sale.commission', [('payment_status', '=', 'unpaid')], '/tmp/unpaid_commissions.json')

# Export all hierarchical plans:
export_to_json('sale.commission.plan', [('type', '=', 'hierarchical')], '/tmp/hierarchical_plans.json')

# Export role configurations:
export_to_json('hr.commission.role.config', [], '/tmp/role_configs.json')

# Get specific plan details:
plan = env['sale.commission.plan'].search([('type', '=', 'hierarchical')], limit=1)
print(plan.read())

# Get commissions for specific user:
user = env['res.users'].search([('login', '=', 'your.user')], limit=1)
commissions = env['sale.commission'].search([('user_id', '=', user.id)])
for c in commissions:
    print(f"{c.name}: {c.commission_amount}")
""")

print()
print("="*80)
