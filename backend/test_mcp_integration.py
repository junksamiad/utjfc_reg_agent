#!/usr/bin/env python3
"""
Test script to verify MCP integration between backend and MCP server
"""

import asyncio
import requests
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = "http://localhost:8001"
MCP_SERVER_URL = "http://localhost:8002"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_mcp_server_health():
    """Test if MCP server is running and healthy"""
    print("🔍 Testing MCP Server Health...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP Server is healthy: {data}")
            return True
        else:
            print(f"❌ MCP Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        return False

def test_mcp_server_direct():
    """Test MCP server directly with JSON-RPC calls"""
    print("\n🔍 Testing MCP Server Direct JSON-RPC...")
    
    # Test 1: Initialize
    print("\n1️⃣ Testing initialize...")
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: List tools
    print("\n2️⃣ Testing tools/list...")
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Call tool
    print("\n3️⃣ Testing tools/call...")
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "airtable_database_operation",
                    "arguments": {
                        "season": "2526",
                        "query": "Count all registrations"
                    }
                }
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        # Extract the actual content if successful
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"][0]["text"]
            print(f"\n   📊 Tool Result:")
            print(f"   {content}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_backend_health():
    """Test if backend is running"""
    print("\n🔍 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            print(f"✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return False

def test_backend_mcp_mode():
    """Test if backend is in MCP mode"""
    print("\n🔍 Testing Backend MCP Mode...")
    try:
        response = requests.get(f"{BACKEND_URL}/agent/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend agent status: {json.dumps(data, indent=2)}")
            return data.get("current_agent", {}).get("use_mcp", False)
        else:
            print(f"❌ Failed to get agent status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting agent status: {e}")
        return False

def test_openai_mcp_integration():
    """Test OpenAI's ability to use MCP server"""
    print("\n🔍 Testing OpenAI MCP Integration...")
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set")
        return
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        print("📤 Sending request to OpenAI with MCP tool...")
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{
                "type": "mcp",
                "server_label": "utjfc_registration",
                "server_url": "http://localhost:8002/mcp",
                "require_approval": "never"
            }],
            input="How many players are registered for season 2526?"
        )
        
        print(f"✅ OpenAI Response received!")
        print(f"   Response ID: {response.id}")
        print(f"   Model: {response.model}")
        print(f"   Output: {response.output[0].content[0].text if response.output else 'No output'}")
        
        # Check for MCP-related outputs
        if hasattr(response, 'output'):
            for output in response.output:
                if output.type == 'mcp_list_tools':
                    print(f"\n📋 MCP Tools Listed:")
                    print(f"   Server: {output.server_label}")
                    print(f"   Tools: {len(output.tools)} tools available")
                    for tool in output.tools:
                        print(f"   - {tool['name']}")
                elif output.type == 'mcp_call':
                    print(f"\n🔧 MCP Tool Called:")
                    print(f"   Tool: {output.name}")
                    print(f"   Arguments: {output.arguments}")
                    print(f"   Output: {output.output}")
                    if output.error:
                        print(f"   Error: {output.error}")
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response}")

def test_backend_chat():
    """Test backend chat endpoint with MCP"""
    print("\n🔍 Testing Backend Chat with MCP...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "user_message": "How many players are registered for season 2526?",
                "session_id": "test_session"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend chat response:")
            print(f"   {data.get('response', 'No response')}")
        else:
            print(f"❌ Backend chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error calling backend chat: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting MCP Integration Tests")
    print("=" * 50)
    
    # Test MCP server
    if not test_mcp_server_health():
        print("\n⚠️  MCP server is not running. Please start it first.")
        return
    
    # Test MCP server directly
    test_mcp_server_direct()
    
    # Test backend
    if not test_backend_health():
        print("\n⚠️  Backend is not running. Please start it first.")
        return
    
    # Check backend MCP mode
    if not test_backend_mcp_mode():
        print("\n⚠️  Backend is not in MCP mode. Please check configuration.")
    
    # Test OpenAI integration
    test_openai_mcp_integration()
    
    # Test backend chat
    test_backend_chat()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")

if __name__ == "__main__":
    main() 