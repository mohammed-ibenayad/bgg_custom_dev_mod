# Multi-Module Setup Guide for Belgogreen

## Overview

This guide explains how to set up multiple Belgogreen modules where:
- **Upstream** (bsimprovement/belgogreen): Main repo with all modules on separate branches
- **Origin** (your forks): Separate GitHub repos for each module
- **Local**: Separate local folders for each module

## Current Module Structure

### Sales Commission Module (Example)
```
Local folder: ~/mytools/belgogreen/
Origin: https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git
Upstream branch: belgogreen_sales_commission
```

## Setting Up a New Module

### Step 1: Create GitHub Repository

1. Go to GitHub and create a new repository
2. Name it following the pattern: `belgogreen_[MODULE_NAME]_mod`
   - Example: `belgogreen_inventory_management_mod`
   - Example: `belgogreen_hr_payroll_mod`

### Step 2: Create Local Folder

```bash
# Navigate to your projects directory
cd ~/mytools/

# Create new folder (without _mod suffix for cleaner local path)
mkdir belgogreen_inventory_management
cd belgogreen_inventory_management

# Initialize git
git init
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

### Step 5: Copy Deploy Script

```bash
# Copy the deploy script from sales commission module
cp ~/mytools/belgogreen/deploy_module.sh .

# Make it executable
chmod +x deploy_module.sh
```

The script will automatically detect your module name from the origin URL!

## Workflow for Development

### 1. Work on Claude Branch

When Claude creates a branch (e.g., `claude/feature-xyz`):

```bash
# Claude pushes to: origin/claude/feature-xyz
git fetch origin
git checkout claude/feature-xyz
```

### 2. Deploy Using Script

```bash
./deploy_module.sh
```

The script will:
1. ✅ Auto-detect module name from origin remote
2. ✅ Ask for the Claude branch name
3. ✅ Merge it into main
4. ✅ Push to origin/main
5. ✅ Optionally push to upstream/[MODULE_BRANCH]

### 3. Manual Push (Alternative)

If you prefer manual control:

```bash
# Merge Claude branch
git checkout main
git merge claude/feature-xyz

# Push to your fork
git push origin main

# Push to upstream module branch
git push upstream main:belgogreen_inventory_management
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
