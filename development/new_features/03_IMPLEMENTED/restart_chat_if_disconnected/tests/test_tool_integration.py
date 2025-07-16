#!/usr/bin/env python3
"""
Tool integration tests for the restart chat feature

Run from project root:
python development/new_features/restart_chat_if_disconnected/tests/test_tool_integration.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
project_root = Path(__file__).parent.parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

def test_tool_integration():
    """Test tool integration and registration"""
    print("🔧 TOOL INTEGRATION TESTS")
    print("=" * 40)
    
    try:
        # Test 1: Import from __init__.py
        print("\n1️⃣ Testing Package Imports...")
        test_package_imports()
        
        # Test 2: Agent registration
        print("\n2️⃣ Testing Agent Registration...")
        test_agent_registration()
        
        # Test 3: OpenAI tool schema
        print("\n3️⃣ Testing OpenAI Schema...")
        test_openai_schema()
        
        # Test 4: Function handlers
        print("\n4️⃣ Testing Function Handlers...")
        test_function_handlers()
        
        # Test 5: Tool execution
        print("\n5️⃣ Testing Tool Execution...")
        test_tool_execution()
        
        print("\n✅ Tool integration tests completed!")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

def test_package_imports():
    """Test importing from the tools package"""
    try:
        from registration_agent.tools.registration_tools import (
            check_if_record_exists_in_db,
            CHECK_IF_RECORD_EXISTS_IN_DB_TOOL,
            handle_check_if_record_exists_in_db
        )
        print("   ✅ Successfully imported from __init__.py")
        print(f"   - Core function: {check_if_record_exists_in_db.__name__}")
        print(f"   - Tool schema: {CHECK_IF_RECORD_EXISTS_IN_DB_TOOL.get('name')}")
        print(f"   - Handler: {handle_check_if_record_exists_in_db.__name__}")
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        raise

def test_agent_registration():
    """Test that the tool is registered in the agent"""
    try:
        from registration_agent.registration_agents import new_registration_agent
        
        # Check tools list
        agent_tools = new_registration_agent.tools
        if "check_if_record_exists_in_db" in agent_tools:
            print("   ✅ Tool is in new_registration_agent.tools")
        else:
            print("   ❌ Tool NOT in new_registration_agent.tools")
            print(f"   Available tools: {agent_tools}")
            
        # Check tool count
        print(f"   Total tools registered: {len(agent_tools)}")
        
    except Exception as e:
        print(f"   ❌ Agent registration test failed: {e}")
        raise

def test_openai_schema():
    """Test OpenAI tool schema generation"""
    try:
        from registration_agent.registration_agents import new_registration_agent
        
        # Get OpenAI tools
        openai_tools = new_registration_agent.get_tools_for_openai()
        
        # Find our tool
        our_tool = None
        for tool in openai_tools:
            if tool.get('name') == 'check_if_record_exists_in_db':
                our_tool = tool
                break
        
        if our_tool:
            print("   ✅ Tool schema found in OpenAI tools")
            print(f"   - Name: {our_tool.get('name')}")
            print(f"   - Type: {our_tool.get('type')}")
            
            # Check parameters
            params = our_tool.get('parameters', {})
            required = params.get('required', [])
            print(f"   - Required params: {required}")
            
            if set(required) == {"player_full_name", "parent_full_name"}:
                print("   ✅ Required parameters are correct")
            else:
                print("   ❌ Required parameters are incorrect")
                
        else:
            print("   ❌ Tool schema NOT found in OpenAI tools")
            tool_names = [t.get('name') for t in openai_tools if t.get('type') == 'function']
            print(f"   Available tools: {tool_names}")
            
    except Exception as e:
        print(f"   ❌ OpenAI schema test failed: {e}")
        raise

def test_function_handlers():
    """Test function handler registration"""
    try:
        from registration_agent.registration_agents import new_registration_agent
        
        # Get function handlers
        handlers = new_registration_agent.get_tool_functions()
        
        if "check_if_record_exists_in_db" in handlers:
            print("   ✅ Function handler is registered")
            
            # Test handler is callable
            handler = handlers["check_if_record_exists_in_db"]
            if callable(handler):
                print("   ✅ Handler is callable")
            else:
                print("   ❌ Handler is not callable")
                
        else:
            print("   ❌ Function handler NOT registered")
            print(f"   Available handlers: {list(handlers.keys())}")
            
    except Exception as e:
        print(f"   ❌ Function handler test failed: {e}")
        raise

def test_tool_execution():
    """Test tool execution through handler"""
    try:
        from registration_agent.registration_agents import new_registration_agent
        
        # Get the handler
        handlers = new_registration_agent.get_tool_functions()
        handler = handlers.get("check_if_record_exists_in_db")
        
        if handler:
            # Test execution with safe data
            result = handler(
                parent_full_name="Test Parent",
                player_full_name="Test Player"
            )
            
            if result.get('success') is not None:
                print("   ✅ Tool executes successfully through handler")
                print(f"   - Success: {result.get('success')}")
                print(f"   - Record Found: {result.get('record_found')}")
            else:
                print("   ❌ Tool execution failed")
                print(f"   - Result: {result}")
                
        else:
            print("   ❌ Handler not found")
            
    except Exception as e:
        print(f"   ❌ Tool execution test failed: {e}")
        raise

if __name__ == "__main__":
    test_tool_integration()