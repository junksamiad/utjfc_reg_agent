#!/usr/bin/env python3
"""
Minimal test of OpenAI Responses API with MCP - Testing the ID fix
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import time

# Enable debug logging
os.environ['OPENAI_LOG'] = 'debug'

load_dotenv()

client = OpenAI()

def test_minimal_mcp():
    print("🧪 Testing MCP After ID Fix")
    print("=" * 50)
    
    # Test 1: Simple test_connection tool
    print("\n1️⃣ Testing test_connection tool:")
    start_time = time.time()
    
    try:
        response = client.responses.create(
            model="gpt-4.1",
            input="Use the test_connection tool with message 'ID fix test'",
            tools=[{
                "type": "mcp",
                "server_label": "utjfc_registration",
                "server_url": "https://utjfc-mcp-server.replit.app/mcp",
                "require_approval": "never",
                "allowed_tools": ["test_connection"]
            }]
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ Response received in {elapsed:.2f}s!")
        
        if hasattr(response, 'output_text') and response.output_text:
            print(f"   Output: {response.output_text[:200]}...")
        else:
            print(f"   Response: {response}")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Error after {elapsed:.2f}s: {type(e).__name__}: {e}")
    
    # Test 2: Airtable tool
    print("\n2️⃣ Testing airtable_database_operation tool:")
    start_time = time.time()
    
    try:
        response = client.responses.create(
            model="gpt-4.1",
            input="How many players are registered for season 2526?",
            tools=[{
                "type": "mcp",
                "server_label": "utjfc_registration",
                "server_url": "https://utjfc-mcp-server.replit.app/mcp",
                "require_approval": "never",
                "allowed_tools": ["airtable_database_operation"]
            }]
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ Response received in {elapsed:.2f}s!")
        
        if hasattr(response, 'output_text') and response.output_text:
            print(f"   Output: {response.output_text}")
        else:
            print(f"   Response: {response}")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Error after {elapsed:.2f}s: {type(e).__name__}: {e}")
    
    print("\n✨ Test complete!")

if __name__ == "__main__":
    test_minimal_mcp() 