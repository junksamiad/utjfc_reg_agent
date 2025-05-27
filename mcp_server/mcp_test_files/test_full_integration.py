#!/usr/bin/env python3
"""
Test Full MCP Integration - Backend to MCP Server to Airtable Tool
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = "http://localhost:8000"
MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_backend_status():
    """Test backend agent status"""
    print("\n1️⃣ Testing Backend Agent Status...")
    try:
        response = requests.get(f"{BACKEND_URL}/agent/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is running")
            print(f"   Current agent: {data['current_agent']['name']}")
            print(f"   Using MCP: {data['current_agent']['use_mcp']}")
            print(f"   MCP Server URL: {data['current_agent'].get('mcp_server_url', 'Not set')}")
            return data
        else:
            print(f"❌ Backend status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print(f"   Make sure backend is running on {BACKEND_URL}")
        return None

def test_mcp_server_health():
    """Test MCP server health"""
    print("\n2️⃣ Testing MCP Server Health...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP Server is healthy")
            print(f"   Version: {data['version']}")
            print(f"   Environment: {data['environment']}")
            return True
        else:
            print(f"❌ MCP Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return False

def test_mcp_tools():
    """Test MCP server tools list"""
    print("\n3️⃣ Testing MCP Server Tools...")
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            headers={"Content-Type": "application/json"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }
        )
        if response.status_code == 200:
            data = response.json()
            tools = data.get("result", {}).get("tools", [])
            print(f"✅ MCP Server has {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
            return True
        else:
            print(f"❌ MCP tools list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error listing MCP tools: {e}")
        return False

def test_backend_chat():
    """Test backend chat with MCP integration"""
    print("\n4️⃣ Testing Backend Chat with MCP...")
    
    # Clear chat history first
    requests.post(f"{BACKEND_URL}/clear")
    
    # Test query
    test_message = "Can you test the connection to the registration database? Just confirm you can access it."
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"user_message": test_message}
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            print(f"✅ Backend chat responded")
            print(f"   User: {test_message}")
            print(f"   AI: {ai_response[:200]}...")
            return True
        else:
            print(f"❌ Backend chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error in backend chat: {e}")
        return False

def test_airtable_query():
    """Test a real Airtable query through the full stack"""
    print("\n5️⃣ Testing Real Airtable Query...")
    
    test_message = "How many players are registered for the current season (2526)?"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"user_message": test_message}
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            print(f"✅ Airtable query completed")
            print(f"   User: {test_message}")
            print(f"   AI Response:")
            print(f"   {ai_response}")
            return True
        else:
            print(f"❌ Airtable query failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in Airtable query: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 UTJFC MCP Full Integration Test")
    print("=" * 50)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"   AIRTABLE_API_KEY: {'✅ Set' if os.getenv('AIRTABLE_API_KEY') else '❌ Not set'}")
    print(f"   MCP_SERVER_URL: {os.getenv('MCP_SERVER_URL', 'Not set (will use default)')}")
    print(f"   USE_MCP: {os.getenv('USE_MCP', 'Not set (defaults to true)')}")
    
    # Run tests
    backend_status = test_backend_status()
    if not backend_status:
        print("\n⚠️  Backend is not running. Please start it with:")
        print("   cd backend && python server.py")
        return
    
    # Check if backend is using correct MCP server URL
    mcp_url = backend_status['current_agent'].get('mcp_server_url', '')
    if 'localhost' in mcp_url or '8002' in mcp_url:
        print("\n⚠️  Backend is using local MCP server URL!")
        print(f"   Current: {mcp_url}")
        print(f"   Should be: {MCP_SERVER_URL}/mcp")
        print("\n   To fix, set environment variable:")
        print(f"   export MCP_SERVER_URL={MCP_SERVER_URL}/mcp")
        print("   Then restart the backend server")
    
    # Continue with other tests
    mcp_healthy = test_mcp_server_health()
    if mcp_healthy:
        test_mcp_tools()
    
    # Test full integration
    if backend_status and mcp_healthy:
        test_backend_chat()
        test_airtable_query()
    
    print("\n✨ Integration test complete!")

if __name__ == "__main__":
    main() 