"""
Responses API Analysis - Understanding the key differences from Chat Completions API

This script demonstrates:
1. Input format differences
2. Output format differences  
3. Tool calling workflow
4. Conversation history management
5. How to maintain compatibility with existing frontend
"""

import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def analyze_responses_api():
    print("=== RESPONSES API ANALYSIS ===\n")
    
    # 1. INPUT FORMAT ANALYSIS
    print("1. INPUT FORMAT:")
    print("   Chat Completions API uses: messages=[{role, content}]")
    print("   Responses API uses: input=[{role, content}] or input='string'")
    print()
    
    # Test both input formats
    input_array = [{"role": "user", "content": "Hello"}]
    input_string = "Hello"
    
    print("   Array format:", json.dumps(input_array))
    print("   String format:", repr(input_string))
    print()
    
    # 2. OUTPUT FORMAT ANALYSIS
    print("2. OUTPUT FORMAT:")
    
    # Test regular message
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Say hello back"
    )
    
    print("   Regular message response:")
    print(f"   - response.id: {response.id}")
    print(f"   - response.output type: {type(response.output)}")
    print(f"   - response.output_text: {response.output_text}")
    print(f"   - First output item type: {type(response.output[0])}")
    print(f"   - First output item class: {response.output[0].__class__.__name__}")
    print()
    
    # 3. TOOL CALLING ANALYSIS
    print("3. TOOL CALLING:")
    
    tools = [{
        "type": "function",
        "name": "calculate",
        "description": "Perform basic math calculation",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression like '2+2'"}
            },
            "required": ["expression"]
        }
    }]
    
    tool_response = client.responses.create(
        model="gpt-4o-mini",
        input="What is 15 + 27?",
        tools=tools
    )
    
    print("   Tool call response:")
    print(f"   - Output length: {len(tool_response.output)}")
    tool_call = tool_response.output[0]
    print(f"   - Tool call type: {tool_call.type}")
    print(f"   - Tool call name: {tool_call.name}")
    print(f"   - Tool call arguments: {tool_call.arguments}")
    print(f"   - Tool call_id: {tool_call.call_id}")
    print()
    
    # 4. CONVERSATION HISTORY MANAGEMENT
    print("4. CONVERSATION HISTORY MANAGEMENT:")
    print("   Key difference: Responses API requires explicit conversation building")
    print()
    
    # Build conversation manually (like your current system)
    conversation = [
        {"role": "user", "content": "What is 15 + 27?"}
    ]
    
    # Add tool call to conversation
    conversation.append({
        "type": "function_call",
        "id": tool_call.id,
        "call_id": tool_call.call_id,
        "name": tool_call.name,
        "arguments": tool_call.arguments
    })
    
    # Add tool result
    conversation.append({
        "type": "function_call_output", 
        "call_id": tool_call.call_id,
        "output": "42"  # Mock result
    })
    
    print("   Conversation history format:")
    print(json.dumps(conversation, indent=2))
    print()
    
    # Get final response
    final_response = client.responses.create(
        model="gpt-4o-mini",
        input=conversation,
        tools=tools
    )
    
    print(f"   Final response: {final_response.output_text}")
    print()
    
    # 5. COMPATIBILITY WITH EXISTING SYSTEM
    print("5. COMPATIBILITY ANALYSIS:")
    print("   Your current system advantages:")
    print("   ✓ Manual conversation history management")
    print("   ✓ Frontend expects {role, content} format")
    print("   ✓ Tool calling already structured")
    print()
    print("   Required changes for Responses API:")
    print("   • Change client.chat.completions.create() → client.responses.create()")
    print("   • Change 'messages' parameter → 'input' parameter")
    print("   • Handle response.output instead of response.choices[0].message")
    print("   • Extract text from response.output_text or response.output[0].content[0].text")
    print("   • Tool calls have different structure (type='function_call' vs tool_calls)")
    print()

def demonstrate_conversion():
    print("=== CONVERSION EXAMPLE ===\n")
    
    print("BEFORE (Chat Completions API):")
    print("""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
        tools=tools
    )
    
    # Access response
    message = response.choices[0].message
    content = message.content
    tool_calls = message.tool_calls
    """)
    
    print("AFTER (Responses API):")
    print("""
    response = client.responses.create(
        model="gpt-4o-mini", 
        input=[{"role": "user", "content": "Hello"}],
        tools=tools
    )
    
    # Access response
    content = response.output_text
    # OR for more control:
    if response.output[0].type == 'message':
        content = response.output[0].content[0].text
    elif response.output[0].type == 'function_call':
        tool_call = response.output[0]
    """)

if __name__ == "__main__":
    analyze_responses_api()
    demonstrate_conversion() 