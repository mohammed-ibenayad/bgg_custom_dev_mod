# Multi-Module Single Repository Setup

This guide shows how to manage multiple Belgogreen modules in a **single local repository**, similar to Odoo.sh workflow.

## Repository Structure

```
/c/Users/mayad/mytools/belgogreen/
├── belgogreen_sales_commission/     ← Module 1
│   ├── __init__.py
│   ├── __manifest__.py
│   └── ...
├── bgg_custom_dev/                  ← Module 2
│   ├── __init__.py
│   ├── __manifest__.py
│   └── ...
├── future_module/                   ← Module 3
│   └── ...
├── deploy_module.sh                 ← Shared deployment script
├── setup_new_module.sh              ← Shared setup script
└── .git/                            ← Single git repository
```

## Current Git Configuration

Since you already have the sales commission module set up:

```bash
cd /c/Users/mayad/mytools/belgogreen
git remote -v
```

Should show:
```
origin    https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git
upstream  https://github.com/bsimprovement/belgogreen.git
```

## Problem: One Origin, Multiple Modules

**Challenge:** Your origin points to `belgogreen_sales_commission_mod`, but you want to add `bgg_custom_dev` which should go to a different origin repo.

**Solution:** Use separate remotes for each module!

## Updated Git Remote Strategy

### Step 1: Rename Current Origin

```bash
cd /c/Users/mayad/mytools/belgogreen

# Rename current origin to be module-specific
git remote rename origin origin-sales-commission

# Verify
git remote -v
```

Should show:
```
origin-sales-commission  https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git
upstream                 https://github.com/bsimprovement/belgogreen.git
```

### Step 2: Add New Remote for Custom Dev Module

```bash
# Add remote for bgg_custom_dev module
git remote add origin-custom-dev https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git

# Verify
git remote -v
```

Should show:
```
origin-sales-commission  https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git (fetch)
origin-sales-commission  https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git (push)
origin-custom-dev        https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git (fetch)
origin-custom-dev        https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git (push)
upstream                 https://github.com/bsimprovement/belgogreen.git (fetch)
upstream                 https://github.com/bsimprovement/belgogreen.git (push)
```

### Step 3: Create New Module in Same Repository

```bash
cd /c/Users/mayad/mytools/belgogreen

# Run setup script (it creates bgg_custom_dev folder here)
./setup_new_module.sh

# Verify structure
ls -la
```

Should see:
```
belgogreen_sales_commission/
bgg_custom_dev/
deploy_module.sh
setup_new_module.sh
...
```

### Step 4: Create Module-Specific Branches

Since both modules exist in one repo, use branches to manage them separately:

```bash
# Current main branch is for sales commission
git branch -m main main-sales-commission

# Create branch for custom dev module
git checkout -b main-custom-dev

# Add only the custom dev module files
git add bgg_custom_dev/
git commit -m "Initial commit: bgg_custom_dev module"

# Push to the custom dev origin
git push origin-custom-dev main-custom-dev:main

# Also push to upstream custom dev branch
git push upstream main-custom-dev:bgg_custom_dev
```

## Alternative: Simpler Approach (Recommended)

Actually, there's an even simpler way that works better:

### Keep One Main Branch, Multiple Upstream Targets

```bash
cd /c/Users/mayad/mytools/belgogreen

# Keep main branch as is
git checkout main

# Add the new module
./setup_new_module.sh

# Commit everything
git add bgg_custom_dev/
git commit -m "Add bgg_custom_dev module"

# Push to upstream (different branches)
git push upstream main:belgogreen_sales_commission  # Sales commission
git push upstream main:bgg_custom_dev              # Custom dev
```

**Issue:** This won't work well with separate GitHub forks (origin repos).

## 🎯 Best Solution: Updated Deploy Script

Let me create an updated deploy script that handles multiple modules in one repo:

```bash
# Updated deploy script will:
# 1. Ask which module you're deploying
# 2. Use the correct origin remote
# 3. Push to correct upstream branch
```

## Recommendation

Given your workflow, I recommend **keeping separate folders** for now because:

1. ✅ **Clean separation:** Each module has its own git history
2. ✅ **Simple git workflow:** No need to manage multiple remotes
3. ✅ **Works with forks:** Each origin points to its own fork
4. ✅ **Deploy script works automatically:** No need to specify which module

## If You Still Want Single Folder

Create an issue: **How to manage multiple origins in one git repo?**

The answer is: You don't. Instead, use **git submodules** or **keep separate folders**.

### Using Git Submodules (Advanced)

```bash
cd /c/Users/mayad/mytools/belgogreen

# Add custom dev as a submodule
git submodule add https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git bgg_custom_dev

# This creates:
# - bgg_custom_dev/ with its own .git
# - .gitmodules file tracking the submodule
```

But this is complex and not recommended for your use case.

## Final Recommendation: Keep Separate Folders

Stick with separate folders approach:

```
/c/Users/mayad/mytools/
├── belgogreen/                     # Sales commission
└── belgogreen_bgg_custom_dev/     # Custom dev
```

**Why?**
- Simpler git workflow
- Each module is independent
- Deploy script works automatically
- Easier to understand and maintain
- Matches standard development practices

**When to use single folder?**
- If you're not using GitHub forks (origin)
- If all modules share the same origin
- If you're working directly with upstream only

Does this make sense? Would you like me to create an updated setup that keeps everything in one folder, or stick with separate folders?
