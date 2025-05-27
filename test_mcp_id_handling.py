#!/usr/bin/env python3
"""Test MCP server ID handling"""

import requests
import json
import time

MCP_URL = "https://utjfc-mcp-server.replit.app/mcp"

def test_id_handling():
    """Test that server correctly echoes request IDs"""
    
    print("🧪 Testing MCP Server ID Handling\n")
    
    # Test 1: Initialize with specific ID
    print("1️⃣ Testing initialize with ID 42:")
    response = requests.post(MCP_URL, json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {}
        },
        "id": 42
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response ID: {data.get('id')} (expected: 42)")
        print(f"   Match: {'✅' if data.get('id') == 42 else '❌'}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Test 2: Tools/list with string ID
    print("\n2️⃣ Testing tools/list with string ID 'test-123':")
    response = requests.post(MCP_URL, json={
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": "test-123"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response ID: {data.get('id')} (expected: 'test-123')")
        print(f"   Match: {'✅' if data.get('id') == 'test-123' else '❌'}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Test 3: Tool call with numeric ID
    print("\n3️⃣ Testing tool call with ID 999:")
    response = requests.post(MCP_URL, json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "airtable_database_operation",
            "arguments": {
                "season": "2526",
                "query": "List all players"
            }
        },
        "id": 999
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response ID: {data.get('id')} (expected: 999)")
        print(f"   Match: {'✅' if data.get('id') == 999 else '❌'}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Test 4: Batch request with different IDs
    print("\n4️⃣ Testing batch request with multiple IDs:")
    batch_response = requests.post(MCP_URL, json=[
        {"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        {"jsonrpc": "2.0", "method": "tools/list", "id": 2},
        {"jsonrpc": "2.0", "method": "tools/list", "id": 3}
    ])
    
    if batch_response.status_code == 200:
        responses = batch_response.json()
        for i, resp in enumerate(responses):
            expected_id = i + 1
            actual_id = resp.get('id')
            print(f"   Response {i+1} ID: {actual_id} (expected: {expected_id})")
            print(f"   Match: {'✅' if actual_id == expected_id else '❌'}")
    else:
        print(f"   ❌ Error: {batch_response.status_code}")
    
    print("\n✅ ID handling test complete!")

if __name__ == "__main__":
    test_id_handling() 