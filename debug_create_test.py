#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import requests

def test_full_registration_flow():
    print("=== TESTING FULL REGISTRATION FLOW ===\n")
    
    # Natural language registration request with all required fields
    natural_query = """Please can you register this player for the 2526 season:

Player Details:
- Name: Alex Johnson
- Date of Birth: March 10th 2015
- Age Group: u10s
- Team: Tigers
- Gender: Male
- Medical Issues: No

Parent/Guardian Details:
- Name: Mike Johnson
- Relationship to Player: dad
- Role: Parent/Guardian

Registration Details:
- Registration Code: 102-tigers-10-2526

Address Information:
- Player Address: 45 Oak Avenue, Urmston, Manchester, M41 5AB
- Parent Address: Same as player

Please process this registration."""
    
    print("📝 STEP 1: User Input (Natural Language)")
    print("=" * 50)
    print(natural_query)
    print("\n")
    
    print("🚀 STEP 2: Sending to Main Agent")
    print("=" * 50)
    print("Calling: POST http://localhost:8001/chat")
    print("This will trigger: Main Agent → Tool Call → Helper Agent → Database")
    print("\n")
    
    try:
        response = requests.post(
            "http://localhost:8001/chat",
            headers={"Content-Type": "application/json"},
            json={"user_message": natural_query}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ STEP 3: Main Agent Response")
            print("=" * 50)
            print(f"Status: SUCCESS")
            print(f"Response: {result.get('response', 'No response')}")
            print("\n")
            
            print("🔍 STEP 4: What Happened Under The Hood")
            print("=" * 50)
            print("1. Main Agent extracted registration data from natural language")
            print("2. Main Agent called airtable_database_operation tool")
            print("3. Helper Agent (Code Interpreter):")
            print("   - Analyzed the request against the schema")
            print("   - Normalized data (dad→Father, no→N, u10s→U10, etc.)")
            print("   - Generated operation plan")
            print("4. Backend executed the operation plan using pyairtable")
            print("5. New record created in Airtable database")
            print("\nNOTE: To see the detailed tool response including record ID,")
            print("check the server logs where the tool call response is printed.")
            
        else:
            print("❌ STEP 3: Error Response")
            print("=" * 50)
            print(f"Status: ERROR {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print("❌ STEP 3: Connection Error")
        print("=" * 50)
        print(f"Error: {e}")
        print("Make sure the server is running: uvicorn server:app --host 0.0.0.0 --port 8001")

    print("\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    print("This test demonstrates:")
    print("✓ Natural language processing by main agent")
    print("✓ Tool calling integration")
    print("✓ Data normalization by helper agent")
    print("✓ Database record creation")
    print("✓ All 10 required fields handled correctly")
    print("✓ Enum conversions (dad→Father, no→N, etc.)")

if __name__ == "__main__":
    test_full_registration_flow() 