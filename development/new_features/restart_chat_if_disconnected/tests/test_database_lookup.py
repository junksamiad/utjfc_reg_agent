#!/usr/bin/env python3
"""
Database lookup tests for the restart chat feature

Run from project root:
python development/new_features/restart_chat_if_disconnected/tests/test_database_lookup.py
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

def test_database_lookup():
    """Test database lookup functionality"""
    print("🔍 DATABASE LOOKUP TESTS")
    print("=" * 40)
    
    try:
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        print("✅ Function imported successfully")
        
        # Test 1: Known existing record
        print("\n1️⃣ Testing Known Record: Lee Hayton / Seb Hayton")
        result = test_known_record()
        
        # Test 2: Non-existent record
        print("\n2️⃣ Testing Non-existent Record")
        result2 = test_nonexistent_record()
        
        # Test 3: Various name formats
        print("\n3️⃣ Testing Name Variations")
        test_name_variations()
        
        # Test 4: Error conditions
        print("\n4️⃣ Testing Error Conditions")
        test_error_conditions()
        
        print("\n✅ Database lookup tests completed!")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

def test_known_record():
    """Test with the known Lee Hayton / Seb Hayton record"""
    from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
    
    result = check_if_record_exists_in_db(
        parent_full_name="Lee Hayton",
        player_full_name="Seb Hayton"
    )
    
    print(f"   Success: {result.get('success')}")
    print(f"   Record Found: {result.get('record_found')}")
    print(f"   Message: {result.get('message')}")
    
    if result.get('record_found') and result.get('record'):
        record = result['record']
        print(f"   📊 Record Details:")
        print(f"     Player: {record.get('player_full_name')}")
        print(f"     Parent: {record.get('parent_full_name')}")
        print(f"     Team: {record.get('team')}")
        print(f"     Age Group: {record.get('age_group')}")
        print(f"     Played Last Season: {record.get('played_for_urmston_town_last_season')}")
        print(f"     Registration Status: {record.get('registration_status')}")
        
        # Analyze routing
        played_last_season = record.get('played_for_urmston_town_last_season')
        print(f"   🔀 Routing Analysis:")
        if played_last_season == 'N':
            print("     → NEW PLAYER: Would route to routine 32 (kit selection)")
        elif played_last_season == 'Y':
            print("     → RETURNING PLAYER: Would call check_if_kit_needed")
            print("     → Then route to routine 32 (kit) or 34 (photo)")
        else:
            print(f"     → UNEXPECTED VALUE: '{played_last_season}'")
    
    return result

def test_nonexistent_record():
    """Test with non-existent record"""
    from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
    
    result = check_if_record_exists_in_db(
        parent_full_name="John Nonexistent",
        player_full_name="Jane Nonexistent"
    )
    
    print(f"   Success: {result.get('success')}")
    print(f"   Record Found: {result.get('record_found')}")
    print(f"   Message: {result.get('message')}")
    
    if result.get('success') and not result.get('record_found'):
        print("   ✅ Correctly identified as new registration")
        print("   → Would route to routine 3 (continue normal flow)")
    else:
        print("   ❌ Unexpected result for non-existent record")
    
    return result

def test_name_variations():
    """Test various name formatting scenarios"""
    from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
    
    # Test different capitalizations (should fail - we use exact matching)
    test_cases = [
        ("lee hayton", "seb hayton"),  # lowercase
        ("LEE HAYTON", "SEB HAYTON"),  # uppercase
        ("Lee  Hayton", "Seb  Hayton"),  # extra spaces
    ]
    
    for parent, player in test_cases:
        print(f"   Testing: '{parent}' / '{player}'")
        result = check_if_record_exists_in_db(
            parent_full_name=parent,
            player_full_name=player
        )
        
        if result.get('record_found'):
            print(f"     ✅ Found (exact match worked)")
        else:
            print(f"     ❌ Not found (expected with exact matching)")

def test_error_conditions():
    """Test error handling"""
    from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
    
    # Test empty names
    test_cases = [
        ("", "Player Name"),
        ("Parent Name", ""),
        ("", ""),
    ]
    
    for parent, player in test_cases:
        print(f"   Testing empty fields: '{parent}' / '{player}'")
        result = check_if_record_exists_in_db(
            parent_full_name=parent,
            player_full_name=player
        )
        
        if not result.get('success'):
            print(f"     ✅ Proper error handling: {result.get('message')}")
        else:
            print(f"     ❌ Should have failed validation")

if __name__ == "__main__":
    test_database_lookup()