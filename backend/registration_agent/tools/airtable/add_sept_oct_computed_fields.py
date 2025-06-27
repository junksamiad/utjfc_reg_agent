#!/usr/bin/env python3
"""
Add September and October Computed Fields

Creates the missing computed fields for Sep and Oct as text fields:
- subscription_paid_sep (text - to be manually converted to formula)
- subscription_paid_oct (text - to be manually converted to formula)

Note: These are created as text fields initially.
User will manually convert them to formula fields in Airtable interface.
"""

import os
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
BASE_ID = 'appBLxf3qmGIBc6ue'
TABLE_ID = 'tbl1D7hdjVcyHbT8a'
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def create_field(api, field_name, field_type, field_options=None):
    """Create a single field in the Airtable table using the SDK."""
    try:
        # Extract description from options if provided
        description = None
        options = None
        
        if field_options:
            description = field_options.get("description")
            # Remove description from options since it's a separate parameter
            options = {k: v for k, v in field_options.items() if k != "description"}
            if not options:  # If options is empty after removing description
                options = None
        
        # Use the pyairtable SDK to create the field
        result = api.table(BASE_ID, TABLE_ID).create_field(
            name=field_name,
            type=field_type,
            description=description,
            options=options
        )
        print(f"   ✅ Successfully created {field_name} ({field_type})")
        return True
        
    except Exception as e:
        error_str = str(e)
        if "FIELD_NAME_ALREADY_EXISTS" in error_str or "DUPLICATE_OR_EMPTY_FIELD_NAME" in error_str:
            print(f"   ✅ Field already exists: {field_name}")
            return True
        else:
            print(f"   ❌ Failed to create field {field_name}: {e}")
            return False

def add_sep_oct_computed_fields():
    """Add September and October computed fields as text fields"""
    
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Initialize Airtable API
    api = Api(AIRTABLE_API_KEY)
    
    print("🔧 Adding September and October computed fields to registrations_2526 table...")
    print(f"   Base ID: {BASE_ID}")
    print(f"   Table ID: {TABLE_ID}")
    print()
    
    # Computed fields for Sep and Oct (created as text, to be converted to formula manually)
    computed_fields = [
        {
            'name': 'subscription_paid_sep',
            'type': 'singleLineText',
            'options': {
                'description': 'Clean Y/N indicator for September 2024 payment. Y = payment confirmed, N = not paid or failed. TO BE CONVERTED TO FORMULA: IF({sep_subscription_payment_status} = "confirmed", "Y", "N")'
            }
        },
        {
            'name': 'subscription_paid_oct',
            'type': 'singleLineText',
            'options': {
                'description': 'Clean Y/N indicator for October 2024 payment. Y = payment confirmed, N = not paid or failed. TO BE CONVERTED TO FORMULA: IF({oct_subscription_payment_status} = "confirmed", "Y", "N")'
            }
        }
    ]
    
    print(f"📝 Creating {len(computed_fields)} computed fields via SDK...")
    success_count = 0
    
    for field in computed_fields:
        if create_field(api, field['name'], field['type'], field['options']):
            success_count += 1
    
    print(f"\n📊 SDK Fields Summary: {success_count}/{len(computed_fields)} fields created successfully")
    
    if success_count == len(computed_fields):
        print("✅ All computed fields created successfully!")
        
        print("\n🔧 Manual Steps Required in Airtable Interface:")
        print("   Convert these computed fields from text to formula:")
        print()
        
        print("   📋 subscription_paid_sep")
        print("      Formula: IF({sep_subscription_payment_status} = \"confirmed\", \"Y\", \"N\")")
        print()
        
        print("   📋 subscription_paid_oct")
        print("      Formula: IF({oct_subscription_payment_status} = \"confirmed\", \"Y\", \"N\")")
        print()
        
        print("🎯 Instructions for each computed field:")
        print("   1. Open Airtable in web browser")
        print("   2. Go to registrations_2526 table")
        print("   3. Click on the field header (subscription_paid_xxx)")
        print("   4. Click 'Customize field type'")
        print("   5. Change from 'Single line text' to 'Formula'")
        print("   6. Copy/paste the formula from above")
        print("   7. Save the field")
        print("   8. Repeat for both fields")
        
        print(f"\n✅ Now you have all 9 computed fields ready to convert!")
        print("📋 Complete: Sep-May 2025 (9 months × 2 fields = 18 total fields)")
        return True
    else:
        print("⚠️  Some fields failed to create - check errors above")
        return False

if __name__ == "__main__":
    add_sep_oct_computed_fields() 