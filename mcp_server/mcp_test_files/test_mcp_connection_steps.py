#!/usr/bin/env python3
"""
Step-by-step test of MCP server connections
"""

import requests
import json
import time

MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_step(step_name, request_data):
    """Execute a test step and display results"""
    print(f"\n{'='*60}")
    print(f"🔧 {step_name}")
    print(f"{'='*60}")
    
    try:
        print("📤 Sending request...")
        print(f"Request: {json.dumps(request_data['params']['arguments'], indent=2)}")
        
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "error" in result:
                print(f"❌ JSON-RPC Error: {result['error']}")
                return False
            
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"][0]["text"]
                parsed = json.loads(content)
                print(f"\n✅ Result:")
                print(json.dumps(parsed, indent=2))
                return True
            else:
                print("❌ Unexpected response format")
                print(json.dumps(result, indent=2))
                return False
        else:
            print(f"❌ HTTP Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return False

def main():
    print("🚀 Step-by-Step MCP Connection Test")
    print(f"🔗 Server: {MCP_SERVER_URL}")
    print("=" * 60)
    
    # Step 1: Basic MCP connectivity
    test_step(
        "Step 1: Basic MCP Connectivity (no OpenAI)",
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "test_connection",
                "arguments": {
                    "message": "Hello from test script",
                    "test_openai": False
                }
            }
        }
    )
    
    time.sleep(1)
    
    # Step 2: Test OpenAI connectivity
    test_step(
        "Step 2: Test OpenAI API Access",
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "test_connection",
                "arguments": {
                    "message": "Testing OpenAI connection",
                    "test_openai": True
                }
            }
        }
    )
    
    time.sleep(1)
    
    # Step 3: List available tools
    print(f"\n{'='*60}")
    print("🔧 Step 3: List Available Tools")
    print("=" * 60)
    
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        if "result" in result and "tools" in result["result"]:
            print("✅ Available tools:")
            for tool in result["result"]["tools"]:
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
        else:
            print("❌ Could not list tools")
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("- If Step 1 works: MCP protocol is functioning")
    print("- If Step 2 works: OpenAI API is accessible") 
    print("- If Step 3 works: Tools are properly registered")
    print("- If all work but Airtable fails: Issue is in the Airtable agent logic")
    print("=" * 60)

if __name__ == "__main__":
    main() 