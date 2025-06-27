#!/usr/bin/env python3
"""
Add Remaining Monthly Payment Fields (Nov 2024 - May 2025)

Creates fields for 7 remaining months:
- 7 raw status fields (text)
- 7 computed fields (text - to be manually converted to formula)

Note: Computed fields are created as text fields initially.
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

def add_remaining_monthly_fields():
    """Add remaining monthly payment tracking fields (Nov 2024 - May 2025)"""
    
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Initialize Airtable API
    api = Api(AIRTABLE_API_KEY)
    
    print("🔧 Adding remaining monthly payment fields to registrations_2526 table...")
    print(f"   Base ID: {BASE_ID}")
    print(f"   Table ID: {TABLE_ID}")
    print("   Months: Nov 2024 - May 2025 (7 months)")
    print()
    
    # Define the remaining months
    months = [
        {"short": "nov", "full": "November 2024"},
        {"short": "dec", "full": "December 2024"},
        {"short": "jan", "full": "January 2025"},
        {"short": "feb", "full": "February 2025"},
        {"short": "mar", "full": "March 2025"},
        {"short": "apr", "full": "April 2025"},
        {"short": "may", "full": "May 2025"}
    ]
    
    # Create all fields for each month
    all_fields = []
    
    for month in months:
        # Raw status field
        all_fields.append({
            'name': f'{month["short"]}_subscription_payment_status',
            'type': 'singleLineText',
            'options': {
                'description': f'Raw payment status from GoCardless webhook for {month["full"]}. Values: confirmed, failed, cancelled, submitted, etc. Blank = no payment attempted yet.'
            }
        })
        
        # Computed field (created as text, to be converted to formula manually)
        all_fields.append({
            'name': f'subscription_paid_{month["short"]}',
            'type': 'singleLineText',
            'options': {
                'description': f'Clean Y/N indicator for {month["full"]} payment. Y = payment confirmed, N = not paid or failed. TO BE CONVERTED TO FORMULA: IF({{{month["short"]}_subscription_payment_status}} = "confirmed", "Y", "N")'
            }
        })
    
    print(f"📝 Creating {len(all_fields)} fields via SDK...")
    success_count = 0
    
    for field in all_fields:
        if create_field(api, field['name'], field['type'], field['options']):
            success_count += 1
    
    print(f"\n📊 SDK Fields Summary: {success_count}/{len(all_fields)} fields created successfully")
    
    if success_count == len(all_fields):
        print("✅ All fields created successfully!")
        
        print("\n🔧 Manual Steps Required in Airtable Interface:")
        print("   Convert these computed fields from text to formula:")
        print()
        
        for month in months:
            field_name = f'subscription_paid_{month["short"]}'
            formula = f'IF({{{month["short"]}_subscription_payment_status}} = "confirmed", "Y", "N")'
            print(f"   📋 {field_name}")
            print(f"      Formula: {formula}")
            print()
        
        print("🎯 Instructions for each computed field:")
        print("   1. Open Airtable in web browser")
        print("   2. Go to registrations_2526 table")
        print("   3. Click on the field header (subscription_paid_xxx)")
        print("   4. Click 'Customize field type'")
        print("   5. Change from 'Single line text' to 'Formula'")
        print("   6. Copy/paste the formula from above")
        print("   7. Save the field")
        print("   8. Repeat for all 7 computed fields")
        
        print(f"\n✅ Complete setup: {len(months)} months × 2 fields = {len(all_fields)} total fields!")
        print("📋 Total monthly payment tracking: Sept 2024 - May 2025 (9 months)")
        return True
    else:
        print("⚠️  Some fields failed to create - check errors above")
        return False

if __name__ == "__main__":
    add_remaining_monthly_fields() 