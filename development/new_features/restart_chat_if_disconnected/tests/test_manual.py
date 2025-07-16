#!/usr/bin/env python3
"""
Manual testing script for the restart chat feature

Run from project root:
python development/new_features/restart_chat_if_disconnected/tests/test_manual.py
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

def manual_test():
    """Interactive manual test of the restart chat feature"""
    print("🎮 MANUAL TESTING - RESTART CHAT FEATURE")
    print("=" * 50)
    
    try:
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        
        print("This script allows you to manually test the restart chat feature.")
        print("You can test with different name combinations to see how the system responds.")
        print()
        
        while True:
            print("Enter test data (or 'quit' to exit):")
            
            parent_name = input("Parent full name: ").strip()
            if parent_name.lower() == 'quit':
                break
                
            player_name = input("Player full name: ").strip()
            if player_name.lower() == 'quit':
                break
            
            print(f"\n🔍 Testing: '{parent_name}' / '{player_name}'")
            print("-" * 40)
            
            # Call the function
            result = check_if_record_exists_in_db(
                parent_full_name=parent_name,
                player_full_name=player_name
            )
            
            # Display results
            print(f"Success: {result.get('success')}")
            print(f"Record Found: {result.get('record_found')}")
            print(f"Message: {result.get('message')}")
            
            if result.get('record_found') and result.get('record'):
                record = result['record']
                print(f"\n📊 Record Details:")
                print(f"  Player: {record.get('player_full_name')}")
                print(f"  Parent: {record.get('parent_full_name')}")
                print(f"  Team: {record.get('team')}")
                print(f"  Age Group: {record.get('age_group')}")
                print(f"  Played Last Season: {record.get('played_for_urmston_town_last_season')}")
                print(f"  Registration Status: {record.get('registration_status')}")
                
                # Show routing logic
                played_last_season = record.get('played_for_urmston_town_last_season')
                print(f"\n🔀 Routing Logic:")
                if played_last_season == 'N':
                    print("  → NEW PLAYER: Would route to routine 32 (kit selection)")
                    print("  → User skips all data collection and goes straight to kit selection")
                elif played_last_season == 'Y':
                    print("  → RETURNING PLAYER: Would call check_if_kit_needed function")
                    print("  → If kit needed: route to routine 32 (kit selection)")
                    print("  → If no kit needed: route to routine 34 (photo upload)")
                else:
                    print(f"  → UNEXPECTED VALUE: '{played_last_season}'")
                    print("  → This might indicate a data issue")
            
            elif not result.get('record_found'):
                print(f"\n🔀 Routing Logic:")
                print("  → NEW REGISTRATION: Would route to routine 3 (continue normal flow)")
                print("  → User continues with standard registration data collection")
            
            print("\n" + "=" * 50)
        
        print("\n👋 Manual testing session ended!")
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()

def quick_test():
    """Quick test with known data"""
    print("🚀 QUICK TEST - Known Record")
    print("=" * 30)
    
    try:
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        
        print("Testing with: Lee Hayton / Seb Hayton")
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        if result.get('record_found'):
            print("✅ Record found!")
            record = result['record']
            played_last_season = record.get('played_for_urmston_town_last_season')
            print(f"Played last season: {played_last_season}")
            
            if played_last_season == 'N':
                print("→ Would route to kit selection")
            elif played_last_season == 'Y':
                print("→ Would check if kit needed")
            
        else:
            print("❌ Record not found")
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Quick test (Lee Hayton / Seb Hayton)")
    print("2. Manual interactive test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        quick_test()
    elif choice == "2":
        manual_test()
    else:
        print("Invalid choice. Running quick test...")
        quick_test()