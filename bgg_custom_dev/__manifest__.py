# -*- coding: utf-8 -*-
{
    'name': 'BelGoGreen Custom Development',
    'version': '19.0.1.0.0',
    'category': 'Customizations',
    'summary': 'Custom automation rules and business logic for BelGoGreen',
    'description': """
        BelGoGreen Custom Development Module
        ====================================

        This module includes custom automation rules migrated from Odoo Studio:

        Appointment Automations:
        - Add conjoint as Contact
        - Update Contact Info
        - Update Appointment Title
        - Set Clickable Customer Phone
        - Set Partner On Behalf

        Calendar Event Automations:
        - Update Calendar Event Organizer
        - Update Calendar Status When Rescheduled
        - Set Clickable Customer Address
        - Update Clickable Address & Phone from Client Attendee
        - Replace Call Center Emails
        - Assign Existing Customer To Calendar Event and Opportunity

        Activity Automations:
        - Add Tag on Activity Completion
        - Create activity for NoShow

        Project Automations:
        - Update Project Folder Name
        - Set Welcome Call Deadline
        - Subscribe Admins to FSM Tasks
    """,
    'author': 'BelGoGreen',
    'website': 'https://www.belgogreen.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'calendar',
        'appointment',
        'crm',
        'project',
        'documents',
        'sale_project',
    ],
    'data': [
        # Security
        # 'security/ir.model.access.csv',

        # Data - Automation Rules
        'data/appointment_automation_rules.xml',
        'data/calendar_automation_rules.xml',
        'data/activity_automation_rules.xml',
        'data/project_automation_rules.xml',

        # Views
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
