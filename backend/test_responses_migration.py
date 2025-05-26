"""
Test script to verify the Responses API migration works correctly,
especially with tool calling functionality.
"""

from responses import chat_loop_1
from agents import Agent
from tools.airtable.airtable_agent import AirtableAgent

def test_basic_conversation():
    """Test basic conversation without tools"""
    print("=== Testing Basic Conversation ===")
    
    agent = Agent(instructions="You are a helpful assistant. Be concise.")
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    
    response = chat_loop_1(agent, messages)
    
    if hasattr(response, 'output_text'):
        print(f"✅ Basic conversation works: {response.output_text}")
        return True
    else:
        print("❌ Basic conversation failed")
        return False

def test_tool_calling():
    """Test tool calling functionality"""
    print("\n=== Testing Tool Calling ===")
    
    try:
        # Test with the existing Airtable tool
        agent = Agent(
            instructions="You are a helpful assistant with access to Airtable database operations.",
            tools=["airtable_database_operation"]  # Use the existing tool name
        )
        
        # Test message that should trigger a tool call
        messages = [{"role": "user", "content": "Can you search for registrations in season 2526?"}]
        
        response = chat_loop_1(agent, messages)
        
        if hasattr(response, 'output_text'):
            print(f"✅ Tool calling works: {response.output_text}")
            return True
        else:
            print("❌ Tool calling failed - no output_text")
            print(f"Response type: {type(response)}")
            if hasattr(response, 'output'):
                print(f"Output length: {len(response.output)}")
                for i, item in enumerate(response.output):
                    print(f"  Item {i}: {type(item)} - {getattr(item, 'type', 'no type')}")
            return False
            
    except Exception as e:
        print(f"❌ Tool calling test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_history():
    """Test that conversation history is maintained correctly"""
    print("\n=== Testing Conversation History ===")
    
    agent = Agent(instructions="You are a helpful assistant. Remember what we talked about.")
    
    # First message
    messages = [{"role": "user", "content": "My name is Alice"}]
    response1 = chat_loop_1(agent, messages)
    
    if hasattr(response1, 'output_text'):
        # Add response to history
        messages.append({"role": "assistant", "content": response1.output_text})
        
        # Second message referencing the first
        messages.append({"role": "user", "content": "What's my name?"})
        response2 = chat_loop_1(agent, messages)
        
        if hasattr(response2, 'output_text'):
            if "Alice" in response2.output_text:
                print(f"✅ Conversation history works: {response2.output_text}")
                return True
            else:
                print(f"❌ Conversation history failed - name not remembered: {response2.output_text}")
                return False
        else:
            print("❌ Second response failed")
            return False
    else:
        print("❌ First response failed")
        return False

if __name__ == "__main__":
    print("Testing Responses API Migration\n")
    
    results = []
    results.append(test_basic_conversation())
    results.append(test_tool_calling())
    results.append(test_conversation_history())
    
    print(f"\n=== Test Results ===")
    print(f"Basic Conversation: {'✅' if results[0] else '❌'}")
    print(f"Tool Calling: {'✅' if results[1] else '❌'}")
    print(f"Conversation History: {'✅' if results[2] else '❌'}")
    
    if all(results):
        print("\n🎉 All tests passed! Responses API migration successful!")
    else:
        print(f"\n⚠️  {sum(results)}/{len(results)} tests passed. Some issues need attention.") 