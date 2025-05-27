#!/usr/bin/env python3
"""
Basic test to check MCP server functionality
"""

import requests
import json

MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_tools_list():
    """Test tools/list method"""
    print("\n🔧 Testing Tools List...")
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_initialize():
    """Test initialize method"""
    print("\n🚀 Testing Initialize...")
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print(f"🔍 Testing MCP Server: {MCP_SERVER_URL}")
    print("=" * 60)
    
    test_health()
    test_tools_list()
    test_initialize()
    
    print("\n" + "=" * 60)
    print("✅ Basic tests completed!") 