# Debugging Checklist for "Update Project Folder Name" Automation

## Sample Data from S00806
From your sample, the project should have:
- **Sale Order**: "S00806"
- **Customer**: "Salah Omari" (partner_id: 11474)
- **Project ID**: 1084
- **Project Name**: "S00806 - AMSS - Tâches Avant - Installation"
- **Current Folder Name**: "S00806 - AMSS - Tâches Avant - Installation"
- **Expected Folder Name**: "S00806 - Projet - Salah Omari"

---

## ✅ Checklist to Complete

### 1. Module Installation ✓
- [ ] Module `bgg_custom_dev` is installed (not just to install/upgrade)
- [ ] Module state is "installed" in Apps menu
- [ ] Server was restarted after module installation

**How to check:**
```bash
# In Odoo shell
module = env['ir.module.module'].search([('name', '=', 'bgg_custom_dev')])
print(f"Module state: {module.state}")
# Should print: "Module state: installed"
```

---

### 2. Project Has Required Fields ⚠️
The automation REQUIRES both fields to work:

- [ ] `sale_line_id` is set (must link to a sale order line)
- [ ] `documents_folder_id` is set (must have a documents folder)

**How to check:**
```python
# In Odoo shell
project = env['project.project'].search([('id', '=', 1084)], limit=1)
print(f"sale_line_id: {project.sale_line_id}")
print(f"documents_folder_id: {project.documents_folder_id}")
# Both should show values, not False
```

**Common Issue:** If the project was created from a template, was the documents folder created BEFORE or AFTER the project creation?

---

### 3. Project Creation Timestamp ⚠️
The automation ONLY runs if `create_date == write_date` (i.e., brand new record)

- [ ] Project was just created (not updated)
- [ ] No writes happened immediately after creation

**How to check:**
```python
project = env['project.project'].search([('id', '=', 1084)], limit=1)
print(f"Created: {project.create_date}")
print(f"Modified: {project.write_date}")
print(f"Same? {project.create_date == project.write_date}")
# Should print: "Same? True" for automation to trigger
```

**Common Issue:** If something else writes to the project immediately after creation (like another automation), the timestamps won't match and this rule won't trigger.

---

### 4. Automation Code is Loaded 🔍
- [ ] Python method `_update_project_folder_name` exists on project.project model
- [ ] Method is being called in the `create()` override

**How to check:**
```python
project = env['project.project'].search([], limit=1)
print(f"Method exists: {hasattr(project, '_update_project_folder_name')}")
# Should print: "Method exists: True"
```

---

### 5. Check for Errors in Logs 📋
- [ ] No Python errors in Odoo logs during project creation
- [ ] Check `ir.logging` table for automation errors

**How to check:**
```python
# Find recent logs for this module
logs = env['ir.logging'].search([
    ('name', 'ilike', 'bgg_custom_dev'),
    ('level', '=', 'ERROR'),
], order='create_date desc', limit=10)

for log in logs:
    print(f"[{log.create_date}] {log.message}")
```

---

### 6. Test Manually 🧪
Try manually triggering the automation to see if it works:

```python
# Get the project
project = env['project.project'].search([('id', '=', 1084)], limit=1)

# Manually call the automation method
project._update_project_folder_name(project)

# Check if folder name changed
print(f"Folder name: {project.documents_folder_id.name}")
# Should now be: "S00806 - Projet - Salah Omari"
```

---

## 🐛 Common Problems and Solutions

### Problem 1: `create_date != write_date`
**Symptom:** Timestamps are different
**Cause:** Another automation or process modified the project after creation
**Solution:** Remove the timestamp check or modify the logic

### Problem 2: Missing `sale_line_id`
**Symptom:** `sale_line_id` is False
**Cause:** Project not properly linked to sale order
**Solution:** Check how projects are created from sale orders in your workflow

### Problem 3: Missing `documents_folder_id`
**Symptom:** `documents_folder_id` is False
**Cause:** Documents module creates folder AFTER project creation
**Solution:** May need to add a write() override to handle delayed folder creation

### Problem 4: Multiple Writes at Creation
**Symptom:** Automation doesn't trigger even though everything looks correct
**Cause:** Odoo's `create_multi` might process records in batches
**Solution:** Check if the automation is running but folder name is already correct

---

## 🔧 Next Steps

1. Run `quick_check.py` in Odoo shell to get current state
2. Go through each checklist item above
3. Report back which items are ✅ and which are ❌
4. We'll create a fix based on what's not working
