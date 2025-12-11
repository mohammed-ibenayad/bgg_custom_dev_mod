# BelGoGreen Automation Rules Implementation

## Overview

This document provides a comprehensive overview of the automation rules migrated from Odoo Studio to the `bgg_custom_dev` module. All rules maintain the same business logic while implementing an optimized logging strategy for better debugging and monitoring.

## Module Structure

```
bgg_custom_dev/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── appointment_automation_rules.xml
│   ├── calendar_automation_rules.xml
│   ├── activity_automation_rules.xml
│   └── project_automation_rules.xml
├── models/
│   └── __init__.py
├── views/
│   └── menu_views.xml
└── security/
```

## Automation Rules by Category

### 1. Appointment Automations (appointment_automation_rules.xml)

#### 1.1 Add conjoint as Contact
- **Trigger**: On create/edit Appointment Answer Inputs
- **Purpose**: Creates or updates spouse contact records based on appointment questionnaire answers
- **Logic**:
  - Detects "Nom du conjoint" and "Numéro de téléphone du conjoint" questions
  - Creates new spouse as child contact (parent_id) of main partner
  - Updates existing spouse if already exists
  - Uses `mail_create_nosubscribe=True` and `tracking_disable=True` to avoid notifications

#### 1.2 Update Contact Info
- **Trigger**: On create/edit Appointment Answer Inputs
- **Purpose**: Updates partner address information from appointment answers
- **Fields Updated**:
  - Street (Adresse)
  - Zip Code (Code Postale)
  - City (Ville)
  - Country (Pays) - uses fuzzy matching with `=ilike`
- **Logging**: Warns when country cannot be matched

#### 1.3 Update Appointment Title
- **Trigger**: On create/edit Appointment Answer Inputs
- **Purpose**: Builds comprehensive appointment title from multiple sources
- **Format**: `[SMS Icon]/Client Name/Postal Code/Phone/Need/Seller`
- **Features**:
  - Adds 📞 icon if SMS confirmation is "Oui"
  - Parses existing title to preserve unchanged parts
  - Handles multiple "Besoin" answers with '+' separator

#### 1.4 Set Clickable Customer Phone
- **Trigger**: On create/edit Appointment Answer Inputs
- **Purpose**: Creates clickable tel: link for customer phone
- **Implementation**:
  - Extracts phone from partner record
  - Cleans phone (removes non-digits except '+')
  - Creates HTML link: `<a href="tel:{clean_phone}">{partner_phone}</a>`
  - Stores in `x_studio_customer_phone` field

#### 1.5 Set Partner On Behalf
- **Trigger**: On create/edit Appointment Answer Inputs
- **Purpose**: Sets "Rendez-vous pris à la place de" field for call center tracking
- **Logic**:
  - Only matches partners with "Call Center" category tag
  - Uses strict matching (`name =ilike` + category filter)
  - Warns when partner not found
  - Clears field if no answer provided

### 2. Calendar Event Automations (calendar_automation_rules.xml)

#### 2.1 Update Calendar Event Organizer
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Sets organizer to currently connected user
- **Safety**: Only updates if user is not public (`user._is_public()`)

#### 2.2 Update Calendar Status When Rescheduled
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Cleans up NoShow activities when event is rescheduled
- **Actions**:
  - Finds and deletes incomplete NoShow activities
  - Posts chatter note as OdooBot with reschedule information
  - Uses `sudo()` for message posting

#### 2.3 Set Clickable Customer Address
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Creates Google Maps clickable link from appointment answers
- **Implementation**:
  - Gathers address components from appointment answers
  - Builds formatted address string
  - Creates Google Maps search URL with encoded address
  - Stores as HTML link in `x_studio_customer_address`

#### 2.4 Update Clickable Address & Phone from Client Attendee
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Syncs contact info from client (non-internal) attendee
- **Logic**:
  - Identifies client attendee (partner without internal user)
  - Extracts address from partner fields (street, street2, zip, city, country)
  - Extracts phone from partner
  - Creates clickable links and updates custom fields

