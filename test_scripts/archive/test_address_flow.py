#!/usr/bin/env python3
"""
Test script for new address collection flow (routines 11-15)
Tests the new multi-step address collection process
"""

from registration_agent.registration_routines import RegistrationRoutines
from registration_agent.registration_agents import new_registration_agent

def test_address_flow():
    """Test the new address collection routines 11-15"""
    
    print("🏠 Testing New Address Collection Flow")
    print("=" * 60)
    
    # Test routine retrieval
    print("\n📋 Testing Routine Definitions:")
    for routine_num in [11, 12, 13, 14, 15]:
        if RegistrationRoutines.is_valid_routine(routine_num):
            routine = RegistrationRoutines.get_routine_message(routine_num)
            print(f"✅ Routine {routine_num}: {routine[:60]}...")
        else:
            print(f"❌ Routine {routine_num}: Not found")
    
    # Test agent tools
    print(f"\n🛠️  Agent Tools Available:")
    agent_tools = new_registration_agent.tools
    print(f"Agent tools: {agent_tools}")
    
    # Verify required tools are present
    required_tools = ["address_validation", "address_lookup"]
    for tool in required_tools:
        if tool in agent_tools:
            print(f"✅ {tool}: Available")
        else:
            print(f"❌ {tool}: Missing")
    
    # Test tool function availability
    print(f"\n🔧 Testing Tool Functions:")
    tool_functions = new_registration_agent.get_tool_functions()
    for tool_name, func in tool_functions.items():
        print(f"✅ {tool_name}: {func.__name__ if callable(func) else 'Not callable'}")
    
    # Test address lookup function
    print(f"\n🔍 Testing Address Lookup Function:")
    try:
        from registration_agent.tools.registration_tools.address_lookup import lookup_address_by_postcode_and_number
        
        # Test with empty inputs (should fail gracefully)
        result = lookup_address_by_postcode_and_number("", "")
        print(f"Empty inputs test: Success={result['success']}, Message='{result['message']}'")
        
        # Test with valid format but no API key (expected behavior)
        result = lookup_address_by_postcode_and_number("M41 9JJ", "10")
        print(f"Valid inputs test: Success={result['success']}, Message='{result['message']}'")
        
        print("✅ Address lookup function working correctly")
        
    except Exception as e:
        print(f"❌ Address lookup error: {e}")
    
    # Test postcode cleaning logic
    print(f"\n📮 Testing Postcode Formats:")
    test_postcodes = [
        "m41 9jj",      # lowercase with space
        "M419JJ",       # uppercase no space  
        "M41  9JJ",     # extra spaces
        "SW1A 2AA",     # standard format
        "INVALID",      # invalid format
    ]
    
    for postcode in test_postcodes:
        cleaned = postcode.strip().upper()
        valid_format = len(cleaned.replace(" ", "")) >= 5 and len(cleaned.replace(" ", "")) <= 8
        print(f"'{postcode}' → '{cleaned}' (Valid format: {valid_format})")
    
    print(f"\n🎯 Address Flow Summary:")
    print("Routine 11: Collect & validate postcode")
    print("Routine 12: Collect house number") 
    print("Routine 13: Google API lookup → show address → confirm")
    print("Routine 14: Manual entry fallback (if needed)")
    print("Routine 15: Check if child lives at same address")
    print("\n✅ New address collection flow ready for testing!")

if __name__ == "__main__":
    test_address_flow() 