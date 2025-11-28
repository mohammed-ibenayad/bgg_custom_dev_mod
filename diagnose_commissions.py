#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commission Diagnostic Script

This script investigates why commissions are not being generated
for the last 4 sales orders.

Usage:
    odoo-bin shell -d your_database < diagnose_commissions.py
"""

print("\n" + "="*80)
print("COMMISSION DIAGNOSTIC SCRIPT")
print("="*80 + "\n")

# Get models
SaleOrder = env['sale.order']
AccountMove = env['account.move']
CommissionPlan = env['sale.commission.plan']
Commission = env['sale.commission']
ResUsers = env['res.users']

# ============================================
# Get last 4 sales orders
# ============================================
print("📋 Fetching last 4 sales orders...\n")

sale_orders = SaleOrder.search([], order='date_order desc', limit=4)

if not sale_orders:
    print("❌ No sales orders found in the system!")
    print("\nPlease create some sales orders first.")
    exit()

print(f"Found {len(sale_orders)} sales orders to analyze:\n")

for idx, so in enumerate(sale_orders, 1):
    print(f"{idx}. {so.name} - {so.partner_id.name} - ${so.amount_total:.2f}")
    print(f"   Salesperson: {so.user_id.name if so.user_id else 'NONE'}")
    print(f"   Date: {so.date_order}")
    print(f"   State: {so.state}")
    print()

# ============================================
# Analyze each sales order
# ============================================
print("\n" + "="*80)
print("DETAILED ANALYSIS")
print("="*80 + "\n")

issues_found = []

for idx, so in enumerate(sale_orders, 1):
    print(f"\n{'─'*80}")
    print(f"📊 SALES ORDER #{idx}: {so.name}")
    print(f"{'─'*80}\n")

    # Check 1: Salesperson
    print("✓ Check 1: Salesperson Assignment")
    if not so.user_id:
        print("  ❌ ISSUE: No salesperson assigned to this order!")
        issues_found.append(f"{so.name}: No salesperson assigned")
        print("  → FIX: Assign a user to the 'Salesperson' field\n")
        continue
    else:
        print(f"  ✓ Salesperson: {so.user_id.name} (ID: {so.user_id.id})")

        # Check salesperson's commission role
        if so.user_id.commission_role:
            print(f"  ✓ Commission Role: {so.user_id.commission_role}")
        else:
            print(f"  ⚠️  WARNING: Salesperson has no commission role set!")
            issues_found.append(f"{so.name}: Salesperson has no commission role")

        # Check hierarchy
        if so.user_id.team_leader_id:
            print(f"  ✓ Team Leader: {so.user_id.team_leader_id.name}")
        else:
            print(f"  ⚠️  No Team Leader assigned")

        if so.user_id.sales_director_id:
            print(f"  ✓ Sales Director: {so.user_id.sales_director_id.name}")
        elif so.user_id.team_leader_id and so.user_id.team_leader_id.sales_director_id:
            print(f"  ✓ Sales Director (via TL): {so.user_id.team_leader_id.sales_director_id.name}")
        else:
            print(f"  ⚠️  No Sales Director in hierarchy")
        print()

    # Check 2: Invoices
    print("✓ Check 2: Invoices")
    invoices = so.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')

    if not invoices:
        print("  ❌ ISSUE: No customer invoices found for this order!")
        issues_found.append(f"{so.name}: No invoices")
        print("  → FIX: Create and post an invoice for this sales order\n")
        continue
    else:
        print(f"  ✓ Found {len(invoices)} invoice(s):")
        for inv in invoices:
            print(f"    - {inv.name}")
            print(f"      State: {inv.state}")
            print(f"      Payment State: {inv.payment_state}")
            print(f"      Amount: ${inv.amount_total:.2f}")

            # Check if paid
            if inv.payment_state not in ['paid', 'in_payment']:
                print(f"      ❌ ISSUE: Invoice not paid! (Current: {inv.payment_state})")
                issues_found.append(f"{so.name}/{inv.name}: Invoice not paid")
                print(f"      → FIX: Register payment for this invoice")
            else:
                print(f"      ✓ Invoice is paid")

            # Check if commissions exist
            existing_commissions = Commission.search([
                ('invoice_id', '=', inv.id),
                ('sale_order_id', '=', so.id)
            ])

            if existing_commissions:
                print(f"      ✓ Commissions exist: {len(existing_commissions)} record(s)")
                for comm in existing_commissions:
                    print(f"        - {comm.user_id.name} ({comm.role}): ${comm.commission_amount:.2f}")
            else:
                print(f"      ❌ No commissions created for this invoice!")
        print()

    # Check 3: Commission Plans
    print("✓ Check 3: Commission Plans")

    # Search for approved hierarchical plans
    approved_plans = CommissionPlan.search([
        ('is_hierarchical', '=', True),
        ('state', '=', 'approved'),
        ('company_id', '=', so.company_id.id)
    ])

    if not approved_plans:
        print("  ❌ CRITICAL ISSUE: No approved hierarchical commission plans found!")
        issues_found.append(f"System: No approved commission plans")
        print("  → FIX: You need to APPROVE a commission plan!")
        print()
        print("  Current commission plans in system:")
        all_plans = CommissionPlan.search([('is_hierarchical', '=', True)])
        if all_plans:
            for plan in all_plans:
                print(f"    - {plan.name}")
                print(f"      State: {plan.state if hasattr(plan, 'state') else 'N/A'}")
                print(f"      Hierarchical: {plan.is_hierarchical}")
                print(f"      Require Paid Invoice: {plan.require_invoice_paid}")

                # Check role configs
                role_configs = plan.role_config_ids
                if role_configs:
                    print(f"      Role Configs:")
                    for rc in role_configs:
                        print(f"        - {rc.role}: {rc.default_percentage}%")
                else:
                    print(f"      ⚠️  No role configurations!")
        else:
            print("    ❌ No hierarchical commission plans found at all!")
    else:
        print(f"  ✓ Found {len(approved_plans)} approved hierarchical plan(s):")
        for plan in approved_plans:
            print(f"    - {plan.name}")
            print(f"      State: {plan.state if hasattr(plan, 'state') else 'NEEDS APPROVAL'}")
            print(f"      Require Paid Invoice: {plan.require_invoice_paid}")

            role_configs = plan.role_config_ids
            if role_configs:
                print(f"      Role Configs: {len(role_configs)}")
                for rc in role_configs:
                    print(f"        - {rc.role}: {rc.default_percentage}% (Active: {rc.active})")
            else:
                print(f"      ❌ No role configurations!")
                issues_found.append(f"{plan.name}: No role configurations")
    print()

# ============================================
# Summary of Issues
# ============================================
print("\n" + "="*80)
print("SUMMARY")
print("="*80 + "\n")

if issues_found:
    print(f"❌ Found {len(issues_found)} issue(s):\n")
    for i, issue in enumerate(issues_found, 1):
        print(f"{i}. {issue}")

    print("\n" + "─"*80)
    print("COMMON FIXES:")
    print("─"*80)

    # Check for the most common issue
    if any('No approved commission plans' in issue for issue in issues_found):
        print("\n🔴 CRITICAL: Commission plans need to be APPROVED!")
        print("\nThe commission plan model might not have a 'state' field.")
        print("Checking if commission plans have a state field...\n")

        plan = CommissionPlan.search([], limit=1)
        if plan:
            if hasattr(plan, 'state'):
                print("✓ Commission plans DO have a 'state' field")
                print("\nTo approve a plan, run:")
                print(">>> plan = env['sale.commission.plan'].search([('is_hierarchical', '=', True)], limit=1)")
                print(">>> plan.state = 'approved'")
                print(">>> env.cr.commit()")
            else:
                print("⚠️  Commission plans DO NOT have a 'state' field")
                print("\nThis means the commission generation logic is looking for")
                print("plan.state == 'approved', but the field doesn't exist!")
                print("\nYou need to either:")
                print("1. Add a 'state' field to sale.commission.plan model, OR")
                print("2. Remove the state check from the commission generation logic")

    if any('Invoice not paid' in issue for issue in issues_found):
        print("\n💰 Register payments for invoices")

    if any('No salesperson' in issue for issue in issues_found):
        print("\n👤 Assign salespeople to sales orders")

    if any('no commission role' in issue.lower() for issue in issues_found):
        print("\n🎭 Set commission roles for users")

else:
    print("✅ No obvious issues found!")
    print("\nIf commissions are still not being created, the issue might be:")
    print("1. The commission generation method is not being called")
    print("2. There's an error in the commission creation logic")
    print("3. The invoice payment state change is not triggering the hook")

# ============================================
# Quick Fixes Section
# ============================================
print("\n" + "="*80)
print("QUICK DIAGNOSTIC COMMANDS")
print("="*80 + "\n")

print("Check commission plan state field:")
print(">>> env['sale.commission.plan']._fields.get('state')")
print()

print("List all commission plans:")
print(">>> env['sale.commission.plan'].search([]).mapped(lambda p: (p.name, getattr(p, 'state', 'NO STATE FIELD')))")
print()

print("Check if commission plan has state field and approve all plans:")
print(">>> plans = env['sale.commission.plan'].search([('is_hierarchical', '=', True)])")
print(">>> for p in plans:")
print(">>>     if hasattr(p, 'state'):")
print(">>>         p.state = 'approved'")
print(">>> env.cr.commit()")
print()

print("Manually trigger commission creation for a specific invoice:")
print(">>> inv = env['account.move'].search([('move_type', '=', 'out_invoice')], limit=1)")
print(">>> inv._create_hierarchical_commissions()")
print(">>> env.cr.commit()")
print()

print("="*80)
print("\n")
