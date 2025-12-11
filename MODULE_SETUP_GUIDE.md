# Multi-Module Setup Guide for Belgogreen

## Overview

This guide explains how to set up multiple Belgogreen modules where:
- **Upstream** (bsimprovement/belgogreen): Main repo with all modules on separate branches
- **Origin** (your forks): Separate GitHub repos for each module
- **Local**: **Separate local folders for each module** ← Recommended approach

## Why Separate Folders? (Recommended)

✅ **Clean separation:** Each module has its own git repository and history
✅ **Simple git workflow:** One origin per module, no confusion about remotes
✅ **Independent development:** Changes to one module don't affect others
✅ **Deploy script works automatically:** Auto-detects module from origin URL
✅ **Standard practice:** Matches typical open-source development workflows
✅ **Easy to understand:** Each folder = one module = one git repo

## Recommended Folder Structure

```
/c/Users/mayad/mytools/
├── belgogreen/                          ← Sales commission module
│   ├── belgogreen_sales_commission/     ← Odoo module
│   ├── deploy_module.sh
│   ├── setup_new_module.sh
│   └── .git/                            ← Git repo 1
│
├── belgogreen_bgg_custom_dev/          ← Custom dev module
│   ├── bgg_custom_dev/                  ← Odoo module
│   ├── deploy_module.sh
│   ├── setup_new_module.sh
│   └── .git/                            ← Git repo 2
│
└── belgogreen_future_module/           ← Future module
    ├── future_module/                   ← Odoo module
    ├── deploy_module.sh
    └── .git/                            ← Git repo 3
```

### Example: Sales Commission Module
```
Local folder:    /c/Users/mayad/mytools/belgogreen/
Origin:          https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git
Upstream branch: belgogreen_sales_commission
```

### Example: Custom Dev Module
```
Local folder:    /c/Users/mayad/mytools/belgogreen_bgg_custom_dev/
Origin:          https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git
Upstream branch: bgg_custom_dev
```

## Setting Up a New Module

### Step 1: Create GitHub Repository

1. Go to GitHub and create a new repository
2. Name it following the pattern: `belgogreen_[MODULE_NAME]_mod`
   - Example: `belgogreen_inventory_management_mod`
   - Example: `belgogreen_hr_payroll_mod`

### Step 2: Create Separate Local Folder

**Important:** Create a NEW separate folder for each module!

```bash
# Navigate to your projects directory
cd /c/Users/mayad/mytools/

# Create new SEPARATE folder for this module
# Pattern: belgogreen_[module_name]
mkdir belgogreen_inventory_management
cd belgogreen_inventory_management

# Initialize git (this is a NEW independent git repository)
git init
```

**Result:** Each module has its own folder and git repository:
```
/c/Users/mayad/mytools/
├── belgogreen/                          ← Module 1 (separate git)
├── belgogreen_bgg_custom_dev/          ← Module 2 (separate git)
└── belgogreen_inventory_management/    ← Module 3 (separate git)
```

### Step 3: Set Up Remotes

```bash
# Add your fork as origin
git remote add origin https://github.com/mohammed-ibenayad/belgogreen_inventory_management_mod.git

# Add main Belgogreen repo as upstream
git remote add upstream https://github.com/bsimprovement/belgogreen.git

# Verify remotes
git remote -v
```

**Expected output:**
```
origin    https://github.com/mohammed-ibenayad/belgogreen_inventory_management_mod.git (fetch)
origin    https://github.com/mohammed-ibenayad/belgogreen_inventory_management_mod.git (push)
upstream  https://github.com/bsimprovement/belgogreen.git (fetch)
upstream  https://github.com/bsimprovement/belgogreen.git (push)
```

### Step 4: Set Up Initial Branch Structure

```bash
# Fetch the upstream module branch
# Replace 'belgogreen_inventory_management' with your actual upstream branch name
git fetch upstream belgogreen_inventory_management

# Create main branch from upstream module branch
git checkout -b main upstream/belgogreen_inventory_management

# Push to your origin
git push -u origin main
```

### Step 5: Copy Scripts from Existing Module

```bash
# Make sure you're in the new module folder
cd /c/Users/mayad/mytools/belgogreen_inventory_management

# Copy scripts from any existing module (e.g., sales commission)
cp ../belgogreen/deploy_module.sh .
cp ../belgogreen/setup_new_module.sh .

# Make them executable
chmod +x deploy_module.sh setup_new_module.sh

# Run the setup script to create module structure
./setup_new_module.sh
```