#### 2.5 Replace Call Center Emails
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Prevents internal user emails from being exposed to customers
- **Logic**:
  - Collects all internal user emails (from `res.users` where `share=False`)
  - Scans customer attendees (non-internal partners)
  - Replaces any customer email matching internal user email with standard call center email
  - Standard email: `rdvcallbgg@gmail.com`
- **Safety**: Skips internal user attendees (organizers)

#### 2.6 Assign Existing Customer To Calendar Event and Opportunity
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Finds existing customers by phone and prevents duplicates
- **Logic**:
  - Extracts phone from custom field or partner
  - Searches by last 8 digits of phone number
  - Filters out internal users
  - Selects oldest customer (by create_date) as primary
  - Adds customer as attendee if not already present
  - Updates linked opportunities
  - Identifies and removes duplicate customer records (if safe)
- **Safety Checks Before Deletion**:
  - Not linked to other events
  - Not attendee of other events
  - Not linked to other opportunities

### 3. Activity Automations (activity_automation_rules.xml)

#### 3.1 Add Tag on Activity Completion
- **Trigger**: On create/edit Activity
- **Purpose**: Tags calendar event when "Call2" activity is completed
- **Logic**:
  - Checks if activity type is "Call2" and state is "done"
  - Creates "Call2" tag if doesn't exist
  - Adds tag to linked calendar event
  - Avoids duplicate tags

#### 3.2 Create activity for NoShow
- **Trigger**: On create/edit Calendar Event
- **Purpose**: Creates NoShow activity when appointment status is no_show
- **Logic**:
  - Checks for existing NoShow activity (updates if exists)
  - Assigns to event organizer or current user (not public)
  - Sets deadline to today
  - Summary format: "NoShow: {event_name}"

### 4. Project Automations (project_automation_rules.xml)

#### 4.1 Update Project Folder Name
- **Trigger**: On create/edit Project
- **Purpose**: Renames document folder based on sales order and customer
- **Format**: `{SO Name} - Projet - {Customer Name}`
- **Condition**: Only processes new projects (create_date == write_date)

#### 4.2 Set Welcome Call Deadline
- **Trigger**: On create/edit Task
- **Purpose**: Sets deadline for "Welcom call" task
- **Logic**:
  - Checks task name (exact match: "Welcom call")
  - Gets sales order date from `project_sale_order_id`
  - Sets deadline to order_date + 2 days
- **Note**: Uses exact spelling "Welcom call" (not "Welcome")

#### 4.3 Subscribe Admins to FSM Tasks
- **Status**: Placeholder - no code provided in migration document
- **Implementation**: Pending future requirements

## Logging Strategy

### Logging Levels

#### ERROR (_logger.error)
- **Usage**: Exceptions and critical errors
- **Includes**: Full stack trace with `exc_info=True`
- **Examples**:
  - Database write failures
  - Unexpected exceptions in try/except blocks
  - Record ID and error message always included

#### WARNING (_logger.warning)
- **Usage**: Issues that don't break flow but need attention
- **Examples**:
  - Country not found during address update
  - Partner not found when setting "on behalf" field
  - NoShow activity type missing
  - Duplicate deletion failed (used elsewhere)
  - Phone number too short (< 8 digits)

#### INFO (_logger.info)
- **Usage**: Successful operations and important state changes
- **Examples**:
  - Record created/updated with key details
  - Field values changed
  - Customer matched and assigned
  - Duplicate records cleaned up
  - Activity created/completed

### Debug Logging

Additional debug logs have been added for:
- Phone number searching (last 8 digits)
- Customer matching process
- Partner category filtering
- Email replacement logic
- Address component extraction
- Duplicate detection and cleanup

### Log Message Format

All log messages follow this format:
```python
_logger.level("Rule Name - Description: record ID %s, details: %s", record.id, details)
```

