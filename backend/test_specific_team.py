#!/usr/bin/env python3
"""
Specific test for Tigers u13 and debugging current_season field
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

def test_tigers_u13():
    """Test specifically for Tigers u13"""
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(TEAM_INFO_BASE_ID, TEAM_INFO_TABLE_ID)
        
        print("=== Testing Tigers u13 Specifically ===")
        
        # Test the exact query we're using in the validation function
        team_normalized = "Tigers"
        age_group_normalized = "u13s"  # u13 -> u13s
        
        print(f"Searching for team: '{team_normalized}' and age group: '{age_group_normalized}'")
        
        # Try the current query format
        formula = f"AND({{fldhmTdJXJjrb8DB1}} = '{team_normalized}', {{fldq6P0I9URZ5XTpF}} = '{age_group_normalized}', {{current_season}} = '2526')"
        print(f"Query formula: {formula}")
        
        records = table.all(formula=formula)
        print(f"Results with current_season: {len(records)} records")
        
        # Try without current_season to see if that's the issue
        formula_no_season = f"AND({{fldhmTdJXJjrb8DB1}} = '{team_normalized}', {{fldq6P0I9URZ5XTpF}} = '{age_group_normalized}')"
        print(f"\nTrying without current_season: {formula_no_season}")
        
        records_no_season = table.all(formula=formula_no_season)
        print(f"Results without current_season: {len(records_no_season)} records")
        
        if len(records_no_season) > 0:
            print("Found records! Let's see what fields they have:")
            for i, record in enumerate(records_no_season):
                print(f"\nRecord {i+1}:")
                for field_name, field_value in record['fields'].items():
                    print(f"  {field_name}: {field_value}")
        
        # Try with field names instead of field IDs
        print(f"\n=== Trying with field names instead of IDs ===")
        formula_field_names = f"AND({{short_team_name}} = '{team_normalized}', {{ageGroup}} = '{age_group_normalized}')"
        print(f"Query with field names: {formula_field_names}")
        
        try:
            records_field_names = table.all(formula=formula_field_names)
            print(f"Results with field names: {len(records_field_names)} records")
            
            if len(records_field_names) > 0:
                print("Found records with field names! Fields:")
                for field_name, field_value in records_field_names[0]['fields'].items():
                    print(f"  {field_name}: {field_value}")
        except Exception as e:
            print(f"Error with field names: {e}")
        
        # Get all records to see the actual structure
        print(f"\n=== Getting all records to see structure ===")
        all_records = table.all()
        print(f"Total records in table: {len(all_records)}")
        
        if len(all_records) > 0:
            print("\nFirst record structure:")
            first_record = all_records[0]
            for field_name, field_value in first_record['fields'].items():
                print(f"  {field_name}: {field_value}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tigers_u13() 