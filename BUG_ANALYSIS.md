# Bug Analysis: NULL name Constraint Violation in calendar.event

**Date**: 2026-01-10
**Module**: bgg_custom_dev
**Severity**: HIGH
**Status**: Reproduced ✅

---

## Executive Summary

The `bgg_custom_dev` module has a critical bug where calendar events can be created without a `name` field, causing a PostgreSQL NOT NULL constraint violation. This prevents users from creating appointments in production.

---

## Production Evidence

### Error from Logs (2026-01-06 13:25:24)

```
ERROR belgogreen-main-17171228 odoo.sql_db: bad query:
INSERT INTO "calendar_event" (..., "name", ...)
VALUES (..., NULL, ...)

ERROR: null value in column "name" of relation "calendar_event"
       violates not-null constraint
```

### Affected Details
- **appointment_type_id**: 2
- **User**: Corine Detilleux (ID: 7, corine.detilleux@belgogreen.be)
- **Partner**: DELESTRAIT Chantal (ID: 11883, +32 71 77 36 45)
- **Attempts**: 3 failed attempts within 18 seconds
- **Description field**: Populated correctly
- **Name field**: NULL ❌

---

## Root Cause Analysis

### 1. Missing Default Name in `create()` Override

**File**: `bgg_custom_dev/models/calendar_event.py:43-55`

```python
@api.model_create_multi
def create(self, vals_list):
    """Override create to set organizer and trigger automation rules"""
    # ❌ PROBLEM: No default name is set here
    records = super(CalendarEvent, self).create(vals_list)

    for record in records:
        self._set_initial_organizer(record)
        self._process_calendar_event(record)

    return records
```

**Issue**: The module overrides `create()` but doesn't ensure a name is provided before calling `super().create()`. If the calling code doesn't provide a name, it remains NULL and violates the database constraint.

---

### 2. Conditional Name Population

**File**: `bgg_custom_dev/models/appointment_answer_input.py:180-266`

The `_update_appointment_title()` method is supposed to build the event name, but:

1. **Only runs for specific appointment types**:
   ```python
   if not record.calendar_event_id.appointment_type_id.x_appointment_ref:
       return  # Early exit

   if x_appointment_ref not in ALL_APPOINTMENT_REFS:
       return  # Early exit
   ```

2. **ALL_APPOINTMENT_REFS** = `['APT-ENERG-CNT', 'APT-ENERG-COM', 'APT-NISOL-CNT', 'APT-NISOL-COM']`

3. **Runs AFTER event creation**: This method is called from `appointment.answer.input.create()`, which happens AFTER the calendar event is already created.

**Issue**: If appointment_type_id = 2 doesn't have `x_appointment_ref` set or has a value not in the allowed list, the name is never set.

---

### 3. Database Constraint

Odoo's core `calendar.event` table has:
```sql
CREATE TABLE calendar_event (
    ...,
    name VARCHAR NOT NULL,
    ...
);
```

This constraint is enforced at the database level, so any INSERT with `name=NULL` will fail immediately.

---

## Reproduction Scenarios

### Scenario A: Missing `x_appointment_ref`

1. appointment_type_id = 2 has NO `x_appointment_ref` value
2. User creates appointment via booking interface
3. Odoo appointment module creates event without name
4. `bgg_custom_dev.create()` doesn't set default
5. Database INSERT fails ❌

### Scenario B: Invalid `x_appointment_ref`

1. appointment_type_id = 2 has `x_appointment_ref` NOT in allowed list
2. Event created without name
3. `_update_appointment_title()` returns early (not in allowed list)
4. Name never set
5. Database INSERT fails ❌

### Scenario C: Timing Issue

1. Calendar event INSERT happens before appointment answers submitted
2. Database rejects INSERT immediately ❌
3. Transaction rolls back
4. Appointment answers never created
5. `_update_appointment_title()` never runs

---

## Evidence in Code

### Defensive Coding for NULL Names

The module already has defensive code handling NULL names in `calendar_event.py:592`:

```python
'summary': f'NoShow: {record.name or "Rendez-vous (Etude)"}',
```

This proves the developers anticipated NULL names could occur.

---

## Test Coverage

### New Tests Added

**File**: `bgg_custom_dev/tests/test_calendar_event.py:685-744`

