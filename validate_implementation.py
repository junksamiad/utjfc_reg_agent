#!/usr/bin/env python3
"""
Quick validation script for the restart chat feature implementation
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def validate_implementation():
    """Validate the restart chat implementation"""
    print("🔍 VALIDATING RESTART CHAT IMPLEMENTATION")
    print("=" * 50)
    
    validation_results = []
    
    # Test 1: Import core function
    print("\n1️⃣ Testing Core Function Import...")
    try:
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        print("   ✅ Core function imported successfully")
        validation_results.append(True)
    except Exception as e:
        print(f"   ❌ Core function import failed: {e}")
        validation_results.append(False)
    
    # Test 2: Import tool definition
    print("\n2️⃣ Testing Tool Definition Import...")
    try:
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db_tool import CHECK_IF_RECORD_EXISTS_IN_DB_TOOL, handle_check_if_record_exists_in_db
        print("   ✅ Tool definition imported successfully")
        validation_results.append(True)
    except Exception as e:
        print(f"   ❌ Tool definition import failed: {e}")
        validation_results.append(False)
    
    # Test 3: Import from package
    print("\n3️⃣ Testing Package Import...")
    try:
        from registration_agent.tools.registration_tools import check_if_record_exists_in_db, CHECK_IF_RECORD_EXISTS_IN_DB_TOOL, handle_check_if_record_exists_in_db
        print("   ✅ Package imports working")
        validation_results.append(True)
    except Exception as e:
        print(f"   ❌ Package import failed: {e}")
        validation_results.append(False)
    
    # Test 4: Agent integration
    print("\n4️⃣ Testing Agent Integration...")
    try:
        from registration_agent.registration_agents import new_registration_agent
        if "check_if_record_exists_in_db" in new_registration_agent.tools:
            print("   ✅ Tool registered in agent")
            validation_results.append(True)
        else:
            print("   ❌ Tool not found in agent tools")
            validation_results.append(False)
    except Exception as e:
        print(f"   ❌ Agent integration test failed: {e}")
        validation_results.append(False)
    
    # Test 5: Function execution
    print("\n5️⃣ Testing Function Execution...")
    try:
        result = check_if_record_exists_in_db(
            parent_full_name="Test Parent",
            player_full_name="Test Player"
        )
        if result.get('success') is not None:
            print("   ✅ Function executes successfully")
            print(f"   Result: Success={result.get('success')}, Found={result.get('record_found')}")
            validation_results.append(True)
        else:
            print("   ❌ Function execution failed")
            validation_results.append(False)
    except Exception as e:
        print(f"   ❌ Function execution test failed: {e}")
        validation_results.append(False)
    
    # Test 6: Routine 2 update
    print("\n6️⃣ Testing Routine 2 Update...")
    try:
        from registration_agent.registration_routines import RegistrationRoutines
        routine_2 = RegistrationRoutines.get_routine_message(2)
        if "check_if_record_exists_in_db" in routine_2:
            print("   ✅ Routine 2 updated with function call")
            validation_results.append(True)
        else:
            print("   ❌ Routine 2 not updated")
            validation_results.append(False)
    except Exception as e:
        print(f"   ❌ Routine 2 test failed: {e}")
        validation_results.append(False)
    
    # Test 7: Database connection test (if possible)
    print("\n7️⃣ Testing Database Connection...")
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Test with Lee Hayton / Seb Hayton (known record)
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        if result.get('success'):
            if result.get('record_found'):
                print("   ✅ Database connection working - record found")
                record = result.get('record', {})
                played_last_season = record.get('played_for_urmston_town_last_season')
                print(f"   Record details: played_last_season='{played_last_season}'")
            else:
                print("   ℹ️  Database connection working - no record found")
            validation_results.append(True)
        else:
            print(f"   ❌ Database connection failed: {result.get('message')}")
            validation_results.append(False)
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        validation_results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(validation_results)
    total = len(validation_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED! Implementation is working correctly.")
        return True
    else:
        print("⚠️  Some validations failed. Review implementation.")
        return False

if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)