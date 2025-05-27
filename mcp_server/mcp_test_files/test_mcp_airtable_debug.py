#!/usr/bin/env python3
"""
Debug test to understand Airtable integration failures
"""

import requests
import json
import time

# MCP Server URL
MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_simple_query():
    """Test with the simplest possible query"""
    print("\n" + "="*60)
    print("🧪 TEST: Simplest Query")
    print("="*60)
    
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "airtable_database_operation",
            "arguments": {
                "season": "2526",
                "query": "count"  # Simplest possible query
            }
        }
    }
    
    try:
        print("📤 Sending minimal query...")
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Full response: {json.dumps(result, indent=2)}")
            
            # Try to extract error details
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"][0]["text"]
                parsed = json.loads(content)
                if parsed.get("status") == "error":
                    print(f"\n❌ Error Details: {parsed.get('message')}")
                    if "data" in parsed and parsed["data"]:
                        print(f"Additional info: {parsed['data']}")
        else:
            print(f"HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

def test_with_different_model():
    """Test if it's a model issue"""
    print("\n" + "="*60)
    print("🧪 TEST: Check Model Availability")
    print("="*60)
    
    # First, let's see if we can get more details about the error
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "airtable_database_operation",
            "arguments": {
                "season": "2526",
                "query": "Show all records"  # Different query format
            }
        }
    }
    
    try:
        print("📤 Testing with 'Show all records' query...")
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if there's an error in the response
            if "error" in result:
                print(f"JSON-RPC Error: {result['error']}")
            elif "result" in result:
                # Try to parse the nested response
                try:
                    content = result["result"]["content"][0]["text"]
                    parsed = json.loads(content)
                    print(f"Status: {parsed.get('status')}")
                    print(f"Message: {parsed.get('message')}")
                    
                    # Look for any clues in the data
                    if "data" in parsed:
                        print(f"Data: {json.dumps(parsed['data'], indent=2)}")
                except Exception as parse_error:
                    print(f"Parse error: {parse_error}")
                    print(f"Raw result: {json.dumps(result, indent=2)}")
                    
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

def test_direct_airtable_check():
    """Test if we can at least verify the table exists"""
    print("\n" + "="*60)
    print("🧪 TEST: Direct Table Check")
    print("="*60)
    
    # Try a very specific query that should work if Airtable is accessible
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "airtable_database_operation",
            "arguments": {
                "season": "2526",
                "query": "List first record"  # Very specific, simple operation
            }
        }
    }
    
    try:
        print("📤 Testing with 'List first record' query...")
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📥 Response Status: {response.status_code}")
        result = response.json()
        
        # Full response for debugging
        print(f"\nFull response structure:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

def main():
    print("🔍 Debug Testing MCP Server Airtable Integration")
    print(f"🔗 Server: {MCP_SERVER_URL}")
    print("=" * 60)
    
    # Run tests with delays
    test_simple_query()
    time.sleep(2)
    
    test_with_different_model()
    time.sleep(2)
    
    test_direct_airtable_check()
    
    print("\n" + "=" * 60)
    print("🔍 Debug tests completed!")
    print("\nPossible issues to investigate:")
    print("1. The model 'gpt-4.1' might not be available")
    print("2. The Responses API might not be accessible from Replit")
    print("3. The code interpreter tool might not be working as expected")
    print("4. There might be an issue with the Airtable agent's code parsing logic")
    print("=" * 60)

if __name__ == "__main__":
    main() 