1. **test_create_event_without_name_should_fail()**: Reproduces the exact production error
2. **test_create_event_with_empty_name_should_fail()**: Tests edge case with empty string

### Running the Tests

```bash
# Using the reproduction script
python3 reproduce_bug.py

# Using Odoo test framework (when available)
odoo-bin -c odoo.conf -d test_db --test-enable \
  --test-tags /bgg_custom_dev:TestCalendarEvent.test_create_event_without_name_should_fail \
  --stop-after-init
```

---

## Recommended Solution

### Option 1: Add Default Name in create() ✅ RECOMMENDED

**File**: `bgg_custom_dev/models/calendar_event.py:43-55`

```python
@api.model_create_multi
def create(self, vals_list):
    """Override create to set organizer and trigger automation rules on new calendar events"""

    # ALWAYS ensure name is set - prevent NULL constraint violations
    for vals in vals_list:
        if not vals.get('name'):
            vals['name'] = 'Rendez-vous (Etude)'

    records = super(CalendarEvent, self).create(vals_list)

    for record in records:
        # Set organizer to the user who created the event
        self._set_initial_organizer(record)

        # Process other automation rules
        self._process_calendar_event(record)

    return records
```

**Advantages**:
- ✅ Prevents all NULL name scenarios
- ✅ Simple, minimal code change
- ✅ No database migration needed
- ✅ Backwards compatible
- ✅ Name can still be updated by `_update_appointment_title()` later

**Trade-offs**:
- Default name "Rendez-vous (Etude)" is temporary until appointment answers set proper title
- Adds 3 lines of code

---

### Option 2: Fix appointment_type_id = 2 Configuration

**Action**: Verify in production database

```sql
-- Check current configuration
SELECT id, name, x_appointment_ref
FROM appointment_type
WHERE id = 2;

-- If missing, set the reference
UPDATE appointment_type
SET x_appointment_ref = 'APT-ENERG-CNT'
WHERE id = 2;
```

**Advantages**:
- ✅ No code changes needed

**Trade-offs**:
- ❌ Only fixes this specific appointment type
- ❌ Doesn't prevent future occurrences
- ❌ Requires manual database update

---

### Option 3: Make Name Computation Automatic

Add a computed field with store=True:

```python
name = fields.Char(compute='_compute_name', store=True, required=True, default='Rendez-vous (Etude)')

@api.depends('partner_ids', 'appointment_type_id', ...)
def _compute_name(self):
    for record in self:
        # Build name from appointment data
        # Fall back to default if data not available
```

**Advantages**:
- ✅ Name always automatically generated
- ✅ No manual title updates needed

**Trade-offs**:
- ❌ Major refactoring required
- ❌ May conflict with existing title update logic
- ❌ Compute dependencies complex

---

## Recommendation

**Implement Option 1** (default name in create()) because:

1. **Immediate fix**: Prevents all future NULL name errors
2. **Low risk**: Minimal code change
3. **Backwards compatible**: Doesn't break existing functionality
4. **Combined with Option 2**: Also fix appointment_type_id = 2 configuration

---

## Next Steps

1. ✅ Bug reproduced successfully
2. ⏳ Implement Option 1 (add default name in create())
3. ⏳ Verify appointment_type_id = 2 has correct x_appointment_ref
4. ⏳ Run tests to verify fix
5. ⏳ Deploy to production
6. ⏳ Monitor logs for recurrence

---

## Files Modified for Bug Reproduction

- ✅ `bgg_custom_dev/tests/test_calendar_event.py` (added 2 tests)
- ✅ `reproduce_bug.py` (created analysis script)
- ✅ `BUG_ANALYSIS.md` (this document)

---

## Related Files

| File | Lines | Purpose |
|------|-------|---------|
| `bgg_custom_dev/models/calendar_event.py` | 43-55 | create() override - needs fix |
| `bgg_custom_dev/models/calendar_event.py` | 592 | Defensive NULL handling |
| `bgg_custom_dev/models/appointment_answer_input.py` | 180-266 | Title building logic |
| `bgg_custom_dev/models/appointment_type.py` | 9-13 | x_appointment_ref field |
| `bgg_custom_dev/tests/test_calendar_event.py` | 685-744 | Reproduction tests |

---

**Analysis Complete** ✅
**Ready for Fix Implementation** ⏳
