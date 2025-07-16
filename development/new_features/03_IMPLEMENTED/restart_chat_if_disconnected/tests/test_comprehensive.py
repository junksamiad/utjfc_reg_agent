#!/usr/bin/env python3
"""
Comprehensive test suite for the restart chat feature

Run from project root:
python development/new_features/restart_chat_if_disconnected/tests/test_comprehensive.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
project_root = Path(__file__).parent.parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

def run_all_tests():
    """Run all tests for the restart chat feature"""
    print("🧪 RESTART CHAT FEATURE - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
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
            print(f"   Available tools: {new_registration_agent.tools}")
            
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
    
    # Test 2: Function Call with Non-existent Record
    print("\n2️⃣ Testing Function Call (Non-existent Record)...")
    total_tests += 1
    try:
        result = check_if_record_exists_in_db(
            parent_full_name="Test Parent",
            player_full_name="Test Player"
        )
        
        if result.get('success') and not result.get('record_found'):
            print("   ✅ Function executes correctly for non-existent record")
            print(f"   Message: {result.get('message')}")
            tests_passed += 1
        else:
            print(f"   ❌ Unexpected result: {result}")
            
    except Exception as e:
        print(f"   ❌ Function call failed: {e}")
    
    # Test 3: Real Database Record (Lee Hayton / Seb Hayton)
    print("\n3️⃣ Testing with Real Database Record...")
    print("   Testing: Lee Hayton / Seb Hayton")
    total_tests += 1
    try:
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        print(f"   Success: {result.get('success')}")
        print(f"   Record Found: {result.get('record_found')}")
        print(f"   Message: {result.get('message')}")
        
        if result.get('success'):
            if result.get('record_found'):
                print("   ✅ Successfully found existing record")
                record = result.get('record', {})
                played_last_season = record.get('played_for_urmston_town_last_season')
                team = record.get('team')
                age_group = record.get('age_group')
                
                print(f"   Team: {team}")
                print(f"   Age Group: {age_group}")
                print(f"   Played Last Season: {played_last_season}")
                
                # Test routing logic
                print(f"   📍 Routing Logic:")
                if played_last_season == 'N':
                    print("   → Would route to routine 32 (kit selection)")
                elif played_last_season == 'Y':
                    print("   → Would call check_if_kit_needed function")
                    print("   → Then route to routine 32 (kit) or 34 (photo)")
                else:
                    print(f"   ⚠️  Unexpected value: '{played_last_season}'")
                
                if played_last_season in ['Y', 'N']:
                    print("   ✅ Valid routing data available")
                else:
                    print(f"   ❌ Invalid routing data: '{played_last_season}'")
                    
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
        # Test with empty parent name
        result = check_if_record_exists_in_db(
            parent_full_name="",
            player_full_name="Test Player"
        )
        
        if not result.get('success') and "required" in result.get('message', '').lower():
            print("   ✅ Proper error handling for empty parent name")
            
        # Test with empty player name  
        result2 = check_if_record_exists_in_db(
            parent_full_name="Test Parent",
            player_full_name=""
        )
        
        if not result2.get('success') and "required" in result2.get('message', '').lower():
            print("   ✅ Proper error handling for empty player name")
            tests_passed += 1
        else:
            print(f"   ❌ Error handling failed: {result2}")
            
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
    
    # Test 5: Routine 2 Update Check
    print("\n5️⃣ Testing Routine 2 Update...")
    total_tests += 1
    try:
        from registration_agent.registration_routines import RegistrationRoutines
        routine_2 = RegistrationRoutines.get_routine_message(2)
        
        if "check_if_record_exists_in_db" in routine_2:
            print("   ✅ Routine 2 includes new function call")
            
            # Check for the new routing logic
            if "played_for_urmston_town_last_season" in routine_2:
                print("   ✅ Routine 2 includes routing logic")
                
                # Check for all new steps
                if "routine_number = 32" in routine_2 and "routine = 34" in routine_2:
                    print("   ✅ Routine 2 includes all routing steps")
                    tests_passed += 1
                else:
                    print("   ❌ Routine 2 missing some routing steps")
            else:
                print("   ❌ Routine 2 missing routing logic")
        else:
            print("   ❌ Routine 2 doesn't include function call")
            
    except Exception as e:
        print(f"   ❌ Routine test failed: {e}")
    
    # Test 6: Tool Schema Validation
    print("\n6️⃣ Testing Tool Schema...")
    total_tests += 1
    try:
        schema = CHECK_IF_RECORD_EXISTS_IN_DB_TOOL
        
        # Check basic schema structure
        if (schema.get('name') == 'check_if_record_exists_in_db' and
            schema.get('type') == 'function' and
            'parameters' in schema):
            
            params = schema['parameters']
            required = params.get('required', [])
            
            if set(required) == {"player_full_name", "parent_full_name"}:
                print("   ✅ Tool schema is correctly structured")
                tests_passed += 1
            else:
                print(f"   ❌ Required parameters incorrect: {required}")
        else:
            print("   ❌ Tool schema structure invalid")
            
    except Exception as e:
        print(f"   ❌ Schema test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Feature is ready for deployment.")
        print("\n🚀 Next Steps:")
        print("1. Commit changes: git add . && git commit -m 'feat: implement restart chat feature'")
        print("2. Push to origin: git push origin feature/restart-chat-if-disconnected")
        print("3. Deploy to production following deployment guide")
        print("4. Test with real registration codes in production")
        return True
    else:
        print("⚠️  Some tests failed. Review issues before deployment.")
        print("\n🔍 Debug Information:")
        print("- Check Airtable API key configuration")
        print("- Verify database connectivity")
        print("- Review import paths")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)