#!/usr/bin/env python3
"""
Test tool integration and registration
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_tool_registration():
    """Test that our new tool is properly registered"""
    print("Testing tool registration...")
    
    try:
        # Test importing from __init__.py
        from registration_agent.tools.registration_tools import (
            check_if_record_exists_in_db,
            CHECK_IF_RECORD_EXISTS_IN_DB_TOOL,
            handle_check_if_record_exists_in_db
        )
        print("✅ Successfully imported from __init__.py")
        
        # Test agent integration
        from registration_agent.registration_agents import new_registration_agent
        print("✅ Successfully imported new_registration_agent")
        
        # Check if our tool is in the agent's tools list
        agent_tools = new_registration_agent.tools
        if "check_if_record_exists_in_db" in agent_tools:
            print("✅ Tool is registered in new_registration_agent.tools")
        else:
            print("❌ Tool NOT found in new_registration_agent.tools")
            print(f"Available tools: {agent_tools}")
        
        # Test getting OpenAI tools
        openai_tools = new_registration_agent.get_tools_for_openai()
        tool_names = [tool.get('name') for tool in openai_tools if tool.get('type') == 'function']
        
        if "check_if_record_exists_in_db" in tool_names:
            print("✅ Tool schema is available for OpenAI")
        else:
            print("❌ Tool schema NOT found in OpenAI tools")
            print(f"Available function tools: {tool_names}")
        
        # Test function handlers
        tool_functions = new_registration_agent.get_tool_functions()
        if "check_if_record_exists_in_db" in tool_functions:
            print("✅ Tool handler is registered")
        else:
            print("❌ Tool handler NOT found")
            print(f"Available handlers: {list(tool_functions.keys())}")
        
        # Test the tool schema structure
        print(f"\n📋 Tool Schema Check:")
        print(f"Tool name: {CHECK_IF_RECORD_EXISTS_IN_DB_TOOL.get('name')}")
        print(f"Tool type: {CHECK_IF_RECORD_EXISTS_IN_DB_TOOL.get('type')}")
        
        params = CHECK_IF_RECORD_EXISTS_IN_DB_TOOL.get('parameters', {})
        required_params = params.get('required', [])
        print(f"Required parameters: {required_params}")
        
        if set(required_params) == {"player_full_name", "parent_full_name"}:
            print("✅ Required parameters are correct")
        else:
            print("❌ Required parameters are incorrect")
        
        print("\n🎉 Tool integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_tool_registration()