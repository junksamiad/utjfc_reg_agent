#!/usr/bin/env python3
"""
Test backend with OpenAI debug logging enabled
"""

import os
import requests
import time

# Enable OpenAI debug logging
os.environ['OPENAI_LOG'] = 'debug'

BACKEND_URL = "http://localhost:8000"

def test_with_debug():
    print("🧪 Testing Backend with OpenAI Debug Logging")
    print("=" * 50)
    print("⚠️  OPENAI_LOG=debug is set - expect verbose output")
    print("")
    
    # Clear chat history
    requests.post(f"{BACKEND_URL}/clear")
    
    # Send simple test message
    test_message = "Just say hello"
    print(f"📤 Sending: {test_message}")
    print("")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"user_message": test_message},
            timeout=30  # 30 second timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n📥 Response received in {elapsed:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"AI says: {data.get('response', 'No response')}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n❌ Request timed out after {elapsed:.2f}s")
        print("Check the backend console for OpenAI debug output")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_with_debug() 