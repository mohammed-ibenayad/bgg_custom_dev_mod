# Single Repository, Multiple Modules Approach

⚠️ **ADVANCED USE CASE** - For most users, **separate folders** (see `MODULE_SETUP_GUIDE.md`) is simpler and recommended.

This guide is for keeping **all your modules in one local git repository**, deploying to different upstream branches.

## ⚠️ When to Use This Approach (Advanced)

Use single repo approach ONLY if:
- You don't care about separate GitHub forks (origin repos) for each module
- You're comfortable with complex git remote management
- You want to share code/files between modules
- You understand git well enough to handle conflicts

## ✅ Recommended for Most Users: Separate Folders

**See `MODULE_SETUP_GUIDE.md` for the simpler, recommended approach.**

Benefits of separate folders:
- ✅ Each module = one folder = one git repo (simple!)
- ✅ No confusion about which module you're working on
- ✅ Deploy script works automatically
- ✅ Independent git histories
- ✅ Standard development practice

## Current Structure

```
/c/Users/mayad/mytools/belgogreen/     ← GIT ROOT
├── belgogreen_sales_commission/       ← Module 1
├── bgg_custom_dev/                    ← Module 2 (to add)
├── future_module/                     ← Module 3 (future)
├── deploy_multi_module.sh             ← NEW: Multi-module deploy
├── setup_new_module.sh
└── .git/
```

## Current Git Configuration

```bash
cd /c/Users/mayad/mytools/belgogreen
git remote -v
```

Shows:
```
origin    https://github.com/mohammed-ibenayad/belgogreen_sales_commission_mod.git
upstream  https://github.com/bsimprovement/belgogreen.git
```

## How to Add bgg_custom_dev Module

### Step 1: Create GitHub Repository (for reference/backup)

1. Go to https://github.com/new
2. Create: `belgogreen_bgg_custom_dev_mod`
3. Keep it empty for now (optional backup)

### Step 2: Create Module Structure

```bash
cd /c/Users/mayad/mytools/belgogreen

# Run the setup script
./setup_new_module.sh
```

This creates:
```
belgogreen/
├── belgogreen_sales_commission/
├── bgg_custom_dev/              ← NEW!
└── ...
```

### Step 3: Commit the New Module

```bash
# Add the new module
git add bgg_custom_dev/

# Commit
git commit -m "Add bgg_custom_dev module for Odoo 19"

# Push to main
git push origin main
```

### Step 4: Push to Upstream Branch

```bash
# Use the new multi-module deploy script
./deploy_multi_module.sh
```

The script will:
1. Show all available modules
2. Ask which one to deploy
3. Push to the correct upstream branch

Or manually:
```bash
# Push bgg_custom_dev to upstream bgg_custom_dev branch
git push upstream main:bgg_custom_dev

# Push sales commission to upstream belgogreen_sales_commission branch
git push upstream main:belgogreen_sales_commission
```

## Workflow: Working with Claude Branches

When Claude creates a branch like `claude/feature-xyz`:

```bash
# Use the multi-module deploy script
./deploy_multi_module.sh

# It will ask:
# 1. Which module? (select from list)
# 2. Which Claude branch to merge?
# 3. Push to upstream? yes
```

## Git Remote Strategy

### Option A: Keep Current Setup (Simpler)

```
origin   → belgogreen_sales_commission_mod (your main branch backup)
upstream → belgogreen.git (deploy target for all modules)
```

**Deploy flow:**
- Develop locally → Commit to main → Push to upstream/[MODULE_BRANCH]
- Origin is just for backup/sharing

### Option B: Add Module-Specific Origins (Advanced)

```bash
# Rename current origin
git remote rename origin origin-sales-commission

# Add origin for custom dev
git remote add origin-custom-dev https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git

# Result:
git remote -v
```

Shows:
```
origin-sales-commission  .../belgogreen_sales_commission_mod.git
origin-custom-dev        .../belgogreen_bgg_custom_dev_mod.git
upstream                 .../belgogreen.git
```

**Deploy flow:**
- Sales commission: `git push origin-sales-commission main && git push upstream main:belgogreen_sales_commission`
- Custom dev: `git push origin-custom-dev main && git push upstream main:bgg_custom_dev`

## File Organization

### Keep Module-Specific Files Separate

```
belgogreen/
├── belgogreen_sales_commission/
│   └── [all module files]
├── bgg_custom_dev/
│   └── [all module files]
├── deploy_multi_module.sh      ← Shared
├── setup_new_module.sh          ← Shared
├── deploy_module.sh             ← Legacy (still works for single module)
├── README.md                    ← Repository overview
└── .gitignore                   ← Shared
```

### Don't Mix Module Files

❌ **Don't do this:**
```
belgogreen/
├── models/                      ← Mixed models from both modules
├── views/                       ← Mixed views
└── __manifest__.py              ← Which module?
```

✅ **Do this:**
```
belgogreen/
├── belgogreen_sales_commission/
│   ├── models/
│   ├── views/
│   └── __manifest__.py
└── bgg_custom_dev/
    ├── models/
    ├── views/
    └── __manifest__.py
```

## Deployment Script Usage

### deploy_multi_module.sh (NEW)

Handles multiple modules in one repo:

```bash
./deploy_multi_module.sh

# Interactive prompts:
# 1. Select module (if more than one)
# 2. Enter Claude branch name (optional)
# 3. Merge and push to upstream
```

### deploy_module.sh (OLD)

Works with single module per repo:
- Only works if repo name matches pattern: `belgogreen_[MODULE]_mod`
- Auto-detects from origin URL

## Pros & Cons

### ✅ Pros of Single Repo
- All modules together locally
- One git history to manage
- Easier to share code between modules
- Less folder clutter

### ❌ Cons of Single Repo
- More complex git remote setup
- Need to track which module goes where
- Larger repository size
- Can't easily separate module ownership

## Recommendation Based on Your Workflow

Since you have:
- Upstream with separate branches per module ✓
- Need to deploy different modules independently ✓
- Working with Claude that creates feature branches ✓

**Use Single Repo with Multi-Module Deploy Script!**

## Quick Reference

```bash
# Create new module in same repo
cd /c/Users/mayad/mytools/belgogreen
./setup_new_module.sh

# Deploy any module
./deploy_multi_module.sh

# Manual push to specific upstream branch
git push upstream main:bgg_custom_dev
git push upstream main:belgogreen_sales_commission

# Check what modules are available
ls -d */  | grep -v ".git"
```

## Troubleshooting

**Problem:** "Which origin should I push to?"
**Solution:** Keep one origin for backup, push to upstream for deployment

**Problem:** "How do I know which module I'm deploying?"
**Solution:** Use `deploy_multi_module.sh` - it shows all modules and asks

**Problem:** "Can I still use deploy_module.sh?"
**Solution:** Yes, but it will try to auto-detect from origin URL (may not work with multiple modules)

## Summary

1. ✅ Keep all modules in `/c/Users/mayad/mytools/belgogreen/`
2. ✅ Each module in its own folder
3. ✅ Use `deploy_multi_module.sh` for deployment
4. ✅ Push to upstream branches: `main:bgg_custom_dev`, `main:belgogreen_sales_commission`
5. ✅ Keep git history clean and organized

This approach matches your Odoo.sh workflow and keeps everything simple! 🎉
