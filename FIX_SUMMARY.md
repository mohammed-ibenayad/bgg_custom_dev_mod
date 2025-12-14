# Fix for "Update Project Folder Name" Automation Rule

## Problem Identified

The automation rule was **working correctly when manually triggered** from Odoo Studio, but **not triggering automatically** during project creation. This indicates a timing/trigger condition issue.

## Root Causes

1. **Timestamp Check Too Restrictive** (`project_project.py:30`):
   ```python
   if not (record.create_date == record.write_date):
       return
   ```
   - This check exits if the record has been modified even slightly after creation
   - Other modules/processes might write to the project immediately after creation
   - This causes `write_date != create_date`, preventing the automation from running

2. **Documents Folder Created After Project**:
   - The documents folder might not exist when `create()` is called
   - If the folder is added via a later `write()`, the original automation never triggers

## Changes Made

### 1. Enhanced Logging (`project_project.py:33-78`)
Added detailed logging with `[FOLDER RENAME]` prefix to track:
- Project being processed
- Timestamps (create_date vs write_date)
- Why the automation is being skipped
- Current vs target folder names
- Success/failure of the rename operation

This helps debug issues in production by checking Odoo logs.

### 2. Added `force` Parameter (`project_project.py:22`)
```python
def _update_project_folder_name(self, record, force=False):
```
- When `force=True`, skips the timestamp check
- Allows manual triggers and write() override to work regardless of timestamps

### 3. Added `write()` Override (`project_project.py:22-33`)
```python
def write(self, vals):
    result = super(ProjectProject, self).write(vals)

    if 'documents_folder_id' in vals and vals['documents_folder_id']:
        for record in self:
            self._update_project_folder_name(record, force=True)

    return result
```
- Triggers folder rename when `documents_folder_id` is added via `write()`
- Handles cases where the folder is created AFTER the project
- Uses `force=True` to bypass timestamp check

### 4. New Test Case (`test_project_project.py:265-286`)
Added `test_folder_added_after_project_creation()` to verify:
- Projects can be created without a folder
- Folder can be added later via `write()`
- Automation triggers and renames the folder correctly

## Expected Behavior After Fix

### Scenario 1: Folder exists at creation
```python
project = env['project.project'].create({
    'sale_line_id': sale_line.id,
    'documents_folder_id': folder.id,
})
# ✅ Folder renamed via create() override
```

### Scenario 2: Folder added after creation
```python
project = env['project.project'].create({
    'sale_line_id': sale_line.id,
})
# ... later ...
project.write({'documents_folder_id': folder.id})
# ✅ Folder renamed via write() override
```

### Scenario 3: Manual trigger from Odoo Studio
```python
# When user manually triggers the automation
# ✅ Works with force=True parameter
```

## Testing Instructions

### 1. Enable Debug Logging
In Odoo configuration:
```ini
[options]
log_level = info
```

### 2. Create a New Project
Create a new project linked to a sale order and watch the logs:
```
[FOLDER RENAME] Checking project (ID 1234): Test Project
[FOLDER RENAME]   create_date: 2024-01-15 10:30:00, write_date: 2024-01-15 10:30:00
[FOLDER RENAME]   Sale Order: S00807, Customer: John Doe
[FOLDER RENAME]   Current folder: 'Test Project'
[FOLDER RENAME]   Target folder: 'S00807 - Projet - John Doe'
[FOLDER RENAME]   ✓ Updated folder name to: 'S00807 - Projet - John Doe' for project ID 1234
```

### 3. Run Unit Tests
```bash
# Run Odoo tests for the module
odoo-bin -d YOUR_DB -i bgg_custom_dev --test-enable --stop-after-init
```

## Files Modified

1. `bgg_custom_dev/models/project_project.py`
   - Added enhanced logging
   - Added `force` parameter to `_update_project_folder_name()`
   - Added `write()` override

2. `bgg_custom_dev/tests/test_project_project.py`
   - Added `test_folder_added_after_project_creation()` test
   - Updated test comments to reflect new behavior

## Next Steps

1. **Upgrade the module** in Odoo to load the changes
2. **Monitor the logs** when creating new projects
3. **Verify** that new projects have folders renamed correctly
4. **Optional**: Create a migration script to update existing projects (S00806, etc.)
