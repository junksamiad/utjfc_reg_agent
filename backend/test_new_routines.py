#!/usr/bin/env python3
"""
Test script for new registration routines 4-6 and medical issues validation
Tests the expanded registration flow with gender, medical issues, and previous team information
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from registration_agent.registration_routines import RegistrationRoutines
from registration_agent.tools.registration_tools.medical_issues_validation import validate_medical_issues
from registration_agent.tools.registration_tools.medical_issues_validation_tool import handle_medical_issues_validation
from registration_agent.registration_agents import new_registration_agent

def test_routine_definitions():
    """Test that all new routines are properly defined"""
    print("🔍 Testing Routine Definitions")
    print("-" * 50)
    
    routines = [4, 5, 6]
    for routine_num in routines:
        routine_msg = RegistrationRoutines.get_routine_message(routine_num)
        if routine_msg:
            print(f"✅ Routine {routine_num}: Found")
            print(f"   Preview: {routine_msg[:100]}...")
        else:
            print(f"❌ Routine {routine_num}: Missing")
    
    print()

def test_medical_issues_validation():
    """Test medical issues validation function"""
    print("🔍 Testing Medical Issues Validation")
    print("-" * 50)
    
    test_cases = [
        # No issues cases
        ("No", "", True, "No medical issues"),
        ("n", "", True, "Normalized 'n' to no"),
        ("nope", "", True, "Normalized 'nope' to no"),
        
        # Yes with single issue
        ("Yes", "Asthma", True, "Single medical issue"),
        ("y", "Diabetes", True, "Normalized 'y' to yes with issue"),
        
        # Multiple issues
        ("yes", "Asthma, diabetes", True, "Multiple issues separated by comma"),
        ("YES", "ADHD; allergies to nuts", True, "Multiple issues separated by semicolon"),
        ("true", "has asthma and wears glasses", True, "Multiple issues with 'and' separator"),
        
        # Invalid cases
        ("maybe", "", False, "Ambiguous response"),
        ("", "", False, "Empty response"),
        ("yes", "", False, "Yes without details"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for has_issues, details, expected_valid, description in test_cases:
        result = validate_medical_issues(has_issues, details)
        test_passed = result["valid"] == expected_valid
        
        if test_passed:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Expected: {expected_valid}, Got: {result['valid']}")
            print(f"   Message: {result['message']}")
        
        # Show details for successful validations
        if result["valid"] and result["has_medical_issues"]:
            print(f"   Issues: {result['medical_issues_list']}")
            if result["normalizations_applied"]:
                print(f"   Normalizations: {result['normalizations_applied']}")
    
    print(f"\nMedical Issues Validation: {passed}/{total} tests passed")
    print()

def test_medical_issues_tool():
    """Test medical issues validation tool wrapper"""
    print("🔍 Testing Medical Issues Tool Wrapper")
    print("-" * 50)
    
    # Test the tool wrapper function
    result = handle_medical_issues_validation("yes", "asthma, diabetes")
    
    try:
        import json
        parsed = json.loads(result)
        if parsed["valid"] and parsed["has_medical_issues"]:
            print("✅ Tool wrapper working correctly")
            print(f"   Issues found: {len(parsed['medical_issues_list'])}")
            print(f"   Usage note: {parsed.get('usage_note', 'None')}")
        else:
            print("❌ Tool wrapper returned invalid result")
    except Exception as e:
        print(f"❌ Tool wrapper error: {e}")
    
    print()

def test_agent_tool_access():
    """Test that agents have access to new tools"""
    print("🔍 Testing Agent Tool Access")
    print("-" * 50)
    
    # Check new registration agent tools
    agent_tools = new_registration_agent.tools
    expected_tools = ["person_name_validation", "child_dob_validation", "medical_issues_validation"]
    
    print(f"Agent tools: {agent_tools}")
    
    for tool in expected_tools:
        if tool in agent_tools:
            print(f"✅ Agent has access to {tool}")
        else:
            print(f"❌ Agent missing tool: {tool}")
    
    # Test tool function access
    tool_functions = new_registration_agent.get_tool_functions()
    if "medical_issues_validation" in tool_functions:
        print("✅ Agent can access medical_issues_validation function")
    else:
        print("❌ Agent cannot access medical_issues_validation function")
    
    print()

def test_routine_flow():
    """Test the logical flow of new routines"""
    print("🔍 Testing Routine Flow Logic")
    print("-" * 50)
    
    # Test routine progression
    routine_flow = [
        (3, "date of birth", "routine_number = 4", "gender"),
        (4, "gender", "routine_number = 5", "medical issues"),
        (5, "medical issues", "routine_number = 6", "previous team"),
        (6, "previous team", "routine_number = 7", "next stage")
    ]
    
    for routine_num, current_step, expected_next, next_step in routine_flow:
        routine_msg = RegistrationRoutines.get_routine_message(routine_num)
        
        # Check if routine mentions the current step
        if current_step.lower() in routine_msg.lower():
            print(f"✅ Routine {routine_num} mentions '{current_step}'")
        else:
            print(f"❌ Routine {routine_num} missing '{current_step}' reference")
        
        # Check if routine mentions progression to next routine
        if expected_next in routine_msg:
            print(f"✅ Routine {routine_num} progresses to next step")
        else:
            print(f"❌ Routine {routine_num} missing progression logic")
    
    print()

def test_gender_handling():
    """Test gender handling approach in routine 4"""
    print("🔍 Testing Gender Handling")
    print("-" * 50)
    
    routine_4 = RegistrationRoutines.get_routine_message(4)
    
    # Check for gender normalization instructions
    gender_keywords = ["male", "female", "not disclosed", "normalize", "variations"]
    found_keywords = []
    
    for keyword in gender_keywords:
        if keyword.lower() in routine_4.lower():
            found_keywords.append(keyword)
    
    if len(found_keywords) >= 3:
        print("✅ Routine 4 includes comprehensive gender handling")
        print(f"   Found keywords: {found_keywords}")
    else:
        print("❌ Routine 4 may need more gender handling details")
        print(f"   Found keywords: {found_keywords}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Testing New Registration Routines (4-6)")
    print("=" * 60)
    print()
    
    test_routine_definitions()
    test_medical_issues_validation()
    test_medical_issues_tool()
    test_agent_tool_access()
    test_routine_flow()
    test_gender_handling()
    
    print("🏁 Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main() 