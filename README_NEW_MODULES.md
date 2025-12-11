# Odoo Multi-Module Development Setup

This repository contains tools and documentation for managing multiple Odoo modules with a clean, scalable structure.

## 📚 Quick Start

**Creating a new Odoo module?** Start here:
- 📖 **[QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md)** - 10-minute setup guide for any new module

## 🎯 Recommended Approach: Separate Folders

Each Odoo module gets its own folder and git repository:

```
/path/to/your/projects/
├── client_module1/              ← Module 1 (separate git)
│   ├── module1/                 ← Odoo module
│   ├── deploy_module.sh
│   └── setup_new_module.sh
│
├── client_module2/              ← Module 2 (separate git)
│   ├── module2/                 ← Odoo module
│   ├── deploy_module.sh
│   └── setup_new_module.sh
│
└── client_module3/              ← Module 3 (separate git)
    └── ...
```

### Why Separate Folders?

✅ **Simple:** One folder = one module = one git repo
✅ **Clean:** Independent git histories, no conflicts
✅ **Automatic:** Deploy script auto-detects module from origin URL
✅ **Standard:** Typical open-source development practice
✅ **Scalable:** Easy to add/remove modules

## 📁 Repository Contents

### 🚀 Essential Files (Copy these to new modules)

1. **`setup_new_module.sh`** - Automated module scaffolding
   - Creates complete Odoo 19 module structure
   - Generates manifest, security, views
   - Customizable for any client

2. **`deploy_module.sh`** - Automated deployment
   - Auto-detects module name from git URL
   - Merges Claude/feature branches
   - Pushes to origin and upstream

3. **`deploy_multi_module.sh`** ⚠️ Advanced only
   - For single-repo, multi-module setups
   - Interactive module selection
   - Not recommended for most users

### 📖 Documentation

4. **`QUICKSTART_GENERIC.md`** ⭐ **START HERE**
   - Generic 10-minute setup guide
   - Works for any client/project
   - Copy & paste commands

5. **`MODULE_SETUP_GUIDE.md`**
   - Comprehensive setup documentation
   - Best practices and workflows
   - Troubleshooting guide

6. **Advanced/Optional:**
   - `SINGLE_REPO_APPROACH.md` - Single repo with multiple modules (advanced)
   - `MULTI_MODULE_SINGLE_REPO.md` - Detailed comparison of approaches

### 🗑️ Client-Specific Files (Examples)

These are specific to BelGoGreen client and can be used as references:
- `QUICKSTART_BGG_CUSTOM_DEV.md` - BelGoGreen custom dev module setup
- `SETUP_BGG_CUSTOM_DEV.md` - BelGoGreen-specific guide
- `README_MODULES.md` - BelGoGreen module overview
- `belgogreen_sales_commission/` - Actual module implementation

## 🛠️ How to Use This Repository

### For Creating a New Module

1. **Copy the scripts:**
   ```bash
   cp setup_new_module.sh /path/to/new/module/
   cp deploy_module.sh /path/to/new/module/
   ```

2. **Edit `setup_new_module.sh`** to customize:
   - `MODULE_NAME` - Technical name (e.g., `acme_inventory`)
   - `MODULE_TITLE` - Display name (e.g., "ACME Inventory Management")
   - `MODULE_DESCRIPTION` - What the module does
   - `AUTHOR` - Your company name
   - `WEBSITE` - Your website

3. **Run the setup:**
   ```bash
   cd /path/to/new/module/
   chmod +x setup_new_module.sh
   ./setup_new_module.sh
   ```

4. **Follow the [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md) guide**

### For Deploying Changes

```bash
cd /path/to/your/module/
./deploy_module.sh
```

The script will:
- ✅ Auto-detect module name
- ✅ Merge feature branches
- ✅ Push to origin and upstream

## 📋 Naming Conventions

### Repository Names
- Pattern: `[client]_[module_name]_mod`
- Examples: `acme_inventory_mod`, `techcorp_hr_payroll_mod`

### Local Folders
- Pattern: `[client]_[module_name]`
- Examples: `acme_inventory`, `techcorp_hr_payroll`

### Odoo Module Names
- Pattern: `[client]_[module_name]` or just `[module_name]`
- Examples: `acme_inventory`, `inventory_management`

### Upstream Branches (if applicable)
- Pattern: `[client]_[module_name]` or `[module_name]`
- Examples: `acme_inventory`, `inventory_management`

## 🔄 Typical Workflow

### 1. Initial Setup (once per module)
```bash
# Create GitHub repo
# Create local folder
# Initialize git with remotes
# Run setup script
# Commit and push
```

### 2. Development (ongoing)
```bash
cd /path/to/module/
# Make changes
git add .
git commit -m "Add feature X"
git push origin main
```

### 3. Deploying Claude Branches
```bash
cd /path/to/module/
./deploy_module.sh
# Enter Claude branch name
# Script handles merge and push
```

## 🎨 Customizing for Your Client

The `setup_new_module.sh` script can be customized per client:

```bash
# Edit these variables in setup_new_module.sh:
MODULE_NAME="clientname_modulename"      # Technical name
MODULE_TITLE="Client Module Title"      # Display name
MODULE_DESCRIPTION="What it does"        # Description
AUTHOR="Your Company"                    # Your company
WEBSITE="https://yourcompany.com"        # Website
VERSION="19.0.0.0"                       # Odoo version
```

## 🆘 Troubleshooting

### Deploy script doesn't detect module name
- Check origin URL matches pattern: `[client]_[module]_mod.git`
- Verify: `git remote get-url origin`

### Module not found by Odoo
- Check `__manifest__.py` is valid Python
- Verify module folder name matches manifest name
- Ensure module is in Odoo addons path

### Git push fails
- Check you have permissions: `git push origin main`
- For upstream: Verify branch exists and you have write access

## 📦 What's Included

### Sample Module: belgogreen_sales_commission

This repository includes a complete Odoo 19 sales commission module as a reference:
- Multi-level commission calculation
- Hierarchical visibility
- Commission claims and payments
- Full Odoo 19 compatibility

**Use it as a reference** for structure and best practices!

## 🚀 Getting Started Checklist

- [ ] Read [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md)
- [ ] Copy `setup_new_module.sh` and `deploy_module.sh`
- [ ] Customize script variables for your client
- [ ] Create GitHub repository
- [ ] Run setup script
- [ ] Commit and push
- [ ] Start developing!

## 📖 Additional Resources

- **Odoo 19 Documentation:** https://www.odoo.com/documentation/19.0/
- **Odoo Development:** https://www.odoo.com/documentation/19.0/developer.html
- **Git Best Practices:** Keep separate folders, clear commit messages

## 🤝 Contributing

When adding new modules:
1. Create separate folder following naming convention
2. Copy and customize setup/deploy scripts
3. Update documentation if adding new patterns
4. Keep generic docs generic (no client-specific content)

---

**Ready to create a new module?** → Open [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md) 🚀
