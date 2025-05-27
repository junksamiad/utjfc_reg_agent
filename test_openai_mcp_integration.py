#!/usr/bin/env python3
"""Test OpenAI integration with the deployed MCP server"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_openai_mcp_integration():
    """Test if OpenAI can connect to and use the MCP server"""
    print("🚀 Testing OpenAI MCP Integration")
    print("=" * 50)
    
    # Create a response with MCP server configuration
    print("📤 Creating OpenAI response with MCP server...")
    
    try:
        response = client.beta.responses.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant with access to UTJFC registration tools via MCP."
                },
                {
                    "role": "user",
                    "content": "Can you check what tools are available to you? List them and describe what they do."
                }
            ],
            tools=[
                {
                    "type": "mcp",
                    "server_label": "utjfc_registration",
                    "server_url": "https://utjfc-mcp-server.replit.app/mcp",
                    "require_approval": "never"
                }
            ],
            stream=True
        )
        
        print("✅ Response created successfully!")
        print("\n📥 Assistant response:")
        print("-" * 50)
        
        # Collect the full response
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n" + "-" * 50)
        
        # Test actual tool usage
        print("\n📤 Testing actual tool usage...")
        
        response2 = client.beta.responses.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant with access to UTJFC registration tools via MCP."
                },
                {
                    "role": "user",
                    "content": "Please use the airtable tool to check how many players are registered for the 2526 season."
                }
            ],
            tools=[
                {
                    "type": "mcp",
                    "server_label": "utjfc_registration",
                    "server_url": "https://utjfc-mcp-server.replit.app/mcp",
                    "require_approval": "never"
                }
            ],
            stream=True
        )
        
        print("\n📥 Assistant response with tool usage:")
        print("-" * 50)
        
        for chunk in response2:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
            
            # Check for tool calls
            if hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    if tool_call.function:
                        print(f"\n🔧 Tool called: {tool_call.function.name}")
                        if tool_call.function.arguments:
                            print(f"   Arguments: {tool_call.function.arguments}")
        
        print("\n" + "-" * 50)
        print("\n✅ OpenAI MCP integration test completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

if __name__ == "__main__":
    test_openai_mcp_integration() 