#!/bin/bash

# Deployment script for restart chat feature
# Run from project root: bash deploy_restart_chat.sh

echo "🚀 DEPLOYING RESTART CHAT FEATURE"
echo "================================="

# Navigate to project directory
cd "/Users/leehayton/Cursor Projects/utjfc_reg_agent"

# Check current branch
echo "📋 Current branch:"
git branch --show-current

# Show git status
echo ""
echo "📋 Git status:"
git status

# Add all changes
echo ""
echo "📦 Adding changes..."
git add .

# Show what will be committed
echo ""
echo "📋 Changes to be committed:"
git status

# Commit changes
echo ""
echo "💾 Committing changes..."
git commit -m "feat: implement registration resume for disconnected users

- Add check_if_record_exists_in_db core function for database record lookup
- Add check_if_record_exists_in_db_tool with OpenAI schema and handler
- Update routine 2 with resume logic (steps 5-8) based on existing records
- Register new tool in __init__.py, agents_reg.py, and registration_agents.py
- Enable users to resume registration after accidental disconnection
- Route based on played_for_urmston_town_last_season field and kit requirements
- Create comprehensive test suite in organized directory structure
- Update feature documentation with new organizational structure

This addresses the 50% disconnection rate at payment SMS step by allowing
users to resume their registration without re-entering all data.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to origin
echo ""
echo "🌐 Pushing to origin..."
git push origin feature/restart-chat-if-disconnected

echo ""
echo "✅ DEPLOYMENT PREPARATION COMPLETE!"
echo ""
echo "🎯 Next Steps:"
echo "1. Follow deployment guide LLD to deploy to production"
echo "2. Test with real registration codes (Lee Hayton / Seb Hayton)"
echo "3. Monitor for successful resume functionality"
echo "4. Merge to dev branch after successful testing"
echo ""
echo "📋 Feature Summary:"
echo "- Core function: check_if_record_exists_in_db"
echo "- Modified routine: Routine 2 (steps 5-8)"
echo "- Test coverage: Comprehensive test suite created"
echo "- Expected impact: Reduce 50% disconnection rate at payment SMS"