#!/usr/bin/env python3
"""
Test script for structured output implementation with Responses API.
Tests both local and MCP modes to ensure the agent_final_response is extracted correctly.
"""

import json
from agents import Agent
from responses import chat_loop_1
from agent_response_schema import AgentResponse

def test_structured_output():
    """Test structured output with a simple query"""
    
    print("=== Testing Structured Output Implementation ===\n")
    
    # Test with local agent
    print("1. Testing Local Function Calling Mode")
    print("-" * 40)
    
    local_agent = Agent(
        name="Test Local Agent",
        model="gpt-4.1",
        instructions="You are a helpful assistant. Always respond in the structured format with your final response in the agent_final_response field.",
        tools=[],  # No tools for simple test
        use_mcp=False
    )
    
    test_messages = [
        {"role": "user", "content": "What is 2 + 2?"}
    ]
    
    print(f"Agent: {local_agent.name}")
    print(f"Model: {local_agent.model}")
    print(f"MCP Mode: {local_agent.use_mcp}")
    print(f"Test Query: {test_messages[0]['content']}")
    print()
    
    try:
        response = chat_loop_1(local_agent, test_messages)
        print("Raw Response Object:")
        print(f"Type: {type(response)}")
        
        if hasattr(response, 'output_text'):
            print(f"Output Text: {response.output_text}")
            
            # Try to parse as structured output
            try:
                structured = json.loads(response.output_text)
                if isinstance(structured, dict) and 'agent_final_response' in structured:
                    print(f"✅ Structured Output Detected!")
                    print(f"Agent Final Response: {structured['agent_final_response']}")
                else:
                    print(f"❌ No agent_final_response field found")
                    print(f"Available fields: {list(structured.keys()) if isinstance(structured, dict) else 'Not a dict'}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"Raw text: {response.output_text}")
        else:
            print("❌ No output_text found in response")
            print(f"Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
    except Exception as e:
        print(f"❌ Error testing local mode: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with MCP agent (if available)
    print("2. Testing MCP Mode")
    print("-" * 40)
    
    try:
        mcp_agent = Agent.create_mcp_agent(
            name="Test MCP Agent",
            instructions="You are a helpful assistant. Always respond in the structured format with your final response in the agent_final_response field."
        )
        
        print(f"Agent: {mcp_agent.name}")
        print(f"Model: {mcp_agent.model}")
        print(f"MCP Mode: {mcp_agent.use_mcp}")
        print(f"MCP Server URL: {mcp_agent.mcp_server_url}")
        print(f"Test Query: {test_messages[0]['content']}")
        print()
        
        response = chat_loop_1(mcp_agent, test_messages)
        print("Raw Response Object:")
        print(f"Type: {type(response)}")
        
        if hasattr(response, 'output_text'):
            print(f"Output Text: {response.output_text}")
            
            # Try to parse as structured output
            try:
                structured = json.loads(response.output_text)
                if isinstance(structured, dict) and 'agent_final_response' in structured:
                    print(f"✅ Structured Output Detected!")
                    print(f"Agent Final Response: {structured['agent_final_response']}")
                else:
                    print(f"❌ No agent_final_response field found")
                    print(f"Available fields: {list(structured.keys()) if isinstance(structured, dict) else 'Not a dict'}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print(f"Raw text: {response.output_text}")
        else:
            print("❌ No output_text found in response")
            print(f"Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
    except Exception as e:
        print(f"❌ Error testing MCP mode: {e}")
        print("Note: MCP mode requires MCP server to be running")

def test_schema():
    """Test the Pydantic schema itself"""
    print("\n" + "="*50)
    print("3. Testing Pydantic Schema")
    print("-" * 40)
    
    # Test valid schema
    try:
        valid_response = AgentResponse(agent_final_response="Hello, this is a test response!")
        print(f"✅ Valid schema created: {valid_response.agent_final_response}")
        
        # Test JSON schema generation
        schema = AgentResponse.model_json_schema()
        print(f"✅ JSON Schema generated successfully")
        print(f"Schema keys: {list(schema.keys())}")
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
    
    # Test invalid schema (empty response)
    try:
        invalid_response = AgentResponse(agent_final_response="")
        print(f"❌ Should have failed validation for empty response")
    except Exception as e:
        print(f"✅ Correctly rejected empty response: {e}")

if __name__ == "__main__":
    test_structured_output()
    test_schema()
    print("\n" + "="*50)
    print("Test Complete!") 