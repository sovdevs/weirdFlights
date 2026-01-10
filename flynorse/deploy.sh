#!/bin/bash

# 🚀 Weird Flights - One-Click Deploy Script
# This script automates deployment to GitHub and enables free hosting

set -e

echo "═══════════════════════════════════════════════════"
echo "  🚀 Weird Flights - Deployment Setup"
echo "═══════════════════════════════════════════════════"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install git first."
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME

# Get repository name
read -p "Enter repository name (default: weirdFlights): " REPO_NAME
REPO_NAME=${REPO_NAME:-weirdFlights}

# Check if repo already exists locally
if [ -d ".git" ]; then
    echo "✓ Git repository already initialized"
else
    echo "📦 Initializing git repository..."
    git init
    git config user.name "${GITHUB_USERNAME}"
    git config user.email "${GITHUB_USERNAME}@users.noreply.github.com"
fi

# Add all files
echo "📝 Staging files..."
git add .

# Create initial commit
if git diff --cached --quiet; then
    echo "✓ Everything up to date"
else
    git commit -m "🚀 Initial commit - Weird Flights deployment"
fi

# Rename branch to main if needed
if git rev-parse --verify main 2>/dev/null; then
    echo "✓ Already on main branch"
elif git rev-parse --verify master 2>/dev/null; then
    echo "📋 Renaming branch to main..."
    git branch -M main
fi

# Check if remote already exists
if git remote | grep -q origin; then
    EXISTING_URL=$(git config --get remote.origin.url)
    echo "✓ Remote origin already set to: $EXISTING_URL"
    read -p "Update to new URL? (y/n): " UPDATE_REMOTE
    if [[ $UPDATE_REMOTE == "y" ]]; then
        git remote remove origin
        git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    fi
else
    echo "🔗 Setting remote repository..."
    git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  📋 Next Steps:"
echo "═══════════════════════════════════════════════════"
echo ""
echo "1️⃣  Create repository on GitHub:"
echo "    → Go to https://github.com/new"
echo "    → Repository name: ${REPO_NAME}"
echo "    → Click 'Create repository' (DON'T initialize with README)"
echo ""
echo "2️⃣  Push to GitHub:"
echo "    git push -u origin main"
echo ""
echo "3️⃣  Deploy to Netlify (RECOMMENDED - Easiest):"
echo "    → Go to https://netlify.com"
echo "    → Click 'New site from Git'"
echo "    → Connect your GitHub account"
echo "    → Select: ${GITHUB_USERNAME}/${REPO_NAME}"
echo "    → Click 'Deploy site'"
echo ""
echo "4️⃣  Daily Scraping Setup:"
echo "    → Go to: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
echo "    → You should see 'Daily Flight Scrape' workflow"
echo "    → It will automatically run daily at 2 AM UTC"
echo ""
echo "5️⃣  Your site will be live at:"
echo "    → https://your-site-name.netlify.app"
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Alternative: Deploy to Vercel"
echo "═══════════════════════════════════════════════════"
echo "→ Go to https://vercel.com"
echo "→ Click 'New Project' → Import Git Repo"
echo "→ Select: ${GITHUB_USERNAME}/${REPO_NAME}"
echo "→ Click 'Deploy'"
echo ""
echo "═══════════════════════════════════════════════════"
echo ""
echo "📚 For more details, see DEPLOY.md"
echo ""