The deploy script will automatically detect your module name from the origin URL!

**Note:** You only need to copy these scripts once per new module. After that, they stay in that module's folder.

## Workflow for Development

**Important:** Each module folder is independent - navigate to the correct folder first!

### 1. Work on Claude Branch

When Claude creates a branch (e.g., `claude/feature-xyz`):

```bash
# Navigate to the specific module folder
cd /c/Users/mayad/mytools/belgogreen_inventory_management

# Fetch and checkout Claude's branch
git fetch origin
git checkout claude/feature-xyz

# Review changes, test, etc.
```

### 2. Deploy Using Script (Recommended)

```bash
# Make sure you're in the correct module folder
cd /c/Users/mayad/mytools/belgogreen_inventory_management

# Run the deploy script
./deploy_module.sh
```

The script will:
1. ✅ Auto-detect module name from origin URL (no manual selection needed!)
2. ✅ Ask for the Claude branch name
3. ✅ Merge it into main
4. ✅ Push to origin/main
5. ✅ Push to upstream/[MODULE_BRANCH]

### 3. Manual Push (Alternative)

If you prefer manual control:

```bash
# Navigate to module folder
cd /c/Users/mayad/mytools/belgogreen_inventory_management

# Merge Claude branch
git checkout main
git merge claude/feature-xyz

# Push to your fork
git push origin main

# Push to upstream module branch
git push upstream main:belgogreen_inventory_management
```

### 4. Working on Multiple Modules

Each module is independent:

```bash
# Work on sales commission
cd /c/Users/mayad/mytools/belgogreen
git checkout main
# make changes, commit, push

# Work on custom dev
cd /c/Users/mayad/mytools/belgogreen_bgg_custom_dev
git checkout main
# make changes, commit, push

# No conflicts, no confusion!
```

## Module Naming Convention

### Naming Pattern

| Component | Pattern | Example |
|-----------|---------|---------|
| GitHub Repo | `belgogreen_[name]_mod` | `belgogreen_sales_commission_mod` |
| Local Folder | `belgogreen_[name]` | `belgogreen_sales_commission` |
| Upstream Branch | `belgogreen_[name]` | `belgogreen_sales_commission` |

### Examples

1. **Sales Commission Module**
   - Repo: `belgogreen_sales_commission_mod`
   - Folder: `belgogreen_sales_commission`
   - Branch: `belgogreen_sales_commission`

2. **Inventory Management Module**
   - Repo: `belgogreen_inventory_management_mod`
   - Folder: `belgogreen_inventory_management`
   - Branch: `belgogreen_inventory_management`

3. **HR Payroll Module**
   - Repo: `belgogreen_hr_payroll_mod`
   - Folder: `belgogreen_hr_payroll`
   - Branch: `belgogreen_hr_payroll`

## Troubleshooting

### Script doesn't detect module name correctly

Check your origin remote:
```bash
git remote get-url origin
```

It should match: `https://github.com/[user]/belgogreen_[MODULE]_mod.git`

### Upstream push fails

1. Verify the branch exists on upstream:
   ```bash
   git ls-remote --heads upstream
   ```

2. If it doesn't exist, you need to create it on upstream first or have permissions

### Module name mismatch

The script assumes:
- Origin repo name: `belgogreen_[NAME]_mod`
- Upstream branch name: `belgogreen_[NAME]`

If your naming is different, edit the `module_name` detection in `deploy_module.sh`:

```bash
# Current auto-detection (line ~20)
module_name=$(echo "$origin_url" | sed -E 's|.*/([^/]+)\.git$|\1|' | sed 's/_mod$//')

# Or manually override:
module_name="your_upstream_branch_name"
```

## Quick Reference

### Common Commands

```bash
# Check which module you're in
git remote get-url origin

# See all remotes
git remote -v

# Fetch latest from upstream
git fetch upstream

# See what branches exist on upstream
git ls-remote --heads upstream | grep belgogreen

# Deploy a Claude branch
./deploy_module.sh
```

## Benefits of This Setup

✅ **Isolated Development**: Each module in its own repo and folder
✅ **Centralized Integration**: All modules merge to upstream branches
✅ **Automatic Detection**: Deploy script works across all modules
✅ **Clean Organization**: Clear naming convention
✅ **Flexible Workflow**: Work locally, deploy when ready

## Next Steps

1. ✅ Test the deploy script with your sales commission module
2. Create your next module following Step 1-5 above
3. Use the same deploy script for all modules (just copy it)
