#!/usr/bin/env python3
"""
Simple test for the check_if_record_exists_in_db function
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_function():
    """Test the record lookup function"""
    print("Testing check_if_record_exists_in_db function...")
    
    try:
        # Import the function
        from registration_agent.tools.registration_tools.check_if_record_exists_in_db import check_if_record_exists_in_db
        print("✅ Function imported successfully")
        
        # Test with the known record
        print("\nTesting with Lee Hayton / Seb Hayton...")
        result = check_if_record_exists_in_db(
            parent_full_name="Lee Hayton",
            player_full_name="Seb Hayton"
        )
        
        print(f"Success: {result.get('success')}")
        print(f"Record Found: {result.get('record_found')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('record'):
            record = result['record']
            print(f"Played Last Season: {record.get('played_for_urmston_town_last_season')}")
            print(f"Team: {record.get('team')}")
            print(f"Age Group: {record.get('age_group')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_function()