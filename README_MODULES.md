# Belgogreen Multi-Module Development Guide

Complete guide for managing multiple Odoo modules with separate folders (recommended approach).

## 🎯 Quick Start

### For bgg_custom_dev Module

**See:** `QUICKSTART_BGG_CUSTOM_DEV.md` - Complete setup in 10 minutes!

### For Any New Module

**See:** `MODULE_SETUP_GUIDE.md` - Step-by-step instructions

---

## 📁 Recommended Structure: Separate Folders

Each module gets its own folder and git repository:

```
/c/Users/mayad/mytools/
├── belgogreen/                          ← Sales commission module
│   ├── belgogreen_sales_commission/     ← Odoo module
│   ├── deploy_module.sh                 ← Deployment script
│   ├── setup_new_module.sh
│   └── .git/                            ← Git repo 1
│
├── belgogreen_bgg_custom_dev/          ← Custom dev module
│   ├── bgg_custom_dev/                  ← Odoo module
│   ├── deploy_module.sh                 ← Deployment script
│   ├── setup_new_module.sh
│   └── .git/                            ← Git repo 2
│
└── belgogreen_[future_module]/         ← Future modules
    └── ...
```

### Why This Approach?

✅ **Simple:** Each folder = one module = one git repo
✅ **Clean:** Independent git histories, no conflicts
✅ **Automatic:** Deploy script auto-detects module from origin URL
✅ **Standard:** Matches typical open-source development
✅ **Easy:** No confusion about which module you're working on

---

## 📚 Documentation Files

### Getting Started

1. **QUICKSTART_BGG_CUSTOM_DEV.md** ⭐ **START HERE for bgg_custom_dev**
   - 10-minute setup guide
   - Copy & paste commands
   - Complete workflow

2. **MODULE_SETUP_GUIDE.md** ⭐ **General guide for any module**
   - Comprehensive step-by-step
   - Examples and troubleshooting
   - Best practices

### Scripts

3. **setup_new_module.sh**
   - Automated module scaffolding
   - Creates complete Odoo 19 structure
   - Generates manifest, security, views

4. **deploy_module.sh**
   - Automated deployment
   - Auto-detects module name
   - Merges Claude branches
   - Pushes to origin and upstream

### Advanced (Optional)

5. **SINGLE_REPO_APPROACH.md** ⚠️ Advanced only
   - Single repo with multiple modules
   - Complex git remote management
   - Not recommended for most users

6. **MULTI_MODULE_SINGLE_REPO.md** ⚠️ Advanced only
   - Detailed comparison of approaches
   - For advanced git users only

7. **deploy_multi_module.sh** ⚠️ Advanced only
   - For single repo approach
   - Interactive module selection

---

## 🚀 Common Workflows

### Creating a New Module

```bash
# 1. Create GitHub repo: belgogreen_[MODULE_NAME]_mod

# 2. Create local folder
cd /c/Users/mayad/mytools/
mkdir belgogreen_[MODULE_NAME]
cd belgogreen_[MODULE_NAME]

# 3. Initialize git and remotes
git init
git remote add origin https://github.com/mohammed-ibenayad/belgogreen_[MODULE_NAME]_mod.git
git remote add upstream https://github.com/bsimprovement/belgogreen.git

# 4. Fetch from upstream (if branch exists)
git fetch upstream [MODULE_BRANCH_NAME]
git checkout -b main upstream/[MODULE_BRANCH_NAME]

# 5. Copy scripts and create module
cp ../belgogreen/setup_new_module.sh .
cp ../belgogreen/deploy_module.sh .
chmod +x *.sh
./setup_new_module.sh

# 6. Commit and push
git add .
git commit -m "Initial commit: [MODULE_NAME] for Odoo 19"
git push -u origin main
git push upstream main:[MODULE_BRANCH_NAME]
```

### Working on Existing Module

```bash
# Navigate to module folder
cd /c/Users/mayad/mytools/belgogreen_[MODULE_NAME]

# Make changes
# ... edit files ...

# Commit and push
git add .
git commit -m "Add feature X"
git push origin main
```

