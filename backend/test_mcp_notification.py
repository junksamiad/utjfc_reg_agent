#!/usr/bin/env python3
"""
Test MCP server's handling of notifications (requests without ID)
"""

import requests
import json

MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_notification():
    """Test JSON-RPC notification (no ID)"""
    print("🔍 Testing JSON-RPC notification handling...")
    
    # Send a notification (no ID field)
    notification = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    print(f"📤 Sending notification (no ID): {json.dumps(notification, indent=2)}")
    
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=notification,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.text:
            print(f"📥 Response body: {response.text}")
        else:
            print("📥 Response body: (empty)")
            
        # For notifications, we expect 202 Accepted or empty response
        if response.status_code == 202:
            print("✅ Server correctly handled notification with 202 Accepted")
        elif response.status_code == 200 and not response.text:
            print("✅ Server correctly handled notification with empty 200 response")
        else:
            print("⚠️  Unexpected response for notification")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_sse_connection():
    """Test SSE connection"""
    print("\n🔍 Testing SSE connection...")
    
    try:
        # Test GET request with SSE accept header
        response = requests.get(
            f"{MCP_SERVER_URL}/mcp",
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=5
        )
        
        print(f"📥 SSE Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SSE endpoint accessible")
            # Read first few events
            for i, line in enumerate(response.iter_lines()):
                if i > 5:  # Only read first few lines
                    break
                if line:
                    print(f"📥 SSE Event: {line.decode('utf-8')}")
        else:
            print(f"❌ SSE endpoint returned: {response.status_code}")
            
    except Exception as e:
        print(f"❌ SSE Error: {e}")

if __name__ == "__main__":
    print("🚀 MCP Server Notification Test")
    print("=" * 50)
    
    test_notification()
    test_sse_connection()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!") 