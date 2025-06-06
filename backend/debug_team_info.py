#!/usr/bin/env python3
"""
Debug script to inspect team_info table structure and data
"""

import sys
import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
TEAM_INFO_BASE_ID = "appBLxf3qmGIBc6ue"
TEAM_INFO_TABLE_ID = "tbl1ZCkcikNsLSw66"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def inspect_team_info_table():
    """Inspect the team_info table to understand its structure and data"""
    try:
        if not AIRTABLE_API_KEY:
            print("ERROR: AIRTABLE_API_KEY not found in environment variables")
            return
        
        # Initialize Airtable client
        api = Api(AIRTABLE_API_KEY)
        table = api.table(TEAM_INFO_BASE_ID, TEAM_INFO_TABLE_ID)
        
        print("=== Team Info Table Inspection ===")
        print(f"Base ID: {TEAM_INFO_BASE_ID}")
        print(f"Table ID: {TEAM_INFO_TABLE_ID}")
        
        # Get all records
        print("\n=== Fetching all records ===")
        records = table.all()
        
        print(f"Found {len(records)} records")
        
        if len(records) > 0:
            print("\n=== First record structure ===")
            first_record = records[0]
            print(f"Record ID: {first_record['id']}")
            print("Fields:")
            for field_name, field_value in first_record['fields'].items():
                print(f"  {field_name}: {field_value}")
            
            print("\n=== All records data ===")
            for i, record in enumerate(records):
                print(f"\nRecord {i+1}:")
                print(f"  ID: {record['id']}")
                for field_name, field_value in record['fields'].items():
                    print(f"  {field_name}: {field_value}")
        else:
            print("No records found in the table")
            
    except Exception as e:
        print(f"Error inspecting team_info table: {e}")
        import traceback
        traceback.print_exc()

def test_field_queries():
    """Test different query combinations to find the right field names"""
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(TEAM_INFO_BASE_ID, TEAM_INFO_TABLE_ID)
        
        print("\n\n=== Testing Field Queries ===")
        
        # Test queries with different field name combinations
        test_queries = [
            # Test with field IDs
            "{{fldhmTdJXJjrb8DB1}} = 'Tigers'",
            "{{fldq6P0I9URZ5XTpF}} = 'u10'",
            
            # Test with potential field names
            "{short_team_name} = 'Tigers'",
            "{ageGroup} = 'u10'",
            "{current_season} = '2526'",
            
            # Test simple queries
            "TRUE()",  # Get all records
        ]
        
        for formula in test_queries:
            print(f"\nTesting formula: {formula}")
            try:
                results = table.all(formula=formula)
                print(f"  Results: {len(results)} records found")
                if len(results) > 0:
                    print(f"  First result fields: {list(results[0]['fields'].keys())}")
            except Exception as e:
                print(f"  Error: {e}")
                
    except Exception as e:
        print(f"Error testing field queries: {e}")

if __name__ == "__main__":
    inspect_team_info_table()
    test_field_queries() 