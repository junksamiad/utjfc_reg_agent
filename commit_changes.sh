#!/bin/bash

# Navigate to project directory
cd "/Users/leehayton/Cursor Projects/utjfc_reg_agent"

# Check git status
echo "Current git status:"
git status

# Add all changes
echo "Adding changes..."
git add .

# Check what will be committed
echo "Changes to be committed:"
git status

# Commit changes
echo "Committing changes..."
git commit -m "feat: implement registration resume for disconnected users

- Add check_if_record_exists_in_db core function
- Add check_if_record_exists_in_db_tool with OpenAI schema and handler
- Update routine 2 with resume logic (steps 5-8)
- Register new tool in __init__.py, agents_reg.py, and registration_agents.py
- Enable users to resume registration after accidental disconnection
- Route based on played_for_urmston_town_last_season field and kit requirements

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "Git operations completed!"