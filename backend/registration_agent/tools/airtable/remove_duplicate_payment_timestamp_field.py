#!/usr/bin/env python3
"""
Remove Duplicate Payment Timestamp Field

This script removes the redundant 'payment_link_sent_timestamp' field from the
registrations_2526 table, since it duplicates the functionality of 'sms_sent_at'.
"""

import os
import sys
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
FIELD_TO_REMOVE = "payment_link_sent_timestamp"

def remove_duplicate_field():
    """Remove the duplicate payment_link_sent_timestamp field"""
    
    # Get Airtable API key
    api_key = os.getenv('AIRTABLE_API_KEY')
    if not api_key:
        print("❌ Error: AIRTABLE_API_KEY not found in environment variables")
        return False
    
    try:
        # Initialize Airtable API
        api = Api(api_key)
        table = api.table(BASE_ID, TABLE_ID)
        
        print(f"🔍 Checking for field: {FIELD_TO_REMOVE}")
        
        # Get table schema to check if field exists
        schema = table.schema()
        
        # Check if the field exists
        field_exists = False
        field_id = None
        
        for field in schema.fields:
            if field.name == FIELD_TO_REMOVE:
                field_exists = True
                field_id = field.id
                break
        
        if not field_exists:
            print(f"✅ Field '{FIELD_TO_REMOVE}' does not exist - already cleaned up!")
            return True
        
        print(f"📋 Found field '{FIELD_TO_REMOVE}' with ID: {field_id}")
        print(f"📝 Field description: When SMS payment link was sent to parent")
        print(f"🔄 This is redundant with 'sms_sent_at' field")
        print()
        
        # Confirm removal
        response = input(f"❓ Remove the redundant '{FIELD_TO_REMOVE}' field? (y/N): ")
        if response.lower() != 'y':
            print("❌ Field removal cancelled.")
            return False
        
        # Remove the field
        print(f"🗑️  Removing field: {FIELD_TO_REMOVE}")
        
        # Note: Airtable doesn't have a direct API to delete fields via pyairtable
        # We need to use the Airtable REST API directly
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields/{field_id}"
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Successfully removed field: {FIELD_TO_REMOVE}")
            print()
            print("🎯 Benefits:")
            print("   ✅ Cleaner database schema")
            print("   ✅ No more duplicate timestamp fields")
            print("   ✅ SMS metrics all grouped together (sms_*)")
            print()
            print("📊 Remaining SMS fields:")
            print("   - sms_sent_at: When SMS was sent")
            print("   - sms_delivery_status: Delivery status (sent/failed)")
            print("   - sms_delivery_error: Error details if failed")
            
            return True
            
        elif response.status_code == 404:
            print(f"✅ Field '{FIELD_TO_REMOVE}' already removed or doesn't exist")
            return True
            
        else:
            print(f"❌ Failed to remove field. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error removing field: {str(e)}")
        return False


def main():
    """Main execution function"""
    print("🧹 Remove Duplicate Payment Timestamp Field")
    print("=" * 50)
    print()
    print("This script will remove the redundant 'payment_link_sent_timestamp' field")
    print("since it duplicates the functionality of 'sms_sent_at'.")
    print()
    
    success = remove_duplicate_field()
    
    if success:
        print()
        print("✅ Field cleanup completed successfully!")
        sys.exit(0)
    else:
        print()
        print("❌ Field cleanup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 