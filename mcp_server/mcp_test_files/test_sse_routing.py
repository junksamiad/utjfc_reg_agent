#!/usr/bin/env python3
"""
Test SSE routing on the fixed MCP server
"""

import requests
import json
import threading
import time
import queue

MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def sse_listener(session_id, message_queue):
    """Listen to SSE stream"""
    print(f"🎧 Starting SSE listener for session {session_id}")
    
    try:
        response = requests.get(
            f"{MCP_SERVER_URL}/mcp",
            headers={
                "Accept": "text/event-stream",
                "X-MCP-Session-Id": session_id
            },
            stream=True,
            timeout=60
        )
        
        print(f"📡 SSE connection established: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    message_queue.put(data)
                    print(f"📥 SSE received: {data}")
                elif line_str.startswith(': '):
                    print(f"💓 Keepalive: {line_str}")
                    
    except Exception as e:
        print(f"❌ SSE Error: {e}")
        message_queue.put(f"ERROR: {e}")

def test_sse_routing():
    """Test if responses are routed through SSE"""
    session_id = "test-session-123"
    message_queue = queue.Queue()
    
    # Start SSE listener in background thread
    sse_thread = threading.Thread(target=sse_listener, args=(session_id, message_queue))
    sse_thread.daemon = True
    sse_thread.start()
    
    # Wait for connection to establish
    time.sleep(2)
    
    print(f"\n📤 Sending tools/list request with session ID: {session_id}")
    
    # Send request with session ID
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        },
        headers={
            "Content-Type": "application/json",
            "X-MCP-Session-Id": session_id
        }
    )
    
    print(f"📥 POST Response: {response.status_code} - {response.text if response.text else '(empty)'}")
    
    # Check if we got 202 (indicating SSE routing)
    if response.status_code == 202:
        print("✅ Server returned 202 - response should come via SSE")
        
        # Wait for SSE message
        try:
            sse_message = message_queue.get(timeout=5)
            print(f"\n🎉 SSE Message received: {sse_message}")
            
            # Parse and verify it's the tools/list response
            try:
                data = json.loads(sse_message)
                if data.get("id") == 1 and "result" in data:
                    print("✅ Correct tools/list response received via SSE!")
                    print(f"   Tools: {len(data['result'])} tools available")
            except:
                pass
                
        except queue.Empty:
            print("❌ No SSE message received within 5 seconds")
    else:
        print(f"❌ Expected 202, got {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing SSE Routing")
    print("=" * 50)
    
    test_sse_routing()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 