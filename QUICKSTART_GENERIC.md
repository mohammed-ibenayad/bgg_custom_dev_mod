# Quick Start: New Odoo Module Setup

Complete setup for a new Odoo module in 10 minutes! 🚀

**Approach:** Separate folder for each module (Recommended)

## Prerequisites

- Git Bash installed (Windows) or terminal (Linux/Mac)
- GitHub account
- Access to upstream repository (if applicable)

## Why Separate Folders?

✅ **Clean isolation:** Each module has its own git repository
✅ **Simple git workflow:** One origin per module, no confusion
✅ **Independent history:** Changes to one module don't affect others
✅ **Deploy script works automatically:** No module selection needed
✅ **Standard practice:** Matches typical development workflows

## 5-Step Setup Process

### Step 1: Create GitHub Repository (2 min)

1. Go to https://github.com/new
2. Repository name: `[client]_[module_name]_mod`
   - Example: `acme_inventory_mod`
   - Example: `acme_hr_payroll_mod`
3. Description: "[Module description] - Odoo 19"
4. Private repository (recommended)
5. **DO NOT** initialize with README
6. Click "Create repository"

### Step 2: Set Up Local Directory (1 min)

Open terminal and create a **separate folder** for this module:

```bash
# Navigate to your projects directory
cd /path/to/your/projects/

# Create NEW separate folder for this module
# Pattern: [client]_[module_name]
mkdir acme_inventory
cd acme_inventory

# Initialize git
git init

# Add your fork as origin
git remote add origin https://github.com/YOUR_USERNAME/acme_inventory_mod.git

# If you have an upstream repository, add it
git remote add upstream https://github.com/UPSTREAM_ORG/main_repo.git

# Verify remotes
git remote -v
```

**Result:** Each module in its own folder:
```
/path/to/your/projects/
├── acme_sales/              ← Module 1
└── acme_inventory/          ← Module 2 (NEW)
```

### Step 3: Fetch from Upstream (Optional, 1 min)

If the upstream branch already exists:

```bash
# Fetch the upstream branch
git fetch upstream [module_branch_name]

# Check if branch has content
git ls-tree -r upstream/[module_branch_name]

# If it has content, create main from it:
git checkout -b main upstream/[module_branch_name]

# If it's empty or doesn't exist, create a new main branch:
git checkout -b main
```

### Step 4: Create Module Structure (2 min)

Use the setup script to create the module:

```bash
# Make sure you're in the new module folder
cd /path/to/your/projects/acme_inventory

# If you have the setup script from another module, copy it
cp ../acme_sales/setup_new_module.sh .
cp ../acme_sales/deploy_module.sh .
chmod +x setup_new_module.sh deploy_module.sh

# Edit setup_new_module.sh to customize:
# - MODULE_NAME
# - MODULE_TITLE
# - MODULE_DESCRIPTION
# - AUTHOR
# - WEBSITE

# Run the setup script to create module structure
./setup_new_module.sh
```

**What this creates:**
- `[module_name]/` - Complete Odoo 19 module structure
- `README.md` - Module documentation
- `.gitignore` - Git ignore rules
- `deploy_module.sh` - Deployment automation

### Step 5: Commit and Push (2 min)

```bash
# Stage all files
git add .

# Commit
git commit -m "Initial commit: [module_name] module for Odoo 19

- Complete module structure
- Manifest configured for Odoo 19.0.0.0
- Basic menu and security files
- Deploy script for automated deployment"

# Push to your fork
git push -u origin main

# Optional: Push to upstream (if you have permissions and upstream branch exists)
git push upstream main:[upstream_branch_name]
```

**Important:** Each module is now in its own folder with its own git repository!

## Verify Setup

Run these commands to verify everything is correct:

```bash
# Check remotes
git remote -v

# Check branches
git branch -a

# Check module structure
ls -la [module_name]/

# Verify manifest (Python syntax check)
python -m py_compile [module_name]/__manifest__.py
```

## What You Have Now

**Folder Structure:**
```
/path/to/your/projects/
├── acme_sales/                    ← Previous module
│   ├── acme_sales/                ← Odoo module
│   ├── deploy_module.sh
│   └── [git → acme_sales_mod]
│
└── acme_inventory/                ← New module
    ├── acme_inventory/            ← Odoo module
    │   ├── __init__.py
    │   ├── __manifest__.py        ← Version: 19.0.0.0
    │   ├── models/
    │   ├── views/
    │   ├── security/
    │   ├── data/
    │   └── static/
    ├── deploy_module.sh           ← Auto-deploy script
    ├── setup_new_module.sh
    ├── README.md
    └── .gitignore
```

**Git Configuration:**
```
✓ origin   → YOUR_USERNAME/acme_inventory_mod
✓ upstream → UPSTREAM_ORG/main_repo (optional)
```

## Development Workflow

### Making Changes

Each module folder works independently:

```bash
# Work on inventory module
cd /path/to/your/projects/acme_inventory
# Make changes, test, commit
git add .
git commit -m "Add feature X"
git push origin main

# Work on sales module
cd /path/to/your/projects/acme_sales
# Make changes, test, commit
git add .
git commit -m "Add feature Y"
git push origin main
```

### Deploying Claude Branches

When Claude creates a branch (e.g., `claude/feature-abc`):

```bash
# Navigate to the specific module folder
cd /path/to/your/projects/acme_inventory

# Run deploy script
./deploy_module.sh
# Enter: claude/feature-abc
# Choose: yes to push to upstream
```

The script automatically:
- Detects module name (from origin URL)
- Merges to main
- Pushes to origin/main
- Pushes to upstream (if configured)

**Key advantage:** No need to specify which module - the script knows based on the folder!

## Troubleshooting

**Problem:** "fatal: not a git repository"
```bash
# Make sure you're in the right directory
cd /path/to/your/projects/acme_inventory
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
3. ✅ Pushed to origin
4. 📝 Start developing your features!
5. 🚀 Use `deploy_module.sh` for deployment

## Module Customization

Edit these files to customize your module:

1. **`[module_name]/__manifest__.py`**
   - Update dependencies
   - Add data files
   - Configure assets

2. **`[module_name]/models/`**
   - Add your Python models
   - Update `__init__.py` to import them

3. **`[module_name]/views/`**
   - Add XML views
   - Add menu items

4. **`[module_name]/security/ir.model.access.csv`**
   - Define access rights

## Resources

- Full Guide: See `MODULE_SETUP_GUIDE.md`
- Odoo 19 Docs: https://www.odoo.com/documentation/19.0/

---

**Total Time:** ~10 minutes
**Result:** Production-ready Odoo 19 module with automated deployment! 🎉
