#!/usr/bin/env python3
"""
Test MCP server session header behavior
"""

import requests
import json

MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_session_headers():
    print("🧪 Testing MCP Session Header Behavior")
    print("=" * 50)
    
    # Test 1: Initialize without session header
    print("\n1️⃣ Testing initialize (no session header):")
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        headers={"Content-Type": "application/json"},
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {},
            "id": 1
        }
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response headers:")
    for key, value in response.headers.items():
        if 'session' in key.lower():
            print(f"   - {key}: {value}")
    
    session_id = response.headers.get('Mcp-Session-Id') or response.headers.get('mcp-session-id')
    print(f"   Session ID returned: {session_id}")
    
    # Test 2: Tools/list WITHOUT session header (this is what OpenAI does)
    print("\n2️⃣ Testing tools/list WITHOUT session header:")
    response2 = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        headers={"Content-Type": "application/json"},
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        },
        timeout=5
    )
    
    print(f"   Status: {response2.status_code}")
    if response2.status_code == 200:
        print(f"   ✅ Server accepted request without session header")
        print(f"   Response: {json.dumps(response2.json(), indent=2)[:200]}...")
    elif response2.status_code == 202:
        print(f"   ❌ Server returned 202 (expects SSE) - this might hang OpenAI")
    else:
        print(f"   ❌ Unexpected status: {response2.text[:200]}")
    
    # Test 3: Tools/list WITH session header (for comparison)
    if session_id:
        print("\n3️⃣ Testing tools/list WITH session header:")
        response3 = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": session_id
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 3
            },
            timeout=5
        )
        
        print(f"   Status: {response3.status_code}")
        if response3.status_code == 200:
            print(f"   ✅ Got direct JSON response")
        elif response3.status_code == 202:
            print(f"   📡 Got 202 - response will come via SSE")

def test_delete_endpoint():
    """Test that DELETE requests are now handled properly"""
    
    print("🧪 Testing MCP Server DELETE Endpoint\n")
    
    # First, initialize to get a session ID
    print("1️⃣ Initializing to get session ID:")
    init_response = requests.post(f"{MCP_SERVER_URL}/mcp", json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {}
        },
        "id": 1
    })
    
    session_id = None
    if init_response.status_code == 200:
        # Check for session ID in headers
        session_id = init_response.headers.get("Mcp-Session-Id")
        print(f"   ✅ Initialized successfully")
        print(f"   Session ID: {session_id}")
    else:
        print(f"   ❌ Error: {init_response.status_code}")
        return
    
    # Test DELETE without session ID
    print("\n2️⃣ Testing DELETE without session ID:")
    delete_response = requests.delete(f"{MCP_SERVER_URL}/mcp")
    print(f"   Status: {delete_response.status_code}")
    print(f"   Expected: 204 (No Content)")
    print(f"   Result: {'✅' if delete_response.status_code == 204 else '❌'}")
    
    # Test DELETE with session ID
    if session_id:
        print("\n3️⃣ Testing DELETE with session ID:")
        headers = {"Mcp-Session-Id": session_id}
        delete_response = requests.delete(f"{MCP_SERVER_URL}/mcp", headers=headers)
        print(f"   Status: {delete_response.status_code}")
        print(f"   Expected: 204 (No Content)")
        print(f"   Result: {'✅' if delete_response.status_code == 204 else '❌'}")
    
    # Test OPTIONS to verify DELETE is allowed
    print("\n4️⃣ Testing OPTIONS to verify DELETE is allowed:")
    options_response = requests.options(f"{MCP_SERVER_URL}/mcp")
    if options_response.status_code == 200:
        allowed_methods = options_response.headers.get("Access-Control-Allow-Methods", "")
        print(f"   Allowed methods: {allowed_methods}")
        print(f"   DELETE allowed: {'✅' if 'DELETE' in allowed_methods else '❌'}")
    else:
        print(f"   ❌ Error: {options_response.status_code}")
    
    print("\n✅ DELETE endpoint test complete!")

if __name__ == "__main__":
    test_session_headers()
    test_delete_endpoint() 