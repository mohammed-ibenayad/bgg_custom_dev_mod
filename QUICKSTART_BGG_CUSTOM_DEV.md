# Quick Start: bgg_custom_dev Module Setup

Complete setup in 10 minutes! 🚀

## Prerequisites

- Git Bash installed on Windows
- GitHub account with access to mohammed-ibenayad organization
- Access to bsimprovement/belgogreen upstream repository

## 5-Step Setup Process

### Step 1: Create GitHub Repository (2 min)

1. Go to https://github.com/new
2. Repository name: `belgogreen_bgg_custom_dev_mod`
3. Description: "Custom development module for BelGoGreen - Odoo 19"
4. Private repository
5. **DO NOT** initialize with README
6. Click "Create repository"

### Step 2: Set Up Local Directory (1 min)

Open Git Bash and run these commands:

```bash
cd /c/Users/mayad/mytools/
mkdir belgogreen_bgg_custom_dev
cd belgogreen_bgg_custom_dev
git init
git remote add origin https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git
git remote add upstream https://github.com/bsimprovement/belgogreen.git
```

### Step 3: Fetch from Upstream (1 min)

```bash
# Fetch the upstream branch
git fetch upstream bgg_custom_dev

# Check if branch has content
git ls-tree -r upstream/bgg_custom_dev

# If it has content, create main from it:
git checkout -b main upstream/bgg_custom_dev

# If it's empty, create a new main branch:
git checkout -b main
```

### Step 4: Create Module Structure (2 min)

```bash
# Copy the setup script from sales commission module
cp ../belgogreen/setup_new_module.sh .
chmod +x setup_new_module.sh

# Run the script to create module structure
./setup_new_module.sh
```

**What this creates:**
- `bgg_custom_dev/` - Complete Odoo 19 module structure
- `README.md` - Module documentation
- `.gitignore` - Git ignore rules

### Step 5: Commit and Push (2 min)

```bash
# Copy deploy script
cp ../belgogreen/deploy_module.sh .
chmod +x deploy_module.sh

# Stage all files
git add .

# Commit
git commit -m "Initial commit: bgg_custom_dev module for Odoo 19

- Complete module structure
- Manifest configured for Odoo 19.0.0.0
- Basic menu and security files
- Deploy script for automated deployment"

# Push to your fork
git push -u origin main

# Optional: Push to upstream (if you have permissions)
git push upstream main:bgg_custom_dev
```

## Verify Setup

Run these commands to verify everything is correct:

```bash
# Check remotes
git remote -v

# Check branches
git branch -a

# Check module structure
ls -la bgg_custom_dev/

# Verify manifest
python -m py_compile bgg_custom_dev/__manifest__.py
```

## What You Have Now

```
belgogreen_bgg_custom_dev/
├── bgg_custom_dev/              ← Your Odoo module
│   ├── __init__.py
│   ├── __manifest__.py          ← Version: 19.0.0.0
│   ├── models/
│   ├── views/
│   ├── security/
│   ├── data/
│   └── static/
├── deploy_module.sh             ← Auto-deploy script
├── README.md
└── .gitignore

Remotes:
✓ origin  → mohammed-ibenayad/belgogreen_bgg_custom_dev_mod
✓ upstream → bsimprovement/belgogreen (branch: bgg_custom_dev)
```

## Development Workflow

### Making Changes

```bash
# 1. Make your changes
# 2. Test locally (if you have Odoo)
# 3. Commit
git add .
git commit -m "Add feature X"
git push origin main
```

### Deploying Claude Branches

When Claude creates a branch (e.g., `claude/feature-abc`):

```bash
./deploy_module.sh
# Enter: claude/feature-abc
# Choose: yes to push to upstream
```

The script automatically:
- Detects module name: `bgg_custom_dev`
- Merges to main
- Pushes to origin/main
- Pushes to upstream/bgg_custom_dev

## Troubleshooting

**Problem:** "fatal: not a git repository"
```bash
# Make sure you're in the right directory
cd /c/Users/mayad/mytools/belgogreen_bgg_custom_dev
```

**Problem:** "permission denied" when pushing to upstream
```bash
# Only push to origin if you don't have upstream access
git push origin main
# Then create a PR manually
```

**Problem:** Script doesn't execute
```bash
# Make it executable
chmod +x deploy_module.sh
chmod +x setup_new_module.sh
```

## Next Steps

1. ✅ Module structure created
2. ✅ Git remotes configured
3. ✅ Pushed to origin and upstream
4. 📝 Start developing your features!
5. 🚀 Use `deploy_module.sh` for deployment

## Helpful Commands

```bash
# Check current status
git status

# See all branches
git branch -a

# See recent commits
git log --oneline -5

# Test deploy script (dry run - choose 'no' when asked)
./deploy_module.sh

# Update from upstream
git fetch upstream bgg_custom_dev
git merge upstream/bgg_custom_dev
```

## Module Customization

Edit these files to customize your module:

1. **`bgg_custom_dev/__manifest__.py`**
   - Update dependencies
   - Add data files
   - Configure assets

2. **`bgg_custom_dev/models/`**
   - Add your Python models
   - Update `__init__.py` to import them

3. **`bgg_custom_dev/views/`**
   - Add XML views
   - Add menu items

4. **`bgg_custom_dev/security/ir.model.access.csv`**
   - Define access rights

## Resources

- Full Guide: See `SETUP_BGG_CUSTOM_DEV.md`
- Multi-Module Setup: See `MODULE_SETUP_GUIDE.md`
- Deploy Script: See `deploy_module.sh`
- Odoo 19 Docs: https://www.odoo.com/documentation/19.0/

---

**Total Time:** ~10 minutes
**Result:** Production-ready Odoo 19 module with automated deployment! 🎉
