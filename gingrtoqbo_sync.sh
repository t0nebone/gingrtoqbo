#!/bin/bash
# Script to cleanly sync the repository with GitHub

# First, let's clone the repository afresh
echo "Creating a fresh clone of the repository..."
cd /Users/antoniojimenez/Projects/nocap
mv gingrtoqbo gingrtoqbo_old
git clone https://github.com/t0nebone/gingrtoqbo.git

# Copy over the cleaned files from the backup
echo "Copying cleaned files from backup..."
cp gingrtoqbo_backup/.gitignore gingrtoqbo/
cp gingrtoqbo_backup/README.md gingrtoqbo/
cp gingrtoqbo_backup/gingrtoqbo.py gingrtoqbo/
cp gingrtoqbo_backup/requirements.txt gingrtoqbo/

# Remove any Excel files and sensitive data from the fresh clone
echo "Removing sensitive files from the repository..."
cd gingrtoqbo
git rm --cached "*.xlsx" 2>/dev/null || true
git rm --cached "~$*.xlsx" 2>/dev/null || true
git rm -r --cached "gingrfile/" 2>/dev/null || true

# Commit these changes
echo "Committing changes..."
git add .
git commit -m "Clean repository for public release"

# Push changes to GitHub
echo "Pushing changes to GitHub..."
git push

echo "====================================="
echo "Repository cleanup complete!"
echo "Now you can make the repository public on GitHub:"
echo "1. Go to https://github.com/t0nebone/gingrtoqbo/settings"
echo "2. Scroll down to 'Danger Zone'"
echo "3. Click 'Change repository visibility'"
echo "4. Select 'Public' and confirm"
echo "====================================="
