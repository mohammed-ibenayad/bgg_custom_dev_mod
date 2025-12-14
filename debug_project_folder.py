#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debugging script for Project Folder Name automation rule
Run this in Odoo shell to diagnose why S00806 folder wasn't renamed
"""

# Instructions to run:
# python odoo-bin shell -d your_database_name --addons-path=addons,bgg_custom_dev
# Then paste this script

def debug_project_folder():
    """Debug the Update Project Folder Name automation for a specific project"""

    print("\n" + "="*80)
    print("PROJECT FOLDER NAME AUTOMATION - DIAGNOSTIC REPORT")
    print("="*80 + "\n")

    # Find project by sale order name S00806
    projects = env['project.project'].search([('sale_line_id.order_id.name', '=', 'S00806')])

    if not projects:
        print("❌ ERROR: No project found linked to sale order S00806")
        print("\nTrying to find project by name containing 'S00806'...")
        projects = env['project.project'].search([('name', 'ilike', 'S00806')])
        if not projects:
            print("❌ Still no project found. Please verify the sale order exists.")
            return

    print(f"✓ Found {len(projects)} project(s) for S00806:\n")

    for idx, project in enumerate(projects, 1):
        print(f"\n{'='*80}")
        print(f"PROJECT #{idx}: {project.name} (ID: {project.id})")
        print(f"{'='*80}")

        # Check 1: Module installation
        print("\n1️⃣  MODULE CHECK:")
        print(f"   - bgg_custom_dev module installed: ", end="")
        module = env['ir.module.module'].search([('name', '=', 'bgg_custom_dev')])
        if module and module.state == 'installed':
            print("✅ YES")
        else:
            print(f"❌ NO (state: {module.state if module else 'not found'})")

        # Check 2: Project creation timestamps
        print("\n2️⃣  CREATION CHECK:")
        print(f"   - Created: {project.create_date}")
        print(f"   - Modified: {project.write_date}")
        print(f"   - Is newly created? ", end="")
        if project.create_date == project.write_date:
            print("✅ YES (automation should have triggered)")
        else:
            print(f"❌ NO (was updated after creation - automation won't trigger)")
            print(f"      Time difference: {project.write_date - project.create_date}")

        # Check 3: Sale order line
        print("\n3️⃣  SALE ORDER LINE CHECK:")
        if project.sale_line_id:
            print(f"   ✅ sale_line_id: {project.sale_line_id.id}")
            print(f"      - Product: {project.sale_line_id.product_id.name}")
            print(f"      - Sale Order: {project.sale_line_id.order_id.name}")
            print(f"      - Customer: {project.sale_line_id.order_id.partner_id.name}")
        else:
            print(f"   ❌ sale_line_id: None (automation won't work without this!)")

        # Check 4: Documents folder
        print("\n4️⃣  DOCUMENTS FOLDER CHECK:")
        if project.documents_folder_id:
            print(f"   ✅ documents_folder_id: {project.documents_folder_id.id}")
            print(f"      - Current name: '{project.documents_folder_id.name}'")

            if project.sale_line_id:
                expected_name = f"{project.sale_line_id.order_id.name} - Projet - {project.sale_line_id.order_id.partner_id.name}"
                print(f"      - Expected name: '{expected_name}'")

                if project.documents_folder_id.name == expected_name:
                    print(f"      ✅ Folder name is CORRECT")
                else:
                    print(f"      ❌ Folder name is INCORRECT")
        else:
            print(f"   ❌ documents_folder_id: None (automation won't work without this!)")

        # Check 5: Method exists
        print("\n5️⃣  AUTOMATION METHOD CHECK:")
        if hasattr(project, '_update_project_folder_name'):
            print(f"   ✅ _update_project_folder_name method exists")
        else:
            print(f"   ❌ _update_project_folder_name method NOT FOUND (module not loaded?)")

        # Check 6: Try to manually trigger the automation
        print("\n6️⃣  MANUAL TRIGGER TEST:")
        if project.sale_line_id and project.documents_folder_id:
            try:
                # Store original name
                original_name = project.documents_folder_id.name

                # Manually call the automation method
                print(f"   Attempting to manually trigger automation...")
                project._update_project_folder_name(project)

                new_name = project.documents_folder_id.name
                print(f"   Original folder name: '{original_name}'")
                print(f"   New folder name: '{new_name}'")

                if new_name != original_name:
                    print(f"   ✅ Automation WORKED when manually triggered!")
                else:
                    print(f"   ⚠️  Folder name unchanged (check logs for errors)")

            except Exception as e:
                print(f"   ❌ ERROR when manually triggering: {str(e)}")
        else:
            print(f"   ⚠️  Cannot test - missing sale_line_id or documents_folder_id")

        # Check 7: Search logs
        print("\n7️⃣  LOG CHECK:")
        try:
            logs = env['ir.logging'].search([
                ('name', '=', 'bgg_custom_dev.models.project_project'),
                ('create_date', '>=', project.create_date),
            ], order='create_date desc', limit=10)

            if logs:
                print(f"   Found {len(logs)} log entries:")
                for log in logs:
                    print(f"      [{log.level}] {log.message[:100]}")
            else:
                print(f"   ⚠️  No logs found (logging might not be enabled)")
        except:
            print(f"   ⚠️  Cannot access logs")

    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80 + "\n")

# Run the diagnostic
debug_project_folder()
