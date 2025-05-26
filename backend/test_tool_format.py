"""
Test script to check tool format compatibility between Chat Completions and Responses API
"""

from agents import Agent
import json

def test_tool_format():
    print("=== Testing Tool Format ===")
    
    agent = Agent(tools=["airtable_database_operation"])
    
    # Get the tools as formatted for OpenAI
    tools = agent.get_tools_for_openai()
    
    print("Current tool format:")
    print(json.dumps(tools, indent=2))
    
    # Check if this matches Responses API format
    if tools and len(tools) > 0:
        tool = tools[0]
        print(f"\nTool structure:")
        print(f"- Has 'type': {'type' in tool}")
        print(f"- Has 'name': {'name' in tool}")
        print(f"- Has 'function': {'function' in tool}")
        
        if 'function' in tool:
            print(f"- Function has 'name': {'name' in tool['function']}")
            print(f"- Function has 'description': {'description' in tool['function']}")
            print(f"- Function has 'parameters': {'parameters' in tool['function']}")

if __name__ == "__main__":
    test_tool_format() 