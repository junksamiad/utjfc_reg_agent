#!/bin/bash

# Setup script for UTJFC MCP Integration

echo "🚀 Setting up UTJFC Backend Environment for MCP Integration"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "backend/server.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create backend .env file
cat > backend/.env << EOF
# Backend Environment Variables

# OpenAI API Configuration
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key_here}

# Airtable Configuration (for local function calling mode)
AIRTABLE_API_KEY=${AIRTABLE_API_KEY:-your_airtable_api_key_here}
AIRTABLE_BASE_ID=appBLxf3qmGIBc6ue

# MCP Server Configuration
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
USE_MCP=true

# Server Configuration
PORT=8000
HOST=0.0.0.0
EOF

echo "✅ Created backend/.env file with MCP configuration"
echo ""
echo "📋 Configuration:"
echo "   - MCP Server URL: https://utjfc-mcp-server.replit.app/mcp"
echo "   - USE_MCP: true (enabled)"
echo "   - Backend Port: 8000"
echo ""

# Check for API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not found in environment"
    echo "   Please edit backend/.env and add your OpenAI API key"
fi

if [ -z "$AIRTABLE_API_KEY" ]; then
    echo "⚠️  Warning: AIRTABLE_API_KEY not found in environment"
    echo "   Please edit backend/.env and add your Airtable API key"
fi

echo ""
echo "🎯 Next steps:"
echo "   1. Edit backend/.env to add your API keys if needed"
echo "   2. Start the backend: cd backend && python server.py"
echo "   3. Test the integration: python test_full_integration.py"
echo ""
echo "✨ Setup complete!" 