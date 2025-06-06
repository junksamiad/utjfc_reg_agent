#!/usr/bin/env python3
"""
Test script for registration routing and validation functionality
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from registration_agent.routing_validation import parse_registration_code, validate_team_and_age_group, route_registration_request

def test_code_parsing():
    """Test registration code parsing functionality"""
    print("=== Testing Registration Code Parsing ===")
    
    test_cases = [
        # Valid 100 codes (re-registration)
        ("100-tigers-u10-2526-john-smith", True, "re_registration"),
        ("100-Lions-U12-2526-Emma-Jones", True, "re_registration"),
        ("100-EAGLES-u8-2526-bob-brown", True, "re_registration"),
        
        # Valid 200 codes (new registration)
        ("200-tigers-u10-2526", True, "new_registration"),
        ("200-Lions-U12-2526", True, "new_registration"),
        ("200-eagles-u8-2526", True, "new_registration"),
        
        # Invalid codes
        ("100-tigers-u10-2526", False, None),  # Missing player name for 100
        ("200-tigers-u10-2526-john-smith", False, None),  # Has player name for 200
        ("100-tigers-u10-2525-john-smith", False, None),  # Wrong season
        ("300-tigers-u10-2526", False, None),  # Invalid prefix
        ("hello world", False, None),  # Not a code at all
        ("100-tigers-10-2526-john-smith", False, None),  # Missing 'u' in age group
    ]
    
    for test_input, should_be_valid, expected_route in test_cases:
        print(f"\nTesting: '{test_input}'")
        
        result = parse_registration_code(test_input)
        
        if should_be_valid:
            if result is None:
                print(f"  ❌ FAIL: Expected valid code but got None")
            else:
                print(f"  ✅ PASS: Parsed successfully")
                print(f"     Prefix: {result['prefix']}")
                print(f"     Team: {result['team']}")
                print(f"     Age Group: {result['age_group']}")
                print(f"     Season: {result['season']}")
                print(f"     Player Name: {result['player_name']}")
                
                # Test routing
                route = route_registration_request(result)
                if route == expected_route:
                    print(f"  ✅ ROUTING PASS: {route}")
                else:
                    print(f"  ❌ ROUTING FAIL: Expected {expected_route}, got {route}")
        else:
            if result is None:
                print(f"  ✅ PASS: Correctly rejected invalid code")
            else:
                print(f"  ❌ FAIL: Should have been rejected but was parsed as: {result}")

def test_team_validation():
    """Test team and age group validation against Airtable"""
    print("\n\n=== Testing Team Validation ===")
    
    # Test some combinations (you may need to adjust these based on your actual data)
    test_cases = [
        ("tigers", "u10"),  # This should exist in your team_info table
        ("lions", "u12"),   # Adjust based on your data
        ("eagles", "u8"),   # Adjust based on your data
        ("nonexistent", "u10"),  # This should not exist
        ("tigers", "u25"),  # Age group that probably doesn't exist
    ]
    
    for team, age_group in test_cases:
        print(f"\nTesting team validation: {team} {age_group}")
        
        try:
            is_valid = validate_team_and_age_group(team, age_group)
            print(f"  Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

if __name__ == "__main__":
    print("Testing Registration Routing and Validation")
    print("=" * 50)
    
    # Test code parsing
    test_code_parsing()
    
    # Test team validation (requires Airtable access)
    test_team_validation()
    
    print("\n" + "=" * 50)
    print("Test completed!") 