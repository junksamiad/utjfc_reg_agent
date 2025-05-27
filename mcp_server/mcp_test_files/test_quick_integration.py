#!/usr/bin/env python3
"""
Quick Integration Test - Non-blocking version
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000"
MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_quick_chat():
    """Test a quick chat interaction"""
    print("🧪 Quick Integration Test")
    print("=" * 40)
    
    # Clear history
    requests.post(f"{BACKEND_URL}/clear")
    
    # Send test message
    test_message = "How many players are registered for season 2526?"
    print(f"\n📤 Sending: {test_message}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"user_message": test_message},
            timeout=45  # 45 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            print(f"\n📥 AI Response:")
            print(f"{ai_response}")
            
            # Check if response indicates MCP was used
            if "registration" in ai_response.lower() or "player" in ai_response.lower():
                print("\n✅ Success! MCP integration is working.")
            else:
                print("\n⚠️  Response received but may not have used MCP tools.")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.Timeout:
        print("\n⏱️  Request timed out after 45 seconds")
        print("This might mean the MCP server is processing the request.")
        print("Check the MCP server logs for activity.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_quick_chat() 