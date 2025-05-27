#!/usr/bin/env python3
"""
Direct test of OpenAI Responses API
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def test_responses_api():
    """Test if Responses API is available in the OpenAI SDK"""
    print("🔍 Testing OpenAI Responses API Availability")
    print("=" * 60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Check if responses attribute exists
        print(f"✅ Client has 'responses' attribute: {hasattr(client, 'responses')}")
        
        if hasattr(client, 'responses'):
            print("\n📝 Testing basic Responses API call...")
            
            # Try the simplest possible call
            response = client.responses.create(
                model="gpt-4o",  # Try with standard model first
                input="Say hello"
            )
            
            print(f"✅ Response type: {type(response)}")
            print(f"✅ Has output_text: {hasattr(response, 'output_text')}")
            if hasattr(response, 'output_text'):
                print(f"✅ Output: {response.output_text}")
            
            return True
        else:
            print("❌ Client does not have 'responses' attribute")
            print(f"Available attributes: {[attr for attr in dir(client) if not attr.startswith('_')][:20]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        
        # Check if it's a model issue
        if "model" in str(e).lower():
            print("\n🔄 Retrying with gpt-4.1 model...")
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.responses.create(
                    model="gpt-4.1",
                    input="Say hello"
                )
                print(f"✅ Success with gpt-4.1!")
                return True
            except Exception as e2:
                print(f"❌ Also failed with gpt-4.1: {e2}")
        
        return False

def test_code_interpreter():
    """Test Responses API with code interpreter"""
    print("\n\n🔍 Testing Responses API with Code Interpreter")
    print("=" * 60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("📝 Testing with code interpreter tool...")
        
        response = client.responses.create(
            model="gpt-4o",  # Start with standard model
            instructions="You are a helpful assistant. Use Python to solve problems.",
            input="Calculate 2 + 2 using Python code",
            tools=[{
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }]
        )
        
        print(f"✅ Success!")
        print(f"Response type: {type(response)}")
        
        if hasattr(response, 'output_text'):
            print(f"Output: {response.output_text[:200]}...")
        
        if hasattr(response, 'output'):
            print(f"Output items: {len(response.output)}")
            for i, item in enumerate(response.output[:2]):
                print(f"  Item {i}: type={item.type if hasattr(item, 'type') else 'unknown'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        
        # If it's an API error, show more details
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
        
        return False

def main():
    print("🚀 Direct OpenAI Responses API Test")
    print("This tests the API locally, not through MCP")
    print("=" * 60)
    
    # Test 1: Basic availability
    basic_works = test_responses_api()
    
    # Test 2: With code interpreter
    if basic_works:
        code_interpreter_works = test_code_interpreter()
    else:
        print("\n⚠️  Skipping code interpreter test since basic API is not available")
        code_interpreter_works = False
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"- Responses API available: {'✅ Yes' if basic_works else '❌ No'}")
    print(f"- Code Interpreter works: {'✅ Yes' if code_interpreter_works else '❌ No'}")
    
    if not basic_works:
        print("\n⚠️  The Responses API might not be available in the public OpenAI SDK")
        print("This could be a beta feature that requires special access")

if __name__ == "__main__":
    main() 