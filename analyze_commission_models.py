#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo Shell Script: Analyze Commission Models
=============================================

Run this script in Odoo shell:
    ./odoo-bin shell -d your_database < analyze_commission_models.py

Or interactively:
    ./odoo-bin shell -d your_database
    >>> exec(open('analyze_commission_models.py').read())
"""

import json
from datetime import datetime

# ============================================
# Configuration
# ============================================

# All commission-related models from the system
COMMISSION_MODELS = [
    'sale.commission',
    'sale.commission.plan',
    'sale.commission.plan.user',
    'sale.commission.plan.user.wizard',
    'sale.commission.plan.target',
    'sale.commission.plan.target.commission',
    'sale.commission.plan.target.forecast',
    'sale.commission.plan.achievement',
    'sale.commission.achievement',
    'sale.commission.achievement.report',
    'sale.commission.report',
    'sale.commission.payment',
    'sale.commission.claim',
    'hr.commission.role.config',
]

# Models specifically for hierarchical commission (our custom development)
HIERARCHICAL_MODELS = [
    'sale.commission',           # Custom model for hierarchical commissions
    'sale.commission.plan',      # Extended with 'hierarchical' type
    'sale.commission.payment',   # Custom payment management
    'sale.commission.claim',     # Custom claim system
    'hr.commission.role.config', # Custom role configuration
]

# Models from base sale_commission module (achievement/target based)
BASE_COMMISSION_MODELS = [
    'sale.commission.plan.user',
    'sale.commission.plan.user.wizard',
    'sale.commission.plan.target',
    'sale.commission.plan.target.commission',
    'sale.commission.plan.target.forecast',
    'sale.commission.plan.achievement',
    'sale.commission.achievement',
    'sale.commission.achievement.report',
    'sale.commission.report',
]


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def print_header(title):
    """Print a formatted header"""
    print_separator('=')
    print(f" {title}")
    print_separator('=')
    print()


def print_subheader(title):
    """Print a formatted subheader"""
    print_separator('-')
    print(f" {title}")
    print_separator('-')


def analyze_model_fields(model_name):
    """
    Analyze fields of a given model
    Returns dict with field information
    """
    try:
        Model = env[model_name]
        fields_info = {}

        for field_name, field in Model._fields.items():
            # Skip internal fields starting with __
            if field_name.startswith('__'):
                continue

            fields_info[field_name] = {
                'type': field.type,
                'string': field.string if hasattr(field, 'string') else field_name,
                'required': getattr(field, 'required', False),
                'readonly': getattr(field, 'readonly', False),
                'store': getattr(field, 'store', True),
                'compute': getattr(field, 'compute', None),
                'related': getattr(field, 'related', None),
                'relation': getattr(field, 'comodel_name', None) if field.type in ['many2one', 'one2many', 'many2many'] else None,
            }

        return fields_info

    except KeyError:
        return None


def get_model_data(model_name, limit=5):
    """
    Get sample data from model
    """
    try:
        Model = env[model_name]
        records = Model.search([], limit=limit)

        data = []
        for record in records:
            record_data = {
                'id': record.id,
                'display_name': record.display_name if hasattr(record, 'display_name') else str(record),
            }

            # Add key fields
            key_fields = ['name', 'type', 'state', 'role', 'user_id', 'plan_id', 'payment_status']
            for field in key_fields:
                if field in record._fields:
                    value = record[field]
                    if hasattr(value, 'display_name'):
                        record_data[field] = f"{value.display_name} (id:{value.id})"
                    else:
                        record_data[field] = value

            data.append(record_data)

        return {
            'total_count': Model.search_count([]),
            'sample_records': data,
        }

    except Exception as e:
        return {
            'error': str(e),
            'total_count': 0,
            'sample_records': [],
        }


def categorize_fields(fields_info):
    """
    Categorize fields by type
    """
    categories = {
        'basic': [],
        'relational': [],
        'computed': [],
        'functional': [],
    }

    for field_name, info in fields_info.items():
        if info['compute']:
            categories['computed'].append(field_name)
        elif info['type'] in ['many2one', 'one2many', 'many2many']:
            categories['relational'].append(field_name)
        elif info['related']:
            categories['functional'].append(field_name)
        else:
            categories['basic'].append(field_name)

    return categories


def analyze_model(model_name, show_fields=True, show_data=True):
    """
    Complete analysis of a model
    """
    print_subheader(f"Model: {model_name}")

    # Check if model exists
    fields_info = analyze_model_fields(model_name)

    if fields_info is None:
        print(f"❌ Model '{model_name}' does not exist in this database")
        print()
        return None

    print(f"✅ Model exists with {len(fields_info)} fields")

    # Get data
    data_info = get_model_data(model_name)
    print(f"📊 Records in database: {data_info['total_count']}")
    print()

    # Show field categories
    if show_fields:
        categories = categorize_fields(fields_info)

        print("📋 Field Categories:")
        print(f"  - Basic Fields: {len(categories['basic'])}")
        print(f"  - Relational Fields: {len(categories['relational'])}")
        print(f"  - Computed Fields: {len(categories['computed'])}")
        print(f"  - Functional Fields: {len(categories['functional'])}")
        print()

        # Show important fields
        important_fields = ['name', 'type', 'state', 'role', 'user_id', 'plan_id',
                           'commission_amount', 'payment_status', 'base_amount',
                           'commission_percentage', 'default_percentage', 'periodicity',
                           'require_invoice_paid', 'is_hierarchical', 'role_config_ids']

        existing_important = [f for f in important_fields if f in fields_info]

        if existing_important:
            print("🔑 Important Fields:")
            for field_name in existing_important:
                info = fields_info[field_name]
                field_type = info['type']
                if info['relation']:
                    field_type += f" -> {info['relation']}"
                print(f"  - {field_name}: {field_type} ({info['string']})")
            print()

    # Show sample data
    if show_data and data_info['sample_records']:
        print(f"📄 Sample Records (showing {len(data_info['sample_records'])} of {data_info['total_count']}):")
        for record in data_info['sample_records']:
            print(f"  ID {record['id']}: {record['display_name']}")
            for key, value in record.items():
                if key not in ['id', 'display_name']:
                    print(f"    - {key}: {value}")
        print()

    return {
        'model': model_name,
        'exists': True,
        'field_count': len(fields_info),
        'record_count': data_info['total_count'],
        'fields': fields_info,
        'categories': categorize_fields(fields_info),
    }


def export_field_details(model_name, fields_info, filename):
    """
    Export detailed field information to a file
    """
    output = []
    output.append(f"Model: {model_name}")
    output.append("=" * 80)
    output.append("")

    # Group by category
    categories = categorize_fields(fields_info)

    for category_name, field_list in categories.items():
        if not field_list:
            continue

        output.append(f"\n{category_name.upper()} FIELDS:")
        output.append("-" * 80)

        for field_name in sorted(field_list):
            info = fields_info[field_name]
            output.append(f"\nField: {field_name}")
            output.append(f"  Type: {info['type']}")
            output.append(f"  Label: {info['string']}")
            output.append(f"  Required: {info['required']}")
            output.append(f"  Readonly: {info['readonly']}")
            output.append(f"  Stored: {info['store']}")

            if info['compute']:
                output.append(f"  Computed by: {info['compute']}")

            if info['related']:
                output.append(f"  Related to: {info['related']}")

            if info['relation']:
                output.append(f"  Related Model: {info['relation']}")

    return "\n".join(output)


# ============================================
# MAIN ANALYSIS
# ============================================

print_header("COMMISSION MODELS ANALYSIS")
print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Database: {env.cr.dbname}")
print()

# Analyze hierarchical commission models (OUR CUSTOM DEVELOPMENT)
print_header("1. HIERARCHICAL COMMISSION MODELS (Our Custom Development)")
print("These models are specific to our hierarchical commission system:")
print()

hierarchical_results = {}
for model_name in HIERARCHICAL_MODELS:
    result = analyze_model(model_name, show_fields=True, show_data=True)
    if result:
        hierarchical_results[model_name] = result
    print()

# Analyze base commission models (ORIGINAL ODOO - For Achievement/Target)
print_header("2. BASE COMMISSION MODELS (Original Odoo - Achievement/Target)")
print("These models are from the base sale_commission module:")
print()

base_results = {}
for model_name in BASE_COMMISSION_MODELS:
    result = analyze_model(model_name, show_fields=False, show_data=False)
    if result:
        base_results[model_name] = result
    print()

# Summary
print_header("3. SUMMARY & RECOMMENDATIONS")

print("📊 HIERARCHICAL COMMISSION MODELS (Relevant to our development):")
print_separator('-')
for model_name, result in hierarchical_results.items():
    status = "✅" if result['record_count'] > 0 else "⚠️ (No data)"
    print(f"{status} {model_name}")
    print(f"   - {result['field_count']} fields, {result['record_count']} records")

print()
print("📊 BASE COMMISSION MODELS (Not directly used, for reference only):")
print_separator('-')
for model_name, result in base_results.items():
    status = "✅" if result['record_count'] > 0 else "⚠️ (No data)"
    print(f"{status} {model_name}")
    print(f"   - {result['field_count']} fields, {result['record_count']} records")

print()
print_header("4. KEY RELATIONSHIPS")
print("""
Hierarchical Commission Flow:
├── sale.commission.plan (type='hierarchical')
│   └── hr.commission.role.config (role percentages)
│       └── sale.commission (generated commissions)
│           ├── sale.commission.claim (user claims)
│           └── sale.commission.payment (manager payments)

