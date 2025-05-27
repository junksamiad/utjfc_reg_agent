#!/usr/bin/env python3
"""
Test the complete backend to MCP flow
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def test_backend_flow():
    print("🧪 Testing Complete Backend → MCP Flow")
    print("=" * 50)
    
    # Check backend status
    print("\n1️⃣ Checking backend status:")
    try:
        response = requests.get(f"{BACKEND_URL}/agent/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend running")
            print(f"   Agent: {data['current_agent']['name']}")
            print(f"   MCP enabled: {data['current_agent']['use_mcp']}")
            print(f"   MCP URL: {data['current_agent']['mcp_server_url']}")
        else:
            print(f"   ❌ Backend not responding properly")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to backend: {e}")
        print("   Make sure backend is running: cd backend && python server.py")
        return
    
    # Clear chat history
    print("\n2️⃣ Clearing chat history:")
    requests.post(f"{BACKEND_URL}/clear")
    print("   ✅ Chat history cleared")
    
    # Send test message
    print("\n3️⃣ Sending test message:")
    test_message = "How many players are registered for season 2526?"
    print(f"   Message: {test_message}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"user_message": test_message},
            timeout=60  # 60 second timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n   Status: {response.status_code}")
        print(f"   Time taken: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            
            print(f"\n   ✅ Got response!")
            print(f"   Response length: {len(ai_response)} characters")
            print(f"\n   AI Response:")
            print("   " + "-" * 50)
            print(f"   {ai_response}")
            print("   " + "-" * 50)
            
            # Check if response contains expected data
            if "12" in ai_response or "twelve" in ai_response.lower():
                print(f"\n   ✅ Response contains correct count (12 players)")
            else:
                print(f"\n   ⚠️  Response doesn't mention the count")
                
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n   ❌ Request timed out after {elapsed:.2f}s")
        print("   The backend is hanging when processing the MCP response")
        
    except Exception as e:
        print(f"\n   ❌ Error: {type(e).__name__}: {e}")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    # First ensure backend is using MCP
    print("📋 Pre-flight check:")
    print("   Make sure backend/.env has:")
    print("   - USE_MCP=true")
    print("   - MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp")
    print("")
    
    test_backend_flow() 