# Setting Up bgg_custom_dev Module

Complete guide to set up the `bgg_custom_dev` module following the Belgogreen multi-module structure.

## Module Information

- **Module Name:** `bgg_custom_dev`
- **Description:** Custom development module for BelGoGreen
- **GitHub Repo (to create):** `belgogreen_bgg_custom_dev_mod`
- **Local Folder:** `belgogreen_bgg_custom_dev`
- **Upstream Branch:** `bgg_custom_dev` (already exists on bsimprovement/belgogreen)
- **Odoo Version:** 19.0.0.0

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository with these settings:
   - **Repository name:** `belgogreen_bgg_custom_dev_mod`
   - **Description:** "Custom development module for BelGoGreen - Odoo 19"
   - **Visibility:** Private (or as per your organization's policy)
   - **DO NOT** initialize with README, .gitignore, or license (we'll add these from upstream)
3. Copy the repository URL: `https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git`

## Step 2: Set Up Local Directory Structure

Open Git Bash on your Windows machine and run:

```bash
# Navigate to your projects directory
cd /c/Users/mayad/mytools/

# Create the module directory
mkdir belgogreen_bgg_custom_dev
cd belgogreen_bgg_custom_dev

# Initialize git repository
git init

# Set up remotes
git remote add origin https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git
git remote add upstream https://github.com/bsimprovement/belgogreen.git

# Verify remotes
git remote -v
```

**Expected output:**
```
origin    https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git (fetch)
origin    https://github.com/mohammed-ibenayad/belgogreen_bgg_custom_dev_mod.git (push)
upstream  https://github.com/bsimprovement/belgogreen.git (fetch)
upstream  https://github.com/bsimprovement/belgogreen.git (push)
```

## Step 3: Fetch from Upstream Branch

```bash
# Fetch the upstream branch
git fetch upstream bgg_custom_dev

# Create and checkout main branch from upstream
git checkout -b main upstream/bgg_custom_dev

# If the branch is empty or doesn't have content yet, you might need to create an initial commit
# Check if there are files:
ls -la
```

### If Upstream Branch is Empty

If the upstream branch doesn't have any files yet, you'll need to create the initial module structure:

```bash
# Make sure you're on main branch
git checkout -b main

# Continue to Step 4 to create the module structure
```

## Step 4: Create Module Structure

### Option A: Using the Setup Script (Recommended)

Copy the setup script from your sales commission module:

```bash
# From your belgogreen_bgg_custom_dev directory
cp ../belgogreen/setup_new_module.sh .
chmod +x setup_new_module.sh

# Run the script
./setup_new_module.sh
```

The script will create the complete module structure for you!

### Option B: Manual Setup

If you prefer to do it manually or the script is not available:

```bash
# Create module directory structure
mkdir -p bgg_custom_dev
mkdir -p bgg_custom_dev/models
mkdir -p bgg_custom_dev/views
mkdir -p bgg_custom_dev/security
mkdir -p bgg_custom_dev/data
mkdir -p bgg_custom_dev/static/description
```

Then copy the template files from the setup package (see Step 5).

## Step 5: Copy Deploy Script

```bash
# Copy the deploy script from sales commission module
cp ../belgogreen/deploy_module.sh .
chmod +x deploy_module.sh
```

## Step 6: Initial Commit and Push

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: bgg_custom_dev module structure for Odoo 19"

# Push to your origin repository
git push -u origin main
```

## Step 7: Push to Upstream (Optional)

If you want to push your initial structure to the upstream branch:

```bash
# Push to upstream bgg_custom_dev branch
git push upstream main:bgg_custom_dev
```

**Note:** Make sure you have write permissions to the upstream repository before doing this.

## Step 8: Verify Setup

Check that everything is set up correctly:

```bash
# Check git status
git status

# Check remotes
git remote -v

# Check branches
git branch -a

# List module contents
ls -la bgg_custom_dev/
```

You should see:
- Clean git status
- Both origin and upstream remotes configured
- main branch tracking origin/main
- Module structure created

## Directory Structure

After setup, your directory should look like this:

```
belgogreen_bgg_custom_dev/
├── bgg_custom_dev/                    # Main module directory
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   └── __init__.py
│   ├── views/
│   │   └── menu_views.xml
│   ├── security/
│   │   └── ir.model.access.csv
│   ├── data/
│   └── static/
│       └── description/
│           └── icon.png
├── deploy_module.sh                   # Deployment script
└── README.md                          # Module documentation
```

## Next Steps: Development Workflow

### 1. Make Changes

Edit your module files as needed:
- Add models in `bgg_custom_dev/models/`
- Add views in `bgg_custom_dev/views/`
- Add security rules in `bgg_custom_dev/security/`

### 2. Test Locally (Optional)

If you have a local Odoo instance:
```bash
# Link or copy your module to Odoo addons path
# Then update the module list in Odoo
```

### 3. Commit Changes

```bash
git add .
git commit -m "Add feature X"
git push origin main
```

### 4. Deploy Using Script

When you're ready to merge a Claude branch:

```bash
./deploy_module.sh
```

The script will:
- Auto-detect the module name (bgg_custom_dev)
- Merge the Claude branch into main
- Push to origin
- Optionally push to upstream/bgg_custom_dev

## Troubleshooting

### Problem: Upstream branch doesn't exist

**Solution:** The branch should already exist. Verify with:
```bash
git ls-remote --heads upstream | grep bgg_custom_dev
```

If it doesn't exist, contact your upstream repository maintainer.

### Problem: Permission denied when pushing to upstream

**Solution:** Make sure you have write access to the upstream repository. If not, you'll only push to origin and create a pull request.

### Problem: Module not detected by Odoo

**Solution:** Check that:
1. The module directory name matches the name in `__manifest__.py`
2. The `__manifest__.py` file is valid Python
3. The module path is in Odoo's addons path

### Problem: Deploy script doesn't work

**Solution:**
1. Verify the script is executable: `chmod +x deploy_module.sh`
2. Check that origin remote URL follows the pattern: `belgogreen_[MODULE]_mod.git`
3. Run the script with bash explicitly: `bash deploy_module.sh`

## Quick Reference Commands

```bash
# Check current module
git remote get-url origin

# See all remotes
git remote -v

# Fetch latest from upstream
git fetch upstream bgg_custom_dev

# Deploy a Claude branch
./deploy_module.sh

# Check Odoo module syntax
python3 -m py_compile bgg_custom_dev/__manifest__.py
```

## Additional Resources

- See `MODULE_SETUP_GUIDE.md` for general multi-module setup
- See `deploy_module.sh` for deployment automation
- Odoo 19 Documentation: https://www.odoo.com/documentation/19.0/

## Summary Checklist

- [ ] GitHub repository created: `belgogreen_bgg_custom_dev_mod`
- [ ] Local directory created: `belgogreen_bgg_custom_dev`
- [ ] Git initialized and remotes configured
- [ ] Upstream branch fetched: `bgg_custom_dev`
- [ ] Main branch created from upstream
- [ ] Module structure created
- [ ] Deploy script copied and executable
- [ ] Initial commit created
- [ ] Pushed to origin/main
- [ ] (Optional) Pushed to upstream/bgg_custom_dev
- [ ] Setup verified with git status and ls commands

You're now ready to develop the bgg_custom_dev module! 🚀
