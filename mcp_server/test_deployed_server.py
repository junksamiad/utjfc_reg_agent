#!/usr/bin/env python3
"""
Test script for deployed MCP server
"""

import requests
import json
import sys

def test_mcp_server(base_url, auth_token=None):
    """Test the deployed MCP server"""
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    print(f"🧪 Testing MCP Server at: {base_url}")
    print("=" * 60)
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["X-MCP-Auth-Token"] = auth_token
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Initialize
    print("\n2️⃣ Testing initialize...")
    try:
        response = requests.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            },
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: List tools
    print("\n3️⃣ Testing tools/list...")
    try:
        response = requests.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Extract tools
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"\n   📋 Available tools: {len(tools)}")
                for tool in tools:
                    print(f"      - {tool['name']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: OpenAI format test
    print("\n4️⃣ Testing OpenAI compatibility...")
    print("   Use this configuration in your OpenAI client:")
    config = {
        "type": "mcp",
        "server_label": "utjfc_registration",
        "server_url": f"{base_url}/mcp",
        "require_approval": "never"
    }
    if auth_token:
        config["headers"] = {
            "X-MCP-Auth-Token": auth_token
        }
    print(f"   {json.dumps(config, indent=2)}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_deployed_server.py <server_url> [auth_token]")
        print("Example: python test_deployed_server.py https://my-mcp-server.repl.co my_secret_token")
        sys.exit(1)
    
    server_url = sys.argv[1]
    auth_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_mcp_server(server_url, auth_token) 