### Deploying Claude Branch

```bash
# Navigate to module folder
cd /c/Users/mayad/mytools/belgogreen_[MODULE_NAME]

# Run deploy script
./deploy_module.sh

# Follow prompts:
# - Enter Claude branch name
# - Confirm upstream push
```

---

## 📊 Module Status

### Existing Modules

1. **belgogreen_sales_commission**
   - Local: `/c/Users/mayad/mytools/belgogreen/`
   - Origin: `belgogreen_sales_commission_mod`
   - Upstream: `belgogreen_sales_commission`
   - Status: ✅ Active, Odoo 19.0.0.0

2. **bgg_custom_dev**
   - Local: `/c/Users/mayad/mytools/belgogreen_bgg_custom_dev/` (to create)
   - Origin: `belgogreen_bgg_custom_dev_mod` (to create)
   - Upstream: `bgg_custom_dev` (exists)
   - Status: 📝 Ready to create

---

## 🔧 Git Remote Configuration

Each module folder has:

```bash
origin   → Your fork (mohammed-ibenayad/belgogreen_[MODULE]_mod)
upstream → Main repo (bsimprovement/belgogreen) on branch [MODULE_NAME]
```

### Verify Remotes

```bash
cd /c/Users/mayad/mytools/belgogreen_[MODULE_NAME]
git remote -v
```

Should show:
```
origin    https://github.com/mohammed-ibenayad/belgogreen_[MODULE]_mod.git
upstream  https://github.com/bsimprovement/belgogreen.git
```

---

## 🎓 Module Naming Convention

| Component | Pattern | Example |
|-----------|---------|---------|
| GitHub Repo | `belgogreen_[name]_mod` | `belgogreen_sales_commission_mod` |
| Local Folder | `belgogreen_[name]` | `belgogreen_sales_commission` |
| Odoo Module Folder | `[name]` or `belgogreen_[name]` | `belgogreen_sales_commission/` |
| Upstream Branch | `belgogreen_[name]` or `[name]` | `belgogreen_sales_commission` |

**Note:** The deploy script automatically detects the correct upstream branch name from your origin URL.

---

## 🆘 Troubleshooting

### Deploy script doesn't work

```bash
# Check you're in the right folder
pwd

# Check remotes
git remote -v

# Origin should match pattern: belgogreen_[MODULE]_mod
```

### Can't find setup script

```bash
# Copy from existing module
cd /c/Users/mayad/mytools/belgogreen_[NEW_MODULE]
cp ../belgogreen/setup_new_module.sh .
cp ../belgogreen/deploy_module.sh .
chmod +x *.sh
```

### Module not in right folder

```bash
# Each module should be in its own folder:
# ✅ /c/Users/mayad/mytools/belgogreen/
# ✅ /c/Users/mayad/mytools/belgogreen_bgg_custom_dev/
# ❌ NOT: /c/Users/mayad/mytools/belgogreen/bgg_custom_dev/
```

### Git push fails

```bash
# Check you have permissions
git remote -v

# Try pushing to origin first
git push origin main

# Then upstream
git push upstream main:[BRANCH_NAME]
```

---

## 📞 Getting Help

- **Quick Start:** `QUICKSTART_BGG_CUSTOM_DEV.md`
- **Full Guide:** `MODULE_SETUP_GUIDE.md`
- **Script Issues:** Check file permissions (`chmod +x *.sh`)
- **Git Issues:** Verify remotes (`git remote -v`)

---

## ✅ Summary

1. **Use separate folders** for each module (recommended)
2. **Copy scripts** from existing modules to new ones
3. **Deploy script auto-detects** module name (no manual selection)
4. **Each folder is independent** - no conflicts between modules
5. **See QUICKSTART_BGG_CUSTOM_DEV.md** to get started now!

**Ready to create bgg_custom_dev?** → Open `QUICKSTART_BGG_CUSTOM_DEV.md` 🚀
