# BelGoGreen Custom Development - Python Implementation

## Overview

This module extends core Odoo models with custom business logic using **proper Python model inheritance** following Odoo development standards. All business rules maintain the same logic as the original Odoo Studio automation rules while providing better performance, maintainability, and testability.

## Why Python Model Extensions?

### ✅ Advantages Over XML Automation Rules

| Feature | Python Models | XML Automation Rules |
|---------|---------------|---------------------|
| Performance | ✅ Direct method calls | ❌ Trigger evaluation overhead |
| IDE Support | ✅ Full autocomplete & debugging | ❌ Limited (code in CDATA) |
| Testing | ✅ Unit testable | ❌ Difficult to test |
| Type Safety | ✅ Compile-time checks | ❌ Runtime only |
| Maintainability | ✅ Standard Odoo patterns | ❌ Harder to modify |
| Debugging | ✅ Standard Python debugging | ❌ Log-based only |

## Module Structure

```
bgg_custom_dev/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── appointment_answer_input.py  # 5 rules
│   ├── calendar_event.py            # 7 rules
│   ├── mail_activity.py             # 1 rule
│   ├── project_project.py           # 1 rule
│   └── project_task.py              # 1 rule
├── views/
│   └── menu_views.xml
└── security/
```

## Implementation Pattern

All models follow this pattern:

```python
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)

class MyModel(models.Model):
    _inherit = 'original.model'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create for new records"""
        records = super(MyModel, self).create(vals_list)
        for record in records:
            self._my_custom_logic(record)
        return records

    def write(self, vals):
        """Override write for updates"""
        result = super(MyModel, self).write(vals)
        for record in self:
            self._my_custom_logic(record, vals)
        return result

    def _my_custom_logic(self, record, vals=None):
        """Business logic implementation"""
        try:
            # Implementation here
            _logger.info("Success: %s", record.id)
        except Exception as e:
            _logger.error("Error: %s", str(e), exc_info=True)
```

## Business Logic by Model

### 1. Appointment Answer Input
**File**: `appointment_answer_input.py`
**Model**: `appointment.answer.input`

#### Rules Implemented:
1. **Add Conjoint as Contact** - Creates spouse contacts
2. **Update Contact Info** - Updates partner addresses
3. **Update Appointment Title** - Builds dynamic titles
4. **Set Clickable Phone** - Creates tel: links
5. **Set Partner On Behalf** - Links call center partners

### 2. Calendar Event
**File**: `calendar_event.py`
**Model**: `calendar.event`

#### Rules Implemented:
1. **Update Organizer** - Sets current user as organizer
2. **Reschedule Handler** - Clears NoShow activities
3. **Clickable Address** - Google Maps links
4. **Attendee Sync** - Syncs client info
5. **Email Protection** - Replaces internal emails
6. **Customer Assignment** - Finds by phone, deduplicates
7. **NoShow Activity** - Creates activities

### 3. Mail Activity
**File**: `mail_activity.py`
**Model**: `mail.activity`

#### Rules Implemented:
1. **Call2 Tag** - Adds tag on completion

### 4. Project & Tasks
**Files**: `project_project.py`, `project_task.py`
**Models**: `project.project`, `project.task`

#### Rules Implemented:
1. **Folder Naming** - Renames from sales orders
2. **Welcome Call Deadline** - Sets order_date + 2 days

## Logging Strategy

### Levels

- **ERROR**: Exceptions with full stack trace
- **WARNING**: Issues needing attention
- **INFO**: Successful operations

### Format

```python
_logger.level("Description: details %s", data)
```

Always includes record ID for traceability.

## Installation

```bash
# Install/upgrade module
odoo-bin -u bgg_custom_dev -d your_database

# Or via UI
Apps → Search "BelGoGreen" → Install/Upgrade
```

## Testing

### Unit Tests

```python
from odoo.tests import TransactionCase

class TestCustomLogic(TransactionCase):
    def test_my_logic(self):
        # Test implementation
        pass
```

### Manual Testing

1. Create appointment with spouse info
2. Create calendar event with phone
3. Mark Call2 activity as done
4. Create project from template

## Debugging

```bash
# View logs
tail -f /var/log/odoo/odoo.log | grep "bgg_custom_dev"

# Specific rule
tail -f /var/log/odoo/odoo.log | grep "Add conjoint"
```

## Performance

- ✅ Only executes when conditions met
- ✅ Batch processing with `@api.model_create_multi`
- ✅ Avoids unnecessary writes
- ✅ Optimized database queries

## Dependencies

- `base`, `mail`, `calendar`, `appointment`
- `crm`, `project`, `documents`, `sale_project`

## Changelog

### v19.0.1.0.0
- ✅ Python model extensions
- ✅ 15 business rules
- ✅ Comprehensive logging
- ✅ Production-ready

## Support

Contact: BelGoGreen Development Team
Website: https://www.belgogreen.com

---

**License**: LGPL-3
