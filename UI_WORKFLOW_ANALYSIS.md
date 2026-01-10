# UI Workflow Analysis: Appointment Booking Flow

**Production Case**: appointment_type_id = 2 (APT-ENERG-CNT)
**User**: Corine Detilleux
**Date**: 2026-01-06 13:25:24

---

## Complete User Journey (UI Flow)

### Phase 1: User Starts Appointment Booking

**What the user sees:**

```
┌─────────────────────────────────────────────────────┐
│  Odoo Appointment Booking Page                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Select Appointment Type:                           │
│  [x] APT-ENERG-CNT (Energie - Call Center)  ←─────┐ │
│  [ ] APT-ENERG-COM (Energie - Commercial)         │ │
│  [ ] APT-NISOL-CNT (Isolation - Call Center)      │ │
│  [ ] APT-NISOL-COM (Isolation - Commercial)       │ │
│                                                    │ │
│  Select Date & Time:                               │ │
│  📅 2026-01-12   🕐 13:00 - 15:00                 │ │
│                                                    │ │
│  [Continue] ────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**User action**: Selects appointment type = 2 and time slot

---

### Phase 2: Customer Information Form

**What the user sees:**

```
┌─────────────────────────────────────────────────────┐
│  Customer Details                                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Name: [DELESTRAIT Chantal                    ]     │
│  Phone: [+32 71 77 36 45                      ]     │
│  Email: [                                      ]     │
│                                                      │
│  Address: [                                    ]     │
│  Postal Code: [                                ]     │
│  City: [                                       ]     │
│  Country: [Belgium ▼]                               │
│                                                      │
│  Additional Questions:                              │
│  Besoin (Need): [Pompe à chaleur ▼]                │
│  Nom du conjoint: [                            ]     │
│  Confirmation par SMS: (•) Oui  ( ) Non            │
│                                                      │
│  [Submit Booking] ───────────────────────────────┐  │
└─────────────────────────────────────────────────│───┘
                                                   │
                                                   ↓
```

**User action**: Fills in customer details and clicks "Submit Booking"

---

### Phase 3: Backend Processing (Where Bug Occurs)

#### Step 3.1: Odoo Appointment Module Creates Calendar Event

**What happens in the backend:**

```python
# Standard Odoo appointment module code (not in this repo)
# Location: addons/appointment/models/calendar_event.py (Odoo core)

def _create_calendar_event_from_booking(self, booking_data):
    """
    Standard Odoo appointment module creates the calendar event
    """
    vals = {
        'appointment_type_id': 2,  # APT-ENERG-CNT
        'start': '2026-01-12 13:00:00',
        'stop': '2026-01-12 15:00:00',
        'appointment_status': 'booked',
        'res_model': 'res.partner',
        'res_id': 11883,  # DELESTRAIT Chantal
        'description': '''
            <div>
                <strong>Organisé par</strong><br>
                Corine Detilleux<br>
                <a href="mailto:corine.detilleux@belgogreen.be">
                    corine.detilleux@belgogreen.be
                </a><br><br>
                <strong>Détails du contact</strong><br>
                DELESTRAIT Chantal<br>
                <a href="tel:+32%2071%2077%2036%2045">+32 71 77 36 45</a>
            </div>
        ''',
        # ❌ NOTE: 'name' field is NOT provided!
        # Odoo appointment module expects it to be set later
    }

    # This calls our custom module's create() override
    event = self.env['calendar.event'].create(vals)
    return event
```

**Data being passed to create():**

| Field | Value | Status |
|-------|-------|--------|
| `appointment_type_id` | 2 | ✅ Provided |
| `start` | 2026-01-12 13:00:00 | ✅ Provided |
| `stop` | 2026-01-12 15:00:00 | ✅ Provided |
| `appointment_status` | 'booked' | ✅ Provided |
| `res_model` | 'res.partner' | ✅ Provided |
| `res_id` | 11883 | ✅ Provided |
| `description` | HTML content | ✅ Provided |
| **`name`** | **NULL** | ❌ **NOT PROVIDED** |

---

#### Step 3.2: Custom Module's create() Override

**File**: `bgg_custom_dev/models/calendar_event.py:43-55`

```python
@api.model_create_multi
def create(self, vals_list):
    """Override create to set organizer and trigger automation rules"""

    # vals_list[0] = {
    #     'appointment_type_id': 2,
    #     'start': '2026-01-12 13:00:00',
    #     ...
    #     # 'name': NOT IN DICT! ❌
    # }

    # ❌ PROBLEM: No check for missing name!
    # Should be:
    # for vals in vals_list:
    #     if not vals.get('name'):
    #         vals['name'] = 'Rendez-vous (Etude)'

    # This tries to INSERT with name=NULL
    records = super(CalendarEvent, self).create(vals_list)  # ← FAILS HERE!

    # Never reaches this code:
    for record in records:
        self._set_initial_organizer(record)
        self._process_calendar_event(record)

    return records
