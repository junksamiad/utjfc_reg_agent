#!/usr/bin/env python3
"""
Final test of the complete registration validation system
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from registration_agent.routing_validation import parse_registration_code, validate_team_and_age_group, route_registration_request

def test_complete_flow():
    """Test the complete registration code validation flow"""
    print("=== Testing Complete Registration Flow ===")
    
    # Test cases with real teams from the table
    test_cases = [
        # Valid codes that should work based on the table data
        ("200-tigers-u13-2526", True, "new_registration"),  # Tigers u13s exists
        ("100-tigers-u13-2526-john-smith", True, "re_registration"),  # Tigers u13s exists
        ("200-leopards-u9-2526", True, "new_registration"),  # Leopards u9s exists
        ("100-leopards-u9-2526-emma-jones", True, "re_registration"),  # Leopards u9s exists
        
        # Invalid teams/age groups
        ("200-tigers-u99-2526", False, None),  # Age group doesn't exist
        ("200-nonexistent-u13-2526", False, None),  # Team doesn't exist
    ]
    
    for test_code, should_validate, expected_route in test_cases:
        print(f"\n--- Testing: '{test_code}' ---")
        
        # Step 1: Parse the code
        parsed_code = parse_registration_code(test_code)
        if parsed_code is None:
            print(f"  ❌ Code parsing failed")
            continue
        
        print(f"  ✅ Code parsed: {parsed_code['team']} {parsed_code['age_group']} (prefix: {parsed_code['prefix']})")
        
        # Step 2: Validate team and age group
        is_valid = validate_team_and_age_group(parsed_code['team'], parsed_code['age_group'])
        
        if should_validate:
            if is_valid:
                print(f"  ✅ Team validation PASSED")
                
                # Step 3: Test routing
                route = route_registration_request(parsed_code)
                if route == expected_route:
                    print(f"  ✅ Routing PASSED: {route}")
                    print(f"  🎉 COMPLETE FLOW SUCCESS!")
                else:
                    print(f"  ❌ Routing FAILED: Expected {expected_route}, got {route}")
            else:
                print(f"  ❌ Team validation FAILED (but should have passed)")
        else:
            if not is_valid:
                print(f"  ✅ Team validation correctly FAILED")
            else:
                print(f"  ❌ Team validation incorrectly PASSED")

if __name__ == "__main__":
    test_complete_flow() 