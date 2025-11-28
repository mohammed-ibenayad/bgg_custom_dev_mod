#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commission Generation Fix Script

This script fixes common issues preventing commission generation
and manually triggers commission creation for paid invoices.

Usage:
    odoo-bin shell -d your_database < fix_commission_generation.py
"""

print("\n" + "="*80)
print("COMMISSION GENERATION FIX SCRIPT")
print("="*80 + "\n")

# Get models
SaleOrder = env['sale.order']
AccountMove = env['account.move']
CommissionPlan = env['sale.commission.plan']
Commission = env['sale.commission']

# ============================================
# STEP 1: Check and fix commission plan state
# ============================================
print("Step 1: Checking commission plan state field...\n")

plans = CommissionPlan.search([('is_hierarchical', '=', True)])

if not plans:
    print("❌ No hierarchical commission plans found!")
    print("Please create at least one commission plan with 'Hierarchical Plan' enabled.")
    exit()

print(f"Found {len(plans)} hierarchical commission plan(s):\n")

has_state_field = hasattr(plans[0], 'state')

if has_state_field:
    print("✓ Commission plans have a 'state' field\n")
    print("Approving all hierarchical commission plans...\n")

    for plan in plans:
        print(f"  - {plan.name}")
        current_state = plan.state if hasattr(plan, 'state') else 'unknown'
        print(f"    Current state: {current_state}")

        # Check role configs
        if not plan.role_config_ids:
            print(f"    ⚠️  WARNING: No role configurations!")
        else:
            print(f"    ✓ Role configs: {len(plan.role_config_ids)}")
            for rc in plan.role_config_ids:
                print(f"      - {rc.role}: {rc.default_percentage}%")

        # Try to approve
        if hasattr(plan, 'state'):
            if plan.state != 'approved':
                plan.state = 'approved'
                print(f"    ✓ Set state to 'approved'")
            else:
                print(f"    ✓ Already approved")
        print()

else:
    print("⚠️  WARNING: Commission plans do NOT have a 'state' field!")
    print("The commission generation logic checks for state='approved',")
    print("but the field doesn't exist. This will prevent commissions from being created.\n")
    print("You need to either:")
    print("1. Add a 'state' field to the sale.commission.plan model, OR")
    print("2. Modify the commission generation logic to remove the state check\n")
    print("For now, we'll try to generate commissions anyway...\n")

# ============================================
# STEP 2: Find paid invoices without commissions
# ============================================
print("Step 2: Finding paid invoices without commissions...\n")

# Get paid customer invoices
paid_invoices = AccountMove.search([
    ('move_type', '=', 'out_invoice'),
    ('payment_state', 'in', ['paid', 'in_payment']),
    ('state', '=', 'posted')
], order='date desc', limit=20)

print(f"Found {len(paid_invoices)} paid customer invoice(s) in the system\n")

if not paid_invoices:
    print("❌ No paid invoices found!")
    print("Please create a sales order, invoice it, and register payment.")
    exit()

invoices_to_process = []

for inv in paid_invoices:
    # Check if commissions already exist
    existing = Commission.search([('invoice_id', '=', inv.id)])

    if not existing:
        # Get sale order
        sale_orders = inv.invoice_line_ids.mapped('sale_line_ids.order_id')

        if sale_orders:
            invoices_to_process.append((inv, sale_orders[0]))
            print(f"  - {inv.name} (${inv.amount_total:.2f})")
            print(f"    Sale Order: {sale_orders[0].name}")
            print(f"    Salesperson: {sale_orders[0].user_id.name if sale_orders[0].user_id else 'NONE'}")
            print(f"    ❌ No commissions created yet")
            print()

if not invoices_to_process:
    print("✅ All paid invoices already have commissions!")
    print("\nExisting commissions:")
    all_commissions = Commission.search([], limit=10, order='create_date desc')
    for comm in all_commissions:
        print(f"  - {comm.user_id.name} ({comm.role}): ${comm.commission_amount:.2f}")
        print(f"    Invoice: {comm.invoice_id.name if comm.invoice_id else 'N/A'}")
        print(f"    Sale Order: {comm.sale_order_id.name if comm.sale_order_id else 'N/A'}")
        print()
    exit()

# ============================================
# STEP 3: Manually create commissions
# ============================================
print(f"\nStep 3: Manually creating commissions for {len(invoices_to_process)} invoice(s)...\n")

commissions_created = 0

for inv, sale_order in invoices_to_process:
    print(f"Processing: {inv.name} - {sale_order.name}")

    # Get salesperson
    salesperson = sale_order.user_id
    if not salesperson:
        print(f"  ⚠️  Skipping: No salesperson assigned")
        continue

    print(f"  Salesperson: {salesperson.name}")

    # Get commission plan
    if has_state_field:
        commission_plan = CommissionPlan.search([
            ('is_hierarchical', '=', True),
            ('state', '=', 'approved'),
            ('company_id', '=', inv.company_id.id)
        ], limit=1)
    else:
        # If no state field, just get any hierarchical plan
        commission_plan = CommissionPlan.search([
            ('is_hierarchical', '=', True),
            ('company_id', '=', inv.company_id.id)
        ], limit=1)

    if not commission_plan:
        print(f"  ❌ No commission plan found!")
        continue

    print(f"  Commission Plan: {commission_plan.name}")

    # Build hierarchy
    users_to_commission = []

    # 1. Salesperson
    if salesperson.commission_role:
        users_to_commission.append((salesperson, salesperson.commission_role))
        print(f"    - Salesperson: {salesperson.name} ({salesperson.commission_role})")

    # 2. Team Leader
    if salesperson.team_leader_id:
        users_to_commission.append((salesperson.team_leader_id, 'team_leader'))
        print(f"    - Team Leader: {salesperson.team_leader_id.name}")

    # 3. Sales Director
    if salesperson.sales_director_id:
        users_to_commission.append((salesperson.sales_director_id, 'sales_director'))
        print(f"    - Sales Director: {salesperson.sales_director_id.name}")
    elif salesperson.team_leader_id and salesperson.team_leader_id.sales_director_id:
        users_to_commission.append((salesperson.team_leader_id.sales_director_id, 'sales_director'))
        print(f"    - Sales Director (via TL): {salesperson.team_leader_id.sales_director_id.name}")

    if not users_to_commission:
        print(f"  ⚠️  No users in commission hierarchy!")
        continue

    # Calculate period
    period = inv.invoice_date.strftime('%Y-%m') if inv.invoice_date else fields.Date.today().strftime('%Y-%m')
    base_amount = inv.amount_total

    # Create commission records
    print(f"  Creating commissions (Base: ${base_amount:.2f}):")

    for user, role in users_to_commission:
        # Get role config
        role_config = env['hr.commission.role.config'].search([
            ('plan_id', '=', commission_plan.id),
            ('role', '=', role),
            ('active', '=', True)
        ], limit=1)

        if not role_config:
            print(f"    ⚠️  No role config for {role} - skipping")
            continue

        # Create commission
        comm = Commission.create({
            'user_id': user.id,
            'role': role,
            'sale_order_id': sale_order.id,
            'invoice_id': inv.id,
            'plan_id': commission_plan.id,
            'date': inv.invoice_date or fields.Date.today(),
            'period': period,
            'base_amount': base_amount,
            'payment_status': 'unpaid',
            'state': 'confirmed',
            'company_id': inv.company_id.id,
            'currency_id': inv.currency_id.id,
        })

        commissions_created += 1
        print(f"    ✓ {user.name} ({role}): ${comm.commission_amount:.2f} ({role_config.default_percentage}%)")

    print()

# ============================================
# STEP 4: Commit and summary
# ============================================
print("="*80)
print("SUMMARY")
print("="*80 + "\n")

if commissions_created > 0:
    env.cr.commit()
    print(f"✅ Successfully created {commissions_created} commission record(s)!\n")

    print("You can now:")
    print("1. Go to Commissions menu to view all commissions")
    print("2. Check each user's profile → Commission Hierarchy tab → View commissions")
    print("3. Process commission claims and payments")

else:
    print("⚠️  No commissions were created.")
    print("\nPossible reasons:")
    print("1. All invoices already have commissions")
    print("2. No approved commission plans")
    print("3. Users don't have commission roles set")
    print("4. No role configurations in commission plans")
    print("\nRun the diagnose_commissions.py script for detailed analysis.")

print("\n" + "="*80 + "\n")
