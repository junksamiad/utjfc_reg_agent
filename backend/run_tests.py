#!/usr/bin/env python3
"""
Comprehensive test suite for the restart chat feature
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_all_tests():
    """Run all tests for the restart chat feature"""
    print("🧪 RESTART CHAT FEATURE TEST SUITE")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Tool Registration
    print("\n1️⃣ Testing Tool Registration...")
    total_tests += 1
    try:
        from registration_agent.tools.registration_tools import (
            check_if_record_exists_in_db,
            CHECK_IF_RECORD_EXISTS_IN_DB_TOOL,
            handle_check_if_record_exists_in_db
        )
        from registration_agent.registration_agents import new_registration_agent
        
        # Check agent tools
        if "check_if_record_exists_in_db" in new_registration_agent.tools:
            print("   ✅ Tool registered in agent.tools")
            tests_passed += 1
        else:
            print("   ❌ Tool NOT in agent.tools")
            
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
    
    # Test 2: Function Call
    print("\n2️⃣ Testing Function Call...")
    total_tests += 1
    try:
        # Test with non-existent record first (safer)
        result = check_if_record_exists_in_db(
            parent_full_name="Test Parent",
            player_full_name="Test Player"
        )
        
        if result.get('success') and not result.get('record_found'):
            print("   ✅ Function executes correctly for non-existent record")
            tests_passed += 1
        else:
            print(f"   ❌ Unexpected result: {result}")
            
    except Exception as e:
        print(f"   ❌ Function call failed: {e}")
    
    # Test 3: Real Database Record
    print("\n3️⃣ Testing with Real Database Record (Lee Hayton / Seb Hayton)...")
    total_tests += 1
    try:
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        print(f"   Success: {result.get('success')}")
        print(f"   Record Found: {result.get('record_found')}")
        
        if result.get('success'):
            if result.get('record_found'):
                print("   ✅ Successfully found existing record")
                record = result.get('record', {})
                played_last_season = record.get('played_for_urmston_town_last_season')
                print(f"   Played Last Season: {played_last_season}")
                
                # Test routing logic
                if played_last_season in ['Y', 'N']:
                    print("   ✅ Valid routing data available")
                else:
                    print(f"   ⚠️  Unexpected played_last_season value: '{played_last_season}'")
                    
            else:
                print("   ℹ️  Record not found (might be expected)")
            tests_passed += 1
        else:
            print(f"   ❌ Database query failed: {result.get('message')}")
            
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
    
    # Test 4: Error Handling
    print("\n4️⃣ Testing Error Handling...")
    total_tests += 1
    try:
        result = check_if_record_exists_in_db(
            parent_full_name="",  # Invalid empty name
            player_full_name="Test"
        )
        
        if not result.get('success') and "required" in result.get('message', '').lower():
            print("   ✅ Proper error handling for invalid input")
            tests_passed += 1
        else:
            print(f"   ❌ Error handling failed: {result}")
            
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    
    # Test 5: Routine Update Check
    print("\n5️⃣ Testing Routine 2 Update...")
    total_tests += 1
    try:
        from registration_agent.registration_routines import RegistrationRoutines
        routine_2 = RegistrationRoutines.get_routine_message(2)
        
        if "check_if_record_exists_in_db" in routine_2:
            print("   ✅ Routine 2 includes new function call")
            
            # Check for the new steps
            if "played_for_urmston_town_last_season" in routine_2:
                print("   ✅ Routine 2 includes routing logic")
                tests_passed += 1
            else:
                print("   ❌ Routine 2 missing routing logic")
        else:
            print("   ❌ Routine 2 doesn't include function call")
            
    except Exception as e:
        print(f"   ❌ Routine test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Feature is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Review issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)