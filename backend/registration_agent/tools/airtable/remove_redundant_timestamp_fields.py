#!/usr/bin/env python3
"""
Remove redundant timestamp fields from registrations_2526 table.

This script removes two redundant timestamp fields:
1. payment_link_sent_timestamp - redundant with initial_db_write_timestamp
2. registration_completed_timestamp - vague and redundant with registration_status

Run this script after manually deleting the fields in Airtable UI.
"""

from pyairtable import Api
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# Fields to remove (for documentation purposes)
FIELDS_TO_REMOVE = [
    "payment_link_sent_timestamp",
    "registration_completed_timestamp"
]

def verify_fields_removed():
    """Verify that the redundant fields have been manually removed from Airtable."""
    
    if not AIRTABLE_API_KEY:
        print("❌ Error: AIRTABLE_API_KEY not found in environment variables")
        return False
    
    print("🔍 Checking if redundant timestamp fields have been removed...")
    
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Get table schema
        table_info = table.schema()
        existing_field_names = [field['name'] for field in table_info.fields]
        
        print(f"   Found {len(existing_field_names)} fields in table")
        
        # Check if redundant fields still exist
        still_exist = []
        for field_name in FIELDS_TO_REMOVE:
            if field_name in existing_field_names:
                still_exist.append(field_name)
        
        if still_exist:
            print("❌ The following redundant fields still exist:")
            for field in still_exist:
                print(f"   - {field}")
            print()
            print("Please manually delete these fields in Airtable UI first:")
            print("1. Go to Airtable → registrations_2526 table")
            print("2. Click on field header → Delete field")
            print("3. Confirm deletion")
            print("4. Then run this script again")
            return False
        
        print("✅ All redundant timestamp fields have been successfully removed!")
        print()
        print("Removed fields:")
        for field in FIELDS_TO_REMOVE:
            print(f"   - {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking table schema: {e}")
        return False

def main():
    """Main execution function."""
    print("🧹 UTJFC Registration Database - Remove Redundant Timestamp Fields")
    print("=" * 70)
    print()
    print("This script verifies removal of redundant timestamp fields:")
    for field in FIELDS_TO_REMOVE:
        print(f"   - {field}")
    print()
    print("⚠️  Note: Fields must be manually deleted in Airtable UI first!")
    print()
    
    # Verify fields have been removed
    success = verify_fields_removed()
    
    if success:
        print()
        print("✅ Cleanup verification complete!")
        print()
        print("🔄 Next steps:")
        print("   1. Update schema documentation if needed")
        print("   2. Remove any references from code (already checked - none found)")
        print("   3. Update field creation scripts if needed")
        sys.exit(0)
    else:
        print()
        print("❌ Cleanup verification failed.")
        print("Please manually delete the fields in Airtable UI and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 