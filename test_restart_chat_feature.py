#!/usr/bin/env python3
"""
Test script for the restart chat feature implementation.
Tests the check_if_record_exists_in_db function with real database records.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set up environment
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

def test_record_lookup():
    """Test the record lookup function with known database record."""
    print("🧪 Testing restart chat feature implementation")
    print("=" * 60)
    
    try:
        # Import our new function
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        print("✅ Successfully imported check_if_record_exists_in_db function")
        
        # Test with the known record: Lee Hayton / Seb Hayton
        print("\n📋 Test Case 1: Known existing record")
        print("Parent: Lee Hayton")
        print("Player: Seb Hayton")
        
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        print(f"\nResult:")
        print(f"  Success: {result.get('success')}")
        print(f"  Record Found: {result.get('record_found')}")
        print(f"  Message: {result.get('message')}")
        
        if result.get('record_found') and result.get('record'):
            record = result['record']
            print(f"\n📊 Record Details:")
            print(f"  Player Full Name: {record.get('player_full_name', 'N/A')}")
            print(f"  Parent Full Name: {record.get('parent_full_name', 'N/A')}")
            print(f"  Team: {record.get('team', 'N/A')}")
            print(f"  Age Group: {record.get('age_group', 'N/A')}")
            print(f"  Played Last Season: {record.get('played_for_urmston_town_last_season', 'N/A')}")
            print(f"  Registration Status: {record.get('registration_status', 'N/A')}")
            
            # Test routing logic
            print(f"\n🔀 Routing Logic Test:")
            played_last_season = record.get('played_for_urmston_town_last_season', '')
            if played_last_season == 'N':
                print("  → Would route to routine 32 (kit selection) - NEW PLAYER")
            elif played_last_season == 'Y':
                print("  → Would call check_if_kit_needed function next")
                print("  → Then route to routine 32 (kit) or 34 (photo) based on result")
            else:
                print(f"  → Unexpected value for played_last_season: '{played_last_season}'")
        
        print("\n" + "=" * 60)
        
        # Test with non-existent record
        print("📋 Test Case 2: Non-existent record")
        print("Parent: John Smith")
        print("Player: Jane Smith")
        
        result2 = check_if_record_exists_in_db(
            parent_full_name="John Smith",
            player_full_name="Jane Smith"
        )
        
        print(f"\nResult:")
        print(f"  Success: {result2.get('success')}")
        print(f"  Record Found: {result2.get('record_found')}")
        print(f"  Message: {result2.get('message')}")
        
        if result2.get('record_found'):
            print("  ⚠️  Unexpected: Found record that shouldn't exist")
        else:
            print("  ✅ Correctly identified as new registration")
        
        print("\n" + "=" * 60)
        
        # Test error handling
        print("📋 Test Case 3: Invalid input")
        
        result3 = check_if_record_exists_in_db(
            parent_full_name="",
            player_full_name="Test Player"
        )
        
        print(f"Result with empty parent name:")
        print(f"  Success: {result3.get('success')}")
        print(f"  Message: {result3.get('message')}")
        
        print("\n🎉 All tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_record_lookup()