Key principles:
- **Always include record ID** for traceability
- **Use descriptive messages** explaining what happened
- **Include relevant data** (names, IDs, field values)
- **Avoid sensitive data** (passwords, tokens, etc.)

## Testing Recommendations

### 1. Appointment Flow
- Create appointment with spouse information
- Verify spouse contact created as child
- Update spouse phone and verify update
- Check appointment title formatting
- Verify clickable phone and address links

### 2. Calendar Event Flow
- Create event as non-public user, verify organizer set
- Set event to no_show, verify NoShow activity created
- Reschedule event, verify NoShow activity deleted
- Add attendee with internal user email, verify replacement

### 3. Customer Deduplication
- Create multiple customers with same phone
- Create calendar event with that phone
- Verify oldest customer assigned
- Verify duplicates removed (if safe)

### 4. Activity Flow
- Create Call2 activity on calendar event
- Mark as done
- Verify Call2 tag added to event

### 5. Project Flow
- Create project from template with sales order
- Verify folder renamed
- Create "Welcom call" task
- Verify deadline set to order_date + 2 days

## Installation

1. Copy the module to your Odoo addons directory
2. Update the app list
3. Install the module "BelGoGreen Custom Development"
4. Verify all automation rules are active in Settings > Technical > Automation Rules

## Dependencies

Required Odoo modules:
- `base` - Core functionality
- `mail` - Activities and messaging
- `calendar` - Calendar events
- `appointment` - Appointment management
- `crm` - Opportunities
- `project` - Projects and tasks
- `documents` - Document management
- `sale_project` - Sales order integration with projects

## Upgrade from Studio

If migrating from Odoo Studio automation rules:

1. **Backup your database** before installation
2. **Disable Studio automation rules** after installing this module
3. **Do not delete Studio rules immediately** - keep for reference during testing
4. **Test thoroughly** in a staging environment first
5. **Monitor logs** during first weeks for any issues

## Troubleshooting

### Common Issues

1. **Country not matching**
   - Check country names in appointment questions
   - Verify `res.country` records
   - Look for warning logs with country name

2. **Spouse not created**
   - Verify question display names are exact: "Nom du conjoint", "Numéro de téléphone du conjoint"
   - Check if record is new (create_date == write_date)

3. **NoShow activity not created**
   - Verify activity type "NoShow" exists
   - Check if user assignment is valid (not public)

4. **Customer not matched by phone**
   - Verify phone has at least 8 digits
   - Check log for search pattern (last 8 digits)
   - Ensure customer is not an internal user

5. **Folder not renamed**
   - Verify project has `sale_line_id`
   - Check if project has `documents_folder_id`
   - Only works on new projects (create_date == write_date)

### Log Filtering

To find logs for specific automation rules in Odoo:
```
Settings > Technical > Logging
Filter by: name contains "Add conjoint" (or other rule name)
```

Or via command line:
```bash
grep "Add conjoint as Contact" /var/log/odoo/odoo.log
```

## Future Enhancements

Potential improvements for consideration:

1. **Performance Optimization**
   - Add conditions to trigger only when relevant fields change
   - Use `@api.model_create_multi` for batch operations

2. **Enhanced Deduplication**
   - Merge duplicate partner data before deletion
   - Check more relationships before deleting

3. **Configuration Options**
   - Make call center email configurable
   - Allow customization of question display names
   - Configurable deadline offset for Welcome call

4. **Additional Logging**
   - Performance metrics (execution time)
   - Statistics dashboard
   - Email alerts for repeated errors

## Support

For issues or questions:
1. Check log files for detailed error messages
2. Review this documentation
3. Contact the development team with:
   - Record ID where issue occurred
   - Relevant log entries
   - Steps to reproduce

## Changelog

### Version 19.0.1.0.0 (Initial Release)
- Migrated 15 automation rules from Odoo Studio
- Implemented optimized logging strategy
- Added comprehensive documentation
- Ready for Odoo 19
