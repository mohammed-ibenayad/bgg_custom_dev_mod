#!/usr/bin/env python3
"""Quick check for project S00806 - paste this in Odoo shell"""

# Find the project
project = env['project.project'].search([
    '|',
    ('sale_line_id.order_id.name', '=', 'S00806'),
    ('name', 'ilike', 'S00806')
], limit=1)

if not project:
    print("❌ Project not found!")
else:
    print(f"\n📋 Project: {project.name}")
    print(f"   ID: {project.id}")
    print(f"   Created: {project.create_date}")
    print(f"   Modified: {project.write_date}")
    print(f"   Newly created? {project.create_date == project.write_date}")
    print(f"\n🔗 Sale Order Line: {project.sale_line_id.id if project.sale_line_id else 'MISSING!'}")

    if project.sale_line_id:
        print(f"   SO: {project.sale_line_id.order_id.name}")
        print(f"   Customer: {project.sale_line_id.order_id.partner_id.name}")

    print(f"\n📁 Documents Folder: {project.documents_folder_id.id if project.documents_folder_id else 'MISSING!'}")

    if project.documents_folder_id:
        print(f"   Current name: '{project.documents_folder_id.name}'")

        if project.sale_line_id:
            expected = f"{project.sale_line_id.order_id.name} - Projet - {project.sale_line_id.order_id.partner_id.name}"
            print(f"   Expected name: '{expected}'")
            print(f"   Match? {project.documents_folder_id.name == expected}")
