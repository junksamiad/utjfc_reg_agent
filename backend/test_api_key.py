#!/usr/bin/env python3
"""
Test script to check what OpenAI API key is being loaded from environment
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def test_openai_key():
    print("=== OpenAI API Key Test ===\n")
    
    # Load environment variables the same way as the main app
    load_dotenv()
    
    # Check what key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        # Mask the key for security (show first 8 and last 4 characters)
        if len(api_key) > 12:
            masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        else:
            masked_key = "***MASKED***"
        print(f"✅ API Key loaded: {masked_key}")
        print(f"✅ Key length: {len(api_key)} characters")
        
        # Test if the key works with a simple API call
        try:
            client = OpenAI()
            print("\n🔄 Testing API key with simple call...")
            
            # Make a very simple call to test authentication
            response = client.models.list()
            print("✅ API key is VALID - authentication successful!")
            
        except Exception as e:
            print(f"❌ API key is INVALID - Error: {str(e)}")
            
    else:
        print("❌ No OPENAI_API_KEY found in environment")
        print("📋 Available environment variables starting with 'OPENAI':")
        for key in os.environ:
            if key.startswith("OPENAI"):
                print(f"   - {key}")
    
    print(f"\n📁 Current working directory: {os.getcwd()}")
    print(f"📄 .env file exists: {os.path.exists('.env')}")

if __name__ == "__main__":
    test_openai_key() 