```

---

#### Step 3.3: Database Rejects the INSERT

**PostgreSQL Database:**

```sql
-- SQL generated by Odoo ORM
INSERT INTO "calendar_event" (
    "access_token",
    "active",
    "allday",
    "appointment_status",
    "appointment_type_id",
    "create_date",
    "create_uid",
    "description",
    "follow_recurrence",
    "name",              ← Column has NOT NULL constraint
    "recurrence_id",
    "res_id",
    "res_model",
    "res_model_id",
    "show_as",
    "start",
    "stop",
    "stop_date",
    "user_id",
    "videocall_location",
    "write_date",
    "write_uid",
    "x_studio_customer_address",
    "x_studio_customer_phone",
    "x_studio_rendez_vous_pris_la_place_de"
) VALUES (
    '3589a310-62bd-43e2-9a60-22a66764e011',
    true,
    false,
    'booked',
    2,
    '2026-01-06T13:25:24.587029'::timestamp,
    7,
    '<div><strong>Organisé par</strong>...',
    false,
    NULL,                ← ❌ NULL value violates constraint!
    NULL,
    11883,
    'res.partner',
    87,
    'busy',
    '2026-01-12T13:00:00'::timestamp,
    '2026-01-12T15:00:00'::timestamp,
    NULL,
    11,
    NULL,
    '2026-01-06T13:25:24.587029'::timestamp,
    7,
    NULL,
    NULL,
    NULL
) RETURNING "id";

-- PostgreSQL Response:
-- ERROR: null value in column "name" of relation "calendar_event"
--        violates not-null constraint
-- DETAIL: Failing row contains (23255, 11, null, 11883, ...)
```

---

#### Step 3.4: Transaction Rollback

```
┌─────────────────────────────────────────────────────┐
│  ❌ DATABASE TRANSACTION ROLLED BACK                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  - Calendar event NOT created                       │
│  - Appointment answers NOT created                  │
│  - Customer sees error in UI                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

### Phase 4: What User Sees (Error State)

**User's browser shows:**

```
┌─────────────────────────────────────────────────────┐
│  ❌ Error Creating Appointment                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  L'opération ne peut pas être terminée :            │
│  Missing required value for the field               │
│  'Sujet du rendez-vous' (name).                     │
│                                                      │
│  Model: 'Événement calendrier' (calendar.event)     │
│  - create/update: a mandatory field is not set      │
│                                                      │
│  [Try Again]                                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Production evidence**: User Corine Detilleux tried 3 times within 18 seconds:
- Attempt 1: 13:25:24 ❌
- Attempt 2: 13:25:36 ❌  (12 seconds later)
- Attempt 3: 13:25:41 ❌  (5 seconds later)

All failed with identical error.

---

## What SHOULD Happen (If Bug Fixed)

### Fixed Flow:

```
┌─────────────────────────────────────────────────────┐
│  Step 3.2: Custom create() with FIX                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  @api.model_create_multi                            │
│  def create(self, vals_list):                       │
│      # ✅ FIX: Set default name                     │
│      for vals in vals_list:                         │
│          if not vals.get('name'):                   │
│              vals['name'] = 'Rendez-vous (Etude)'   │
│                                                      │
│      records = super().create(vals_list) ✓         │
│      # ... automation runs ...                      │
│                                                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 3.3: Database INSERT succeeds ✓                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  INSERT INTO calendar_event (                       │
│      ...,                                           │
│      name,  ← 'Rendez-vous (Etude)' ✓              │
│      ...                                            │
│  )                                                  │
│                                                      │
│  ✓ Event created with ID 23255                     │
│                                                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 4: Appointment Answers Created                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  For each question answered:                        │
│  - Besoin: Pompe à chaleur                         │
│  - SMS confirmation: Oui                            │
│  - Postal Code: (from form)                        │
│                                                      │
│  ✓ appointment.answer.input records created        │
│                                                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 5: Title Builder Runs                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  _update_appointment_title() executes:              │
│                                                      │
│  1. Checks x_appointment_ref ✓                     │
│  2. Builds title from answers:                      │
│     📞DELESTRAIT Chantal/1000/+32 71 77 36 45/     │
│     Pompe à chaleur/Corine Detilleux               │
│                                                      │
│  3. Updates event name:                             │
│     'Rendez-vous (Etude)' →                        │
│     '📞DELESTRAIT Chantal/1000/...'                │
│                                                      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  ✓ SUCCESS: User sees confirmation                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Your appointment has been booked!                  │
│                                                      │
│  📅 Date: Sunday, January 12, 2026                  │
│  🕐 Time: 13:00 - 15:00                            │
│  📍 With: Corine Detilleux                         │
│                                                      │
│  Confirmation email sent to your inbox.             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Why appointment_type_id = 2 Specifically?

