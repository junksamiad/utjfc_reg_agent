#!/usr/bin/env python3
"""
Simple test to debug OpenAI's connection to the MCP server
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import time

# Load environment variables
load_dotenv()

# Configuration
MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_openai_basic():
    """Test basic OpenAI call without MCP"""
    print("🔍 Testing basic OpenAI call (no MCP)...")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello, OpenAI is working!'"}],
            max_tokens=50
        )
        print(f"✅ Basic OpenAI call works: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Basic OpenAI call failed: {e}")
        return False

def test_openai_mcp_minimal():
    """Test minimal MCP connection"""
    print("\n🔍 Testing minimal MCP connection...")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        print(f"📡 Connecting to MCP server at: {MCP_SERVER_URL}/mcp")
        print("⏳ Creating response with MCP tool (10 second timeout)...")
        
        start_time = time.time()
        
        # Use a timeout
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{
                "type": "mcp",
                "server_label": "test_mcp",
                "server_url": f"{MCP_SERVER_URL}/mcp",
                "require_approval": "never"
            }],
            input="Just say hello",
            timeout=10.0  # 10 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"✅ MCP connection successful! (took {elapsed:.2f}s)")
        print(f"Response ID: {response.id}")
        
        # Check for MCP outputs
        if hasattr(response, 'output'):
            for output in response.output:
                print(f"Output type: {output.type}")
                if output.type == 'mcp_list_tools':
                    print(f"✅ Tools retrieved from MCP server!")
                    print(f"   Server: {output.server_label}")
                    print(f"   Number of tools: {len(output.tools) if hasattr(output, 'tools') else 0}")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ MCP connection failed after {elapsed:.2f}s: {type(e).__name__}: {e}")
        return False

def main():
    print("🚀 Simple OpenAI MCP Test")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set!")
        return
    
    # Test 1: Basic OpenAI
    if not test_openai_basic():
        print("\n⚠️  Basic OpenAI is not working. Check your API key.")
        return
    
    # Test 2: MCP connection
    test_openai_mcp_minimal()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    main() 