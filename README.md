# Odoo Multi-Module Development Tools

This repository contains tools, scripts, and documentation for managing multiple Odoo 19 modules with a clean, scalable structure.

## 🚀 Quick Start

**Creating a new Odoo module?**
1. Read [**QUICKSTART_GENERIC.md**](QUICKSTART_GENERIC.md) for a 10-minute setup guide
2. Read [**README_NEW_MODULES.md**](README_NEW_MODULES.md) for comprehensive documentation

## 📦 What's Included

### 🛠️ Scripts (Copy to New Modules)
- `setup_new_module.sh` - Automated Odoo 19 module scaffolding
- `deploy_module.sh` - Automated deployment (auto-detects module name)
- `deploy_multi_module.sh` - Multi-module deployment (advanced use case)

### 📖 Generic Documentation (For Any Client)
- `QUICKSTART_GENERIC.md` - Quick start guide for any new module
- `README_NEW_MODULES.md` - Comprehensive setup documentation
- `MODULE_SETUP_GUIDE.md` - Detailed setup and workflow guide
- `SINGLE_REPO_APPROACH.md` - Advanced: Single repo with multiple modules
- `MULTI_MODULE_SINGLE_REPO.md` - Advanced: Comparison of approaches

### 📝 Example Module
- `belgogreen_sales_commission/` - Complete Odoo 19 sales commission module
  - Multi-level hierarchical commissions
  - Payment tracking and claims
  - Odoo 19 compatible (jsonrpc, Constraint)
  - Use as reference for structure and best practices

### 🗂️ Client-Specific Examples
- `QUICKSTART_BGG_CUSTOM_DEV.md` - BelGoGreen custom dev module setup
- `SETUP_BGG_CUSTOM_DEV.md` - BelGoGreen-specific guide
- `README_MODULES.md` - BelGoGreen module overview

## 🎯 Recommended Structure

Each module in its own folder:

```
/your/projects/
├── client_module1/           ← Separate git repo
├── client_module2/           ← Separate git repo
└── client_module3/           ← Separate git repo
```

## 📋 Documentation Guide

| File | Purpose | Audience |
|------|---------|----------|
| [README.md](README.md) | This file - overview | Everyone |
| [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md) | Quick start for new module | **START HERE** |
| [README_NEW_MODULES.md](README_NEW_MODULES.md) | Comprehensive guide | All developers |
| [MODULE_SETUP_GUIDE.md](MODULE_SETUP_GUIDE.md) | Detailed setup steps | All developers |
| [SINGLE_REPO_APPROACH.md](SINGLE_REPO_APPROACH.md) | Advanced: Single repo setup | Advanced users only |
| [QUICKSTART_BGG_CUSTOM_DEV.md](QUICKSTART_BGG_CUSTOM_DEV.md) | BelGoGreen example | Reference only |

## 🔧 Features

- ✅ **Odoo 19 Compatible:** Uses jsonrpc and Constraint (not deprecated APIs)
- ✅ **Auto-detection:** Deploy script detects module name from git URL
- ✅ **Generic:** Works for any client, not hardcoded to specific company
- ✅ **Scalable:** Clean separate-folder structure for multiple modules
- ✅ **Automated:** Scripts for scaffolding and deployment

## 🚀 Usage

### Create New Module
```bash
# 1. Copy scripts to new folder
cp setup_new_module.sh /path/to/new/module/
cp deploy_module.sh /path/to/new/module/

# 2. Edit setup_new_module.sh (customize for your client)

# 3. Run setup
cd /path/to/new/module/
./setup_new_module.sh

# 4. Follow QUICKSTART_GENERIC.md for git setup
```

### Deploy Changes
```bash
cd /path/to/your/module/
./deploy_module.sh
```

## 📚 Learn More

- [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md) - 10-minute setup guide
- [README_NEW_MODULES.md](README_NEW_MODULES.md) - Full documentation
- [Odoo 19 Documentation](https://www.odoo.com/documentation/19.0/)

---

**Ready to create a new module?** → [QUICKSTART_GENERIC.md](QUICKSTART_GENERIC.md) 🚀
