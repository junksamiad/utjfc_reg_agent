import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

# Test tool definition
test_tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country e.g. Paris, France"
            }
        },
        "required": ["location"],
        "additionalProperties": False
    }
}]

def mock_get_weather(location):
    """Mock weather function for testing"""
    return f"The weather in {location} is 22°C and sunny"

def test_responses_api():
    print("=== Testing Responses API ===\n")
    
    # Test 1: Basic input format
    print("1. Testing basic input format:")
    input_messages = [{"role": "user", "content": "What is the weather like in Paris today?"}]
    
    print("Input format:")
    print(json.dumps(input_messages, indent=2))
    
    response = client.responses.create(
        model="gpt-4o-mini",
        input=input_messages,
        tools=test_tools
    )
    
    print("\nRaw response object structure:")
    print(f"response.id: {response.id}")
    print(f"response.model: {response.model}")
    print(f"response.output type: {type(response.output)}")
    print(f"response.output length: {len(response.output)}")
    
    print("\nResponse output:")
    print(json.dumps([{
        "type": getattr(item, 'type', None),
        "role": getattr(item, 'role', None),
        "content": getattr(item, 'content', None),
        "name": getattr(item, 'name', None),
        "arguments": getattr(item, 'arguments', None),
        "call_id": getattr(item, 'call_id', None),
        "id": getattr(item, 'id', None)
    } for item in response.output], indent=2))
    
    # Test 2: Handle tool call and continue conversation
    print("\n\n2. Testing tool call handling:")
    
    if response.output and hasattr(response.output[0], 'type') and response.output[0].type == 'function_call':
        tool_call = response.output[0]
        print(f"Tool call detected: {tool_call.name}")
        print(f"Arguments: {tool_call.arguments}")
        
        # Execute the mock function
        args = json.loads(tool_call.arguments)
        result = mock_get_weather(args["location"])
        print(f"Function result: {result}")
        
        # Add tool call and result to conversation
        input_messages.append({
            "type": "function_call",
            "id": tool_call.id,
            "call_id": tool_call.call_id,
            "name": tool_call.name,
            "arguments": tool_call.arguments
        })
        
        input_messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": result
        })
        
        print("\nUpdated conversation history:")
        print(json.dumps(input_messages, indent=2))
        
        # Get final response
        response_2 = client.responses.create(
            model="gpt-4o-mini",
            input=input_messages,
            tools=test_tools
        )
        
        print("\nFinal response:")
        if hasattr(response_2, 'output_text'):
            print(response_2.output_text)
        else:
            print(json.dumps([{
                "type": getattr(item, 'type', None),
                "role": getattr(item, 'role', None),
                "content": getattr(item, 'content', None)
            } for item in response_2.output], indent=2))
    
    # Test 3: Regular conversation without tools
    print("\n\n3. Testing regular conversation:")
    
    conversation = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    response_3 = client.responses.create(
        model="gpt-4o-mini",
        input=conversation
    )
    
    print("Regular response structure:")
    for i, item in enumerate(response_3.output):
        print(f"Item {i}: type={type(item)}, class={item.__class__.__name__}")
        if hasattr(item, 'type'):
            print(f"  type: {item.type}")
        if hasattr(item, 'role'):
            print(f"  role: {item.role}")
        if hasattr(item, 'content'):
            print(f"  content: {item.content}")
        if hasattr(item, 'text'):
            print(f"  text: {item.text}")
    
    if hasattr(response_3, 'output_text'):
        print(f"\noutput_text: {response_3.output_text}")

if __name__ == "__main__":
    test_responses_api() 