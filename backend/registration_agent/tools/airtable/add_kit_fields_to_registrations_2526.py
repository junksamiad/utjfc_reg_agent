#!/usr/bin/env python3
"""
Script to add kit-related fields to the registrations_2526 Airtable table.

This script adds the following kit fields:
- new_kit_required: Boolean Y/N (single select with green/red colors)
- kit_type_required: Single select - Goalkeeper / Outfield  
- kit_size: Single select - all the size options (5/6, 7/8, 9/10, 11/12, 13/14, S, M, L, XL, 2XL, 3XL)
- shirt_number: Single select - 1 to 25

Run this script once to update the table schema.
"""

import os
import sys
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"  # registrations_2526 table
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def create_field(api, field_name, field_type, field_options=None):
    """Create a single field in the Airtable table."""
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
        
        # Use the correct pyairtable method signature
        result = api.table(BASE_ID, TABLE_ID).create_field(
            name=field_name,
            type=field_type,
            description=description,
            options=options
        )
        print(f"✅ Created field: {field_name} ({field_type})")
        return True
        
    except Exception as e:
        if "FIELD_NAME_ALREADY_EXISTS" in str(e):
            print(f"⚠️  Field already exists: {field_name}")
            return True
        else:
            print(f"❌ Failed to create field {field_name}: {e}")
            return False

def add_kit_fields():
    """Add kit-related fields to the registrations_2526 table."""
    
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Initialize Airtable API
    api = Api(AIRTABLE_API_KEY)
    
    print(f"🚀 Adding kit-related fields to registrations_2526 table...")
    print(f"   Base ID: {BASE_ID}")
    print(f"   Table ID: {TABLE_ID}")
    print()
    
    success_count = 0
    total_count = 0
    
    # Define kit fields to add
    kit_fields = [
        # New kit required (boolean Y/N)
        {
            "name": "new_kit_required",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Whether player requires a new kit this season"
            }
        },
        
        # Kit type required (Goalkeeper / Outfield)
        {
            "name": "kit_type_required",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Goalkeeper", "color": "yellowBright"},
                    {"name": "Outfield", "color": "blueBright"}
                ],
                "description": "Type of kit required (Goalkeeper or Outfield)"
            }
        },
        
        # Kit size (all size options)
        {
            "name": "kit_size",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "5/6", "color": "purpleBright"},
                    {"name": "7/8", "color": "purpleBright"},
                    {"name": "9/10", "color": "purpleBright"},
                    {"name": "11/12", "color": "purpleBright"},
                    {"name": "13/14", "color": "purpleBright"},
                    {"name": "S", "color": "cyanBright"},
                    {"name": "M", "color": "cyanBright"},
                    {"name": "L", "color": "cyanBright"},
                    {"name": "XL", "color": "cyanBright"},
                    {"name": "2XL", "color": "cyanBright"},
                    {"name": "3XL", "color": "cyanBright"}
                ],
                "description": "Kit size selected by player/parent"
            }
        },
        
        # Shirt number (1 to 25)
        {
            "name": "shirt_number",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "1", "color": "greenBright"},
                    {"name": "2", "color": "greenBright"},
                    {"name": "3", "color": "greenBright"},
                    {"name": "4", "color": "greenBright"},
                    {"name": "5", "color": "greenBright"},
                    {"name": "6", "color": "blueBright"},
                    {"name": "7", "color": "blueBright"},
                    {"name": "8", "color": "blueBright"},
                    {"name": "9", "color": "blueBright"},
                    {"name": "10", "color": "blueBright"},
                    {"name": "11", "color": "purpleBright"},
                    {"name": "12", "color": "purpleBright"},
                    {"name": "13", "color": "purpleBright"},
                    {"name": "14", "color": "purpleBright"},
                    {"name": "15", "color": "purpleBright"},
                    {"name": "16", "color": "redBright"},
                    {"name": "17", "color": "redBright"},
                    {"name": "18", "color": "redBright"},
                    {"name": "19", "color": "redBright"},
                    {"name": "20", "color": "redBright"},
                    {"name": "21", "color": "orangeBright"},
                    {"name": "22", "color": "orangeBright"},
                    {"name": "23", "color": "orangeBright"},
                    {"name": "24", "color": "orangeBright"},
                    {"name": "25", "color": "orangeBright"}
                ],
                "description": "Shirt number chosen by player (1-25)"
            }
        }
    ]
    
    # Add each field
    for field_def in kit_fields:
        total_count += 1
        field_name = field_def["name"]
        field_type = field_def["type"]
        field_options = field_def.get("options", {})
        
        if create_field(api, field_name, field_type, field_options):
            success_count += 1
    
    print()
    print(f"📊 Summary:")
    print(f"   Total fields processed: {total_count}")
    print(f"   Successfully created/verified: {success_count}")
    print(f"   Failed: {total_count - success_count}")
    
    if success_count == total_count:
        print("✅ All kit fields successfully added to registrations_2526 table!")
        print()
        print("🔄 Next steps:")
        print("   1. Update the Pydantic schema in registration_data_models.py")
        print("   2. Update routines 32 and 33 to save kit_size and shirt_number")
        print("   3. Create routine 34 for photo upload")
        print("   4. Test the complete kit selection flow")
        return True
    else:
        print("⚠️  Some fields failed to create. Check the errors above.")
        return False

def main():
    """Main execution function."""
    print("🏗️  UTJFC Registration Kit Fields Update")
    print("=" * 50)
    print()
    print("This will add the following fields to registrations_2526:")
    print("  • new_kit_required (Y/N)")
    print("  • kit_type_required (Goalkeeper/Outfield)")
    print("  • kit_size (5/6, 7/8, 9/10, 11/12, 13/14, S, M, L, XL, 2XL, 3XL)")
    print("  • shirt_number (1-25)")
    print()
    
    # Confirm before proceeding
    response = input("Continue with adding these fields? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return
    
    success = add_kit_fields()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 