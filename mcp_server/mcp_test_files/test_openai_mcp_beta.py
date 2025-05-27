#!/usr/bin/env python3
"""Test OpenAI MCP integration using the correct beta API"""

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
    print("🚀 Testing OpenAI MCP Integration with Beta API")
    print("=" * 50)
    
    # Create a response with MCP server configuration
    print("📤 Creating OpenAI response with MCP server...")
    
    try:
        # Use the responses API (not beta.responses)
        response = client.responses.create(
            model="gpt-4.1",
            input=[
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
            ]
        )
        
        print("✅ Response created successfully!")
        print(f"\n📥 Response ID: {response.id}")
        print(f"Model: {response.model}")
        
        # Check the output
        if hasattr(response, 'output_text') and response.output_text:
            print(f"\n📥 Assistant response:")
            print("-" * 50)
            print(response.output_text)
            print("-" * 50)
        elif hasattr(response, 'output') and response.output:
            print(f"\n📥 Response outputs:")
            for i, output in enumerate(response.output):
                print(f"\nOutput {i+1}:")
                print(f"  Type: {output.type}")
                if output.type == 'message' and hasattr(output, 'content'):
                    for content in output.content:
                        if hasattr(content, 'text'):
                            print(f"  Text: {content.text}")
                elif output.type == 'mcp_list_tools':
                    print(f"  Server: {output.server_label}")
                    print(f"  Tools: {len(output.tools)} available")
                    for tool in output.tools:
                        print(f"    - {tool['name']}: {tool.get('description', 'No description')}")
        
        # Test actual tool usage
        print("\n📤 Testing actual tool usage...")
        
        response2 = client.responses.create(
            model="gpt-4.1",
            input=[
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
            ]
        )
        
        print("\n📥 Response with tool usage:")
        print("-" * 50)
        
        if hasattr(response2, 'output_text') and response2.output_text:
            print(response2.output_text)
        elif hasattr(response2, 'output') and response2.output:
            for output in response2.output:
                if output.type == 'message' and hasattr(output, 'content'):
                    for content in output.content:
                        if hasattr(content, 'text'):
                            print(content.text)
                elif output.type == 'mcp_call':
                    print(f"\n🔧 MCP Tool Called:")
                    print(f"  Tool: {output.name}")
                    print(f"  Arguments: {output.arguments}")
                    if hasattr(output, 'output'):
                        print(f"  Result: {output.output}")
        
        print("-" * 50)
        print("\n✅ OpenAI MCP integration test completed!")
        
    except AttributeError as e:
        print(f"\n❌ AttributeError: {e}")
        print("\nThe OpenAI SDK might not have the 'responses' API yet.")
        print("This could be a beta or internal API that's not publicly available.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

if __name__ == "__main__":
    test_openai_mcp_integration() 