### Investigation Needed in Production Database:

```sql
-- Check appointment type configuration
SELECT
    id,
    name,
    x_appointment_ref
FROM appointment_type
WHERE id = 2;
```

### Possible Results:

**Scenario A**: x_appointment_ref is NULL
```
 id |           name            | x_appointment_ref
----+---------------------------+-------------------
  2 | Energie - Call Center     | NULL              ← PROBLEM!
```

**Scenario B**: x_appointment_ref is set but wrong
```
 id |           name            | x_appointment_ref
----+---------------------------+-------------------
  2 | Energie - Call Center     | APT-WRONG-TYPE    ← Not in allowed list!
```

**Scenario C**: x_appointment_ref is correct
```
 id |           name            | x_appointment_ref
----+---------------------------+-------------------
  2 | Energie - Call Center     | APT-ENERG-CNT     ← Should work, but...
```

If Scenario C, then the bug is purely the missing default name in create().

---

## Data Flow Diagram

```
┌──────────────┐
│  Web Browser │
│  (User UI)   │
└──────┬───────┘
       │ User clicks "Submit Booking"
       ↓
┌──────────────────────────────────────────┐
│  Odoo Appointment Module (Standard)      │
│  Creates booking data from form          │
└──────┬───────────────────────────────────┘
       │ Calls calendar.event.create(vals)
       │ vals['name'] = NULL ❌
       ↓
┌──────────────────────────────────────────┐
│  bgg_custom_dev CalendarEvent.create()   │
│  ❌ Doesn't set default name             │
└──────┬───────────────────────────────────┘
       │ Calls super().create(vals_list)
       ↓
┌──────────────────────────────────────────┐
│  Odoo ORM                                 │
│  Generates SQL INSERT with name=NULL     │
└──────┬───────────────────────────────────┘
       │ Executes SQL
       ↓
┌──────────────────────────────────────────┐
│  PostgreSQL Database                      │
│  ❌ CONSTRAINT VIOLATION!                 │
│  Rejects INSERT - name cannot be NULL    │
└──────┬───────────────────────────────────┘
       │ Raises IntegrityError
       ↓
┌──────────────────────────────────────────┐
│  Transaction Rolled Back                  │
│  - Event NOT created                      │
│  - Answers NOT created                    │
└──────┬───────────────────────────────────┘
       │ Error returned to UI
       ↓
┌──────────────────────────────────────────┐
│  User Sees Error Message                  │
│  "Missing required value for field name" │
└───────────────────────────────────────────┘
```

---

## Key Insights

### 1. **Why Description is Populated but Name is Not**

The Odoo appointment module explicitly builds the `description` field with organizer and contact details, but **assumes the name will be set later** through:
- Default values
- Computed fields
- Post-processing logic

### 2. **Why the Bug Only Affects Certain Appointment Types**

The custom module's `_update_appointment_title()` only runs for appointment types with valid `x_appointment_ref` values. If appointment_type_id = 2 doesn't have this configured correctly, the title never gets set.

### 3. **Timing is Critical**

The sequence is:
1. Calendar event INSERT (needs name NOW)
2. Event creation fails ❌
3. Appointment answers never created
4. Title builder never runs

There's no opportunity for post-processing to fix the name because the INSERT fails immediately.

---

## Files to Check

| What to Check | Where | Why |
|---------------|-------|-----|
| appointment_type_id = 2 config | Production database | Verify x_appointment_ref is set correctly |
| Allowed refs list | `appointment_answer_input.py:9-10` | Confirm APT-ENERG-CNT is in list |
| Create method | `calendar_event.py:43-55` | Add default name fix |
| Title builder | `appointment_answer_input.py:180-266` | Understand what name should be |

---

## Recommended Next Steps

1. ✅ Bug reproduced (done)
2. ⏳ Check production appointment_type_id = 2 configuration
3. ⏳ Implement fix (add default name in create())
4. ⏳ Test with real appointment booking flow
5. ⏳ Deploy and monitor

---

**Document Complete** ✅
