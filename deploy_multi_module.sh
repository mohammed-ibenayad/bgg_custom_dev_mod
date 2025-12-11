#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Multi-Module Deployment Script ===${NC}\n"

# Detect available modules in the current directory
echo -e "${YELLOW}Detecting modules...${NC}"
modules=()
for dir in */; do
    if [ -f "${dir}__manifest__.py" ]; then
        module_name="${dir%/}"
        modules+=("$module_name")
        echo -e "  Found: ${BLUE}$module_name${NC}"
    fi
done

if [ ${#modules[@]} -eq 0 ]; then
    echo -e "${RED}❌ Error: No Odoo modules found in current directory${NC}"
    exit 1
fi

echo ""

# Ask which module to deploy
if [ ${#modules[@]} -eq 1 ]; then
    selected_module="${modules[0]}"
    echo -e "${GREEN}✓ Auto-selected module: ${BLUE}$selected_module${NC}\n"
else
    echo -e "${YELLOW}Select module to deploy:${NC}"
    for i in "${!modules[@]}"; do
        echo -e "  $((i+1)). ${BLUE}${modules[$i]}${NC}"
    done
    echo ""
    read -p "Enter number (1-${#modules[@]}): " selection

    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt "${#modules[@]}" ]; then
        echo -e "${RED}❌ Error: Invalid selection${NC}"
        exit 1
    fi

    selected_module="${modules[$((selection-1))]}"
    echo -e "\n${GREEN}✓ Selected: ${BLUE}$selected_module${NC}\n"
fi

# Determine upstream branch name based on module
# belgogreen_sales_commission → belgogreen_sales_commission
# bgg_custom_dev → bgg_custom_dev
upstream_branch="$selected_module"

echo -e "${BLUE}📦 Module: ${YELLOW}$selected_module${NC}"
echo -e "${BLUE}📤 Upstream branch: ${YELLOW}$upstream_branch${NC}\n"

# Verify upstream exists
if ! git remote get-url upstream >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: No upstream remote found${NC}"
    echo -e "${YELLOW}ℹ️  Add upstream with: git remote add upstream https://github.com/bsimprovement/belgogreen.git${NC}"
    exit 1
fi

# Ask for Claude branch name
read -p "Enter the Claude branch name (or press Enter to skip merge): " claude_branch

if [ -n "$claude_branch" ]; then
    echo -e "\n${YELLOW}Fetching latest branches...${NC}"
    git fetch --all

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: Failed to fetch${NC}"
        exit 1
    fi

    # Validate branch exists
    if ! git rev-parse --verify "$claude_branch" >/dev/null 2>&1; then
        if ! git rev-parse --verify "origin/$claude_branch" >/dev/null 2>&1; then
            echo -e "${RED}❌ Error: Branch '$claude_branch' does not exist${NC}"
            exit 1
        else
            echo -e "${YELLOW}Branch exists remotely, checking out...${NC}"
            git checkout "$claude_branch"
            if [ $? -ne 0 ]; then
                echo -e "${RED}❌ Error: Failed to checkout branch${NC}"
                exit 1
            fi
        fi
    fi

    echo -e "\n${YELLOW}Switching to main branch...${NC}"
    git checkout main

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: Failed to checkout main branch${NC}"
        exit 1
    fi

    echo -e "\n${YELLOW}Merging $claude_branch into main...${NC}"
    git merge "$claude_branch"

    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error: Merge failed. Please resolve conflicts manually.${NC}"
        exit 1
    fi

    echo -e "\n${GREEN}✅ Successfully merged $claude_branch into main!${NC}\n"
fi

# Check if there are changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  There are uncommitted changes. Please commit them first.${NC}"
    read -p "Do you want to commit all changes now? (yes/no): " commit_changes

    if [[ "$commit_changes" == "yes" || "$commit_changes" == "y" ]]; then
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg"

        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Error: Commit failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Cannot deploy with uncommitted changes${NC}"
        exit 1
    fi
fi

# Push to upstream
echo -e "${YELLOW}Pushing to upstream:${BLUE}$upstream_branch${NC}...${NC}"
git push upstream main:$upstream_branch

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error: Failed to push to upstream${NC}"
    echo -e "${YELLOW}ℹ️  Make sure the branch '$upstream_branch' exists on upstream or you have permission${NC}"

    read -p "Do you want to create the branch on upstream? (yes/no): " create_branch
    if [[ "$create_branch" == "yes" || "$create_branch" == "y" ]]; then
        git push upstream main:$upstream_branch
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Error: Still failed to push${NC}"
            exit 1
        fi
    else
        exit 1
    fi
fi

echo -e "\n${GREEN}✅ Successfully pushed to upstream:$upstream_branch!${NC}"

# Clean up merged branch if specified
if [ -n "$claude_branch" ]; then
    read -p "Do you want to delete the merged Claude branch? (yes/no): " delete_branch

    if [[ "$delete_branch" == "yes" || "$delete_branch" == "y" ]]; then
        echo -e "\n${YELLOW}Deleting local branch $claude_branch...${NC}"
        git branch -d "$claude_branch"

        echo -e "${YELLOW}Deleting remote branch $claude_branch...${NC}"
        # Try to delete from origin if it exists
        git push origin --delete "$claude_branch" 2>/dev/null || true

        echo -e "${GREEN}✅ Branch cleanup complete!${NC}"
    fi
fi

echo -e "\n${GREEN}🎉 Deployment complete!${NC}"
echo -e "${BLUE}Summary:${NC}"
echo -e "  • Module: ${YELLOW}$selected_module${NC}"
if [ -n "$claude_branch" ]; then
    echo -e "  • Merged: ${YELLOW}$claude_branch${NC} → main"
fi
echo -e "  • Pushed to: ${YELLOW}upstream/$upstream_branch${NC}"
echo ""
