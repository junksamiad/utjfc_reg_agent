#!/usr/bin/env python3
"""
Test script for parent contact details routines 7-11
Tests relationship, phone, email, DOB, and address collection with validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from registration_agent.registration_routines import RegistrationRoutines
from registration_agent.tools.registration_tools.address_validation import validate_address
from registration_agent.tools.registration_tools.address_validation_tool import handle_address_validation
from registration_agent.registration_agents import new_registration_agent

def test_parent_routine_definitions():
    """Test that all parent contact routines are properly defined"""
    print("🔍 Testing Parent Contact Routine Definitions")
    print("-" * 60)
    
    routines = [7, 8, 9, 10, 11]
    for routine_num in routines:
        routine_msg = RegistrationRoutines.get_routine_message(routine_num)
        if routine_msg:
            print(f"✅ Routine {routine_num}: Found")
            print(f"   Preview: {routine_msg[:100]}...")
        else:
            print(f"❌ Routine {routine_num}: Missing")
    
    print()

def test_relationship_enum_validation():
    """Test relationship enum validation logic"""
    print("🔍 Testing Relationship Enum Validation")
    print("-" * 60)
    
    # Test cases for relationship normalization
    test_cases = [
        ("Mother", "Mother", "Exact match"),
        ("mum", "Mother", "Common variation"),
        ("mom", "Mother", "US variation"),
        ("mam", "Mother", "Regional variation"),
        ("Father", "Father", "Exact match"),
        ("dad", "Father", "Common variation"),
        ("daddy", "Father", "Informal variation"),
        ("Guardian", "Guardian", "Exact match"),
        ("grandma", "Other", "Grandparent variation"),
        ("granny", "Other", "Grandparent variation"),
        ("grandfather", "Other", "Grandparent variation"),
        ("grandad", "Other", "Grandparent variation"),
        ("aunt", "Other", "Other relative"),
        ("uncle", "Other", "Other relative"),
    ]
    
    # Check if routine 7 contains the enum values
    routine_7 = RegistrationRoutines.get_routine_message(7)
    enum_values = ["Mother", "Father", "Guardian", "Other"]
    
    all_enums_found = True
    for enum_val in enum_values:
        if enum_val in routine_7:
            print(f"✅ Enum '{enum_val}' found in routine")
        else:
            print(f"❌ Enum '{enum_val}' missing from routine")
            all_enums_found = False
    
    if all_enums_found:
        print("✅ All relationship enums properly defined")
    else:
        print("❌ Some relationship enums missing")
    
    print()

def test_phone_validation_logic():
    """Test UK phone number validation logic"""
    print("🔍 Testing UK Phone Number Validation Logic")
    print("-" * 60)
    
    test_cases = [
        ("07123456789", True, "Valid mobile"),
        ("07 123 456 789", True, "Mobile with spaces"),
        ("07-123-456-789", True, "Mobile with dashes"),
        ("(07) 123 456 789", True, "Mobile with brackets"),
        ("01612345678", True, "Valid Manchester landline"),
        ("0161 234 5678", True, "Landline with spaces"),
        ("0161-234-5678", True, "Landline with dashes"),
        ("0123456789", False, "Wrong landline prefix"),
        ("071234567890", False, "Too many digits mobile"),
        ("0712345678", False, "Too few digits mobile"),
        ("01234567890", False, "Wrong format"),
        ("abc123def456", False, "Contains letters"),
    ]
    
    routine_8 = RegistrationRoutines.get_routine_message(8)
    
    # Check if routine contains validation instructions
    validation_keywords = ["07", "0161", "11 digits", "mobile", "landline"]
    found_keywords = []
    
    for keyword in validation_keywords:
        if keyword in routine_8:
            found_keywords.append(keyword)
    
    if len(found_keywords) >= 4:
        print("✅ Phone validation logic properly defined in routine")
        print(f"   Found keywords: {found_keywords}")
    else:
        print("❌ Phone validation logic incomplete")
        print(f"   Found keywords: {found_keywords}")
    
    print()

def test_email_validation_logic():
    """Test email validation logic"""
    print("🔍 Testing Email Validation Logic")
    print("-" * 60)
    
    test_cases = [
        ("user@example.com", True, "Standard email"),
        ("USER@EXAMPLE.COM", True, "Uppercase (should be lowercased)"),
        ("user.name@domain.co.uk", True, "Complex valid email"),
        ("user+tag@example.org", True, "Email with plus"),
        ("user@domain", False, "Missing dot"),
        ("userdomain.com", False, "Missing @"),
        ("user@@domain.com", False, "Double @"),
        ("user@.com", False, "Missing domain"),
        ("@domain.com", False, "Missing user"),
    ]
    
    routine_9 = RegistrationRoutines.get_routine_message(9)
    
    # Check if routine contains email validation instructions
    email_keywords = ["@", "dot", "lowercase", "something@something.something"]
    found_keywords = []
    
    for keyword in email_keywords:
        if keyword.lower() in routine_9.lower():
            found_keywords.append(keyword)
    
    if len(found_keywords) >= 3:
        print("✅ Email validation logic properly defined in routine")
        print(f"   Found keywords: {found_keywords}")
    else:
        print("❌ Email validation logic incomplete")
        print(f"   Found keywords: {found_keywords}")
    
    print()

def test_address_validation_function():
    """Test address validation function (without API key)"""
    print("🔍 Testing Address Validation Function")
    print("-" * 60)
    
    # Test without API key (should gracefully handle)
    result = validate_address("10 Downing Street, London")
    
    if "api key not configured" in result["message"].lower():
        print("✅ Address validation handles missing API key gracefully")
        print(f"   Message: {result['message']}")
    else:
        print("❌ Address validation doesn't handle missing API key properly")
    
    # Test empty address
    result = validate_address("")
    if not result["valid"] and "empty" in result["message"].lower():
        print("✅ Address validation handles empty input")
    else:
        print("❌ Address validation doesn't handle empty input")
    
    print()

def test_address_tool_wrapper():
    """Test address validation tool wrapper"""
    print("🔍 Testing Address Validation Tool Wrapper")
    print("-" * 60)
    
    result = handle_address_validation("Test Address")
    
    try:
        import json
        parsed = json.loads(result)
        if "valid" in parsed and "message" in parsed:
            print("✅ Address tool wrapper returns valid JSON")
            print(f"   Contains usage_note: {'usage_note' in parsed}")
        else:
            print("❌ Address tool wrapper malformed response")
    except Exception as e:
        print(f"❌ Address tool wrapper error: {e}")
    
    print()

def test_agent_tool_access():
    """Test that agents have access to address validation tool"""
    print("🔍 Testing Agent Tool Access for Address Validation")
    print("-" * 60)
    
    # Check new registration agent tools
    agent_tools = new_registration_agent.tools
    expected_tools = ["person_name_validation", "child_dob_validation", "medical_issues_validation", "address_validation"]
    
    print(f"Agent tools: {agent_tools}")
    
    for tool in expected_tools:
        if tool in agent_tools:
            print(f"✅ Agent has access to {tool}")
        else:
            print(f"❌ Agent missing tool: {tool}")
    
    # Test tool function access
    tool_functions = new_registration_agent.get_tool_functions()
    if "address_validation" in tool_functions:
        print("✅ Agent can access address_validation function")
    else:
        print("❌ Agent cannot access address_validation function")
    
    print()

def test_routine_flow_progression():
    """Test the logical flow of parent contact routines"""
    print("🔍 Testing Parent Contact Routine Flow")
    print("-" * 60)
    
    # Test routine progression
    routine_flow = [
        (6, "previous team", "routine_number = 7", "contact details"),
        (7, "relationship", "routine_number = 8", "telephone"),
        (8, "telephone", "routine_number = 9", "email"),
        (9, "email", "routine_number = 10", "date of birth"),
        (10, "date of birth", "routine_number = 11", "address"),
        (11, "address", "routine_number = 12", "next stage")
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
            print(f"✅ Routine {routine_num} progresses correctly")
        else:
            print(f"❌ Routine {routine_num} missing progression logic")
    
    print()

def test_validation_approach():
    """Test the validation approach (embedded vs function calls)"""
    print("🔍 Testing Validation Approach")
    print("-" * 60)
    
    routines_with_embedded_validation = [7, 8, 9, 10]  # These should have validation in prompt
    routines_with_function_validation = [11]  # These use function calls
    
    for routine_num in routines_with_embedded_validation:
        routine_msg = RegistrationRoutines.get_routine_message(routine_num)
        if "validate" in routine_msg.lower() or "format" in routine_msg.lower():
            print(f"✅ Routine {routine_num} has embedded validation logic")
        else:
            print(f"❌ Routine {routine_num} missing validation logic")
    
    for routine_num in routines_with_function_validation:
        routine_msg = RegistrationRoutines.get_routine_message(routine_num)
        if "function" in routine_msg.lower() and "validation" in routine_msg.lower():
            print(f"✅ Routine {routine_num} uses function validation")
        else:
            print(f"❌ Routine {routine_num} missing function validation")
    
    print()

def main():
    """Run all tests for parent contact routines"""
    print("🚀 Testing Parent Contact Details Routines (7-11)")
    print("=" * 70)
    print()
    
    test_parent_routine_definitions()
    test_relationship_enum_validation()
    test_phone_validation_logic()
    test_email_validation_logic()
    test_address_validation_function()
    test_address_tool_wrapper()
    test_agent_tool_access()
    test_routine_flow_progression()
    test_validation_approach()
    
    print("🏁 Parent Contact Testing Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main() 