# -*- coding: utf-8 -*-
{
    'name': "Belgogreen Sales Commission",

    'summary': "Hierarchical commission system for sales with multi-level calculation",

    'description': """
Belgogreen Sales Commission Module
===================================

This module provides a comprehensive hierarchical commission system that:

* Automatically calculates commissions for salesperson, team leader, and sales director
* Tracks commission payments and allows users to claim their commissions
* Provides dedicated views for salespeople to see their commissions (wallet)
* Includes admin tools for managing and processing commission payments
* Supports manual adjustments and flexible configuration

Main Features:
--------------
* Multi-level commission calculation (3 hierarchy levels)
* Automatic commission creation when invoices are paid
* Commission claims and approval workflow
* Payment tracking and history
* Role-based commission percentages
* Integration with Odoo's existing commission and sales modules
    """,

    'author': "Belgogreen",
    'website': "https://www.belgogreen.com",

    'category': 'Sales/Sales',
    'version': '18.0.1.0',
    'license': 'LGPL-3',

    # Dependencies - require Odoo sale_commission module
    'depends': [
        'base',
        'sale_management',
        'account',
        'hr',
        'mail',
        'sale_commission',  # Odoo's commission module
    ],

    # always loaded
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/cron_data.xml',
        'views/hr_commission_role_config_views.xml',
        'views/sale_commission_plan_views.xml',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
        'views/sale_commission_payment_views.xml',  # Must load BEFORE sale_commission_views
        'views/sale_commission_claim_views.xml',
        'views/sale_commission_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

