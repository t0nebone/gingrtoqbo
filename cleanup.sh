#!/bin/bash
# Script to remove sensitive files from Git tracking

# Remove Excel files from Git tracking (but keep them locally)
git rm --cached "Processed_File (1).xlsx"
git rm --cached "Processed_File.xlsx"
git rm --cached "Q3-2024-Invoices and Payments for Import.xlsx"
git rm --cached "final from jerm Q3-2024-Invoices and Payments for Import.xlsx"

# Remove the entire gingrfile directory from Git tracking
git rm --cached -r gingrfile/

# Remove any temp Excel files that might be tracked
git rm --cached "~$*.xlsx"

# Commit these changes
git commit -m "Remove sensitive files from Git tracking"

# Push the changes to remote
git push

echo "Cleanup complete! The repository is now ready to be made public."
echo "You can now go to the GitHub repository settings and change it to public."
