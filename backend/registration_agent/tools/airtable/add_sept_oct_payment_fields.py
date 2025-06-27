#!/usr/bin/env python3
"""
Add September and October Payment Fields (Part 1)

Creates 4 fields:
- 2 raw status fields (text) - via SDK
- 2 formula fields (Y/N) - must be created manually in Airtable

Note: Airtable API does not support creating formula fields via API.
Formula fields must be created manually in the Airtable web interface.
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

def add_sept_oct_fields():
    """Add September and October payment tracking fields"""
    
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Initialize Airtable API
    api = Api(AIRTABLE_API_KEY)
    
    print("🔧 Adding September and October payment fields to registrations_2526 table...")
    print(f"   Base ID: {BASE_ID}")
    print(f"   Table ID: {TABLE_ID}")
    print()
    
    # Fields to add (only text fields via SDK - formula fields need manual creation)
    text_fields = [
        {
            'name': 'sep_subscription_payment_status',
            'type': 'singleLineText',
            'options': {
                'description': 'Raw payment status from GoCardless webhook for September 2024. Values: confirmed, failed, cancelled, submitted, etc. Blank = no payment attempted yet.'
            }
        },
        {
            'name': 'oct_subscription_payment_status', 
            'type': 'singleLineText',
            'options': {
                'description': 'Raw payment status from GoCardless webhook for October 2024. Values: confirmed, failed, cancelled, submitted, etc. Blank = no payment attempted yet.'
            }
        }
    ]
    
    # Formula fields that must be created manually in Airtable interface
    formula_fields = [
        {
            'name': 'subscription_paid_sep',
            'formula': 'IF({sep_subscription_payment_status} = "confirmed", "Y", "N")',
            'description': 'Clean Y/N indicator for September 2024 payment. Y = payment confirmed, N = not paid or failed. Auto-calculated from sep_subscription_payment_status.'
        },
        {
            'name': 'subscription_paid_oct',
            'formula': 'IF({oct_subscription_payment_status} = "confirmed", "Y", "N")',
            'description': 'Clean Y/N indicator for October 2024 payment. Y = payment confirmed, N = not paid or failed. Auto-calculated from oct_subscription_payment_status.'
        }
    ]
    
    print("📝 Creating text fields via SDK...")
    success_count = 0
    
    for field in text_fields:
        if create_field(api, field['name'], field['type'], field['options']):
            success_count += 1
    
    print(f"\n📊 SDK Fields Summary: {success_count}/{len(text_fields)} text fields created successfully")
    
    if success_count == len(text_fields):
        print("✅ All SDK-supported fields created successfully!")
        
        print("\n🔧 Manual Steps Required in Airtable Interface:")
        print("   Create these formula fields manually:")
        for field in formula_fields:
            print(f"\n   📋 Field: {field['name']}")
            print(f"      Type: Formula")
            print(f"      Formula: {field['formula']}")
            print(f"      Description: {field['description']}")
        
        print("\n🎯 Instructions:")
        print("   1. Open Airtable in web browser")
        print("   2. Go to registrations_2526 table")
        print("   3. Click '+' to add new field")
        print("   4. Select 'Formula' as field type")
        print("   5. Copy/paste the formula above")
        print("   6. Add the description")
        print("   7. Repeat for both formula fields")
        
        print("\n✅ Setup will be complete after manual formula field creation!")
        return True
    else:
        print("⚠️  Some text fields failed to create - check errors above")
        return False

if __name__ == "__main__":
    add_sept_oct_fields() 