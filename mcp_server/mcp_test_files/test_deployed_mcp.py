#!/usr/bin/env python3
"""Test the deployed MCP server's SSE routing behavior"""

import requests
import json
import threading
import time
import queue

# Server URL
SERVER_URL = "https://utjfc-mcp-server.replit.app"

def sse_listener(session_id, message_queue):
    """Listen to SSE stream"""
    print(f"🎧 Starting SSE listener for session {session_id}")
    
    headers = {
        "Accept": "text/event-stream",
        "Mcp-Session-Id": session_id  # Using correct header name
    }
    
    try:
        response = requests.get(f"{SERVER_URL}/mcp", headers=headers, stream=True)
        print(f"📡 SSE connection established: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    print(f"📥 SSE received: {data}")
                    try:
                        message_queue.put(json.loads(data))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"❌ SSE error: {e}")

def test_sse_routing():
    """Test SSE routing with the deployed server"""
    print("🚀 Testing Deployed MCP Server SSE Routing")
    print("=" * 50)
    
    session_id = "test-session-123"
    message_queue = queue.Queue()
    
    # Start SSE listener in background
    sse_thread = threading.Thread(target=sse_listener, args=(session_id, message_queue))
    sse_thread.daemon = True
    sse_thread.start()
    
    # Wait for connection
    time.sleep(2)
    
    # Test 1: Send tools/list with session ID
    print(f"\n📤 Sending tools/list request with session ID: {session_id}")
    headers = {
        "Content-Type": "application/json",
        "Mcp-Session-Id": session_id  # Using correct header name
    }
    
    request_data = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    response = requests.post(f"{SERVER_URL}/mcp", json=request_data, headers=headers)
    print(f"📥 POST Response: {response.status_code}")
    
    if response.status_code == 202:
        print("✅ Got 202 - Response should be routed through SSE")
        
        # Wait for SSE message
        try:
            sse_message = message_queue.get(timeout=5)
            print(f"✅ SSE Message received: {json.dumps(sse_message, indent=2)}")
        except queue.Empty:
            print("❌ No SSE message received within 5 seconds")
    else:
        print(f"❌ Expected 202, got {response.status_code}")
        if response.text:
            print(f"Response body: {response.text}")
    
    # Test 2: Send initialize request
    print(f"\n📤 Sending initialize request")
    headers = {
        "Content-Type": "application/json"
    }
    
    request_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 2
    }
    
    response = requests.post(f"{SERVER_URL}/mcp", json=request_data, headers=headers)
    print(f"📥 Initialize Response: {response.status_code}")
    
    # Check for session ID in response headers
    response_session_id = response.headers.get("Mcp-Session-Id")
    if response_session_id:
        print(f"✅ Got session ID in response: {response_session_id}")
    else:
        print("❌ No session ID in response headers")
        print(f"Response headers: {dict(response.headers)}")
    
    if response.text:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_sse_routing() 