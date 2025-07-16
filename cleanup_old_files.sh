#!/bin/bash

# Navigate to project directory
cd "/Users/leehayton/Cursor Projects/utjfc_reg_agent"

echo "🧹 Cleaning up old test files and organizing project structure..."

# Remove old test files from backend directory
echo "Removing old test files from backend..."
rm -f backend/test_record_check.py
rm -f backend/test_tool_integration.py
rm -f backend/run_tests.py
rm -f test_restart_chat_feature.py
rm -f commit_changes.sh

# Remove duplicated feature files from root new_features directory  
echo "Removing duplicated feature files..."
rm -f development/new_features/restart_chat_if_disconnected.md
rm -f development/new_features/restart_chat_implementation_plan.md

echo "✅ Cleanup completed!"
echo ""
echo "📁 New project structure:"
echo "development/new_features/restart_chat_if_disconnected/"
echo "├── README.md"
echo "├── feature_specification.md"
echo "├── implementation_plan.md"
echo "└── tests/"
echo "    ├── test_comprehensive.py"
echo "    ├── test_database_lookup.py"
echo "    ├── test_tool_integration.py"
echo "    └── test_manual.py"
echo ""
echo "🧪 To run tests:"
echo "python development/new_features/restart_chat_if_disconnected/tests/test_comprehensive.py"