Key Fields to Focus On:
- sale.commission.plan.type = 'hierarchical'
- sale.commission.plan.is_hierarchical (computed)
- sale.commission.plan.require_invoice_paid
- sale.commission.role (salesperson/team_leader/sales_director)
- hr.commission.role.config.default_percentage
""")

print()
print_header("5. EXPORT DETAILED FIELD INFORMATION")
print("Exporting detailed field information for hierarchical models...")
print()

# Export detailed information for each hierarchical model
for model_name in HIERARCHICAL_MODELS:
    if model_name in hierarchical_results:
        fields_info = hierarchical_results[model_name]['fields']
        filename = f"/tmp/{model_name.replace('.', '_')}_fields.txt"

        content = export_field_details(model_name, fields_info, filename)

        try:
            with open(filename, 'w') as f:
                f.write(content)
            print(f"✅ Exported: {filename}")
        except Exception as e:
            print(f"❌ Could not export {model_name}: {e}")

print()
print_header("ANALYSIS COMPLETE")
print("You can now identify which models and fields are relevant to your development.")
print()

# ============================================
# OPTIONAL: Extract Data for Specific Models
# ============================================

def extract_model_data_json(model_name, domain=[], limit=100):
    """
    Extract data from a model as JSON
    """
    try:
        Model = env[model_name]
        records = Model.search(domain, limit=limit)

        data = []
        for record in records:
            record_data = {'id': record.id}

            # Get all stored fields
            for field_name, field in Model._fields.items():
                if field_name.startswith('__'):
                    continue

                # Skip computed fields that aren't stored
                if hasattr(field, 'compute') and field.compute and not getattr(field, 'store', False):
                    continue

                try:
                    value = record[field_name]

                    # Handle different field types
                    if field.type == 'many2one' and value:
                        record_data[field_name] = {
                            'id': value.id,
                            'display_name': value.display_name
                        }
                    elif field.type in ['one2many', 'many2many'] and value:
                        record_data[field_name] = [r.id for r in value]
                    elif field.type in ['date', 'datetime']:
                        record_data[field_name] = str(value) if value else None
                    elif field.type == 'binary':
                        record_data[field_name] = '<binary data>' if value else None
                    else:
                        record_data[field_name] = value
                except Exception as e:
                    record_data[field_name] = f"<error: {e}>"

            data.append(record_data)

        return data

    except Exception as e:
        print(f"Error extracting data from {model_name}: {e}")
        return []


print_header("6. DATA EXTRACTION FUNCTIONS")
print("""
Use these functions to extract data from specific models:

# Extract all hierarchical commission plans:
plans = extract_model_data_json('sale.commission.plan', [('type', '=', 'hierarchical')])
print(json.dumps(plans, indent=2))

# Extract role configurations:
configs = extract_model_data_json('hr.commission.role.config')
print(json.dumps(configs, indent=2))

# Extract commissions:
commissions = extract_model_data_json('sale.commission', limit=10)
print(json.dumps(commissions, indent=2))

# Extract payments:
payments = extract_model_data_json('sale.commission.payment', limit=10)
print(json.dumps(payments, indent=2))

# Extract claims:
claims = extract_model_data_json('sale.commission.claim', limit=10)
print(json.dumps(claims, indent=2))
""")

print_separator('=')
print("Script execution completed successfully!")
print_separator('=')
