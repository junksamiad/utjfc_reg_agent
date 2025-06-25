#!/usr/bin/env python3
"""
Script to add missing fields to the registrations_2526 Airtable table.

This script adds all the fields identified as missing from our analysis,
including parent contact information, payment architecture fields, and 
registration metadata fields.

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

def add_missing_fields():
    """Add all missing fields to the registrations_2526 table."""
    
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Initialize Airtable API
    api = Api(AIRTABLE_API_KEY)
    
    print(f"🚀 Adding missing fields to registrations_2526 table...")
    print(f"   Base ID: {BASE_ID}")
    print(f"   Table ID: {TABLE_ID}")
    print()
    
    success_count = 0
    total_count = 0
    
    # Define all fields to add
    fields_to_add = [
        # Parent Contact Information
        {
            "name": "parent_telephone",
            "type": "singleLineText",
            "options": {
                "description": "Parent's telephone number (UK mobile 07... or Manchester landline 0161...)"
            }
        },
        {
            "name": "parent_email", 
            "type": "email",
            "options": {
                "description": "Parent's email address (validated format, stored lowercase)"
            }
        },
        {
            "name": "parent_dob",
            "type": "singleLineText", 
            "options": {
                "description": "Parent's date of birth in DD-MM-YYYY format"
            }
        },
        
        # Communication Preferences
        {
            "name": "communication_consent",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Parent's consent for email/SMS club communications"
            }
        },
        
        # Previous Club Information
        {
            "name": "previous_team_name",
            "type": "singleLineText",
            "options": {
                "description": "Name of previous football team (if child played elsewhere last season)"
            }
        },
        {
            "name": "played_elsewhere_last_season",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Whether child played for another team last season"
            }
        },
        
        # U16+ Player Contact Details
        {
            "name": "player_telephone",
            "type": "singleLineText",
            "options": {
                "description": "Player's own mobile number (required for U16+, must be different from parent's)"
            }
        },
        {
            "name": "player_email",
            "type": "email",
            "options": {
                "description": "Player's own email address (required for U16+, must be different from parent's)"
            }
        },
        
        # Registration Meta Information
        {
            "name": "registration_type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "100", "color": "blueBright"},
                    {"name": "200", "color": "greenBright"}
                ],
                "description": "Type of registration (100 = re-registration, 200 = new registration)"
            }
        },
        {
            "name": "season",
            "type": "singleLineText",
            "options": {
                "description": "Season code (2526 for 2025-26 season)"
            }
        },
        {
            "name": "original_registration_code",
            "type": "singleLineText",
            "options": {
                "description": "Full registration code entered by user (e.g., 200-tigers-u10-2526)"
            }
        },
        
        # Payment Architecture Fields
        {
            "name": "billing_request_id",
            "type": "singleLineText",
            "options": {
                "description": "GoCardless billing request ID (serves as payment token)"
            }
        },
        {
            "name": "preferred_payment_day",
            "type": "number",
            "options": {
                "description": "Day of month for monthly payments (1-31 or -1 for last day)",
                "precision": 0  # Integer only
            }
        },
        {
            "name": "signing_on_fee_paid",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Whether £45 signing fee has been paid"
            }
        },
        {
            "name": "mandate_authorised",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Whether Direct Debit mandate has been authorised"
            }
        },
        {
            "name": "subscription_activated",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ],
                "description": "Whether monthly subscription is active"
            }
        },
                 {
             "name": "payment_link_sent_timestamp",
             "type": "dateTime",
             "options": {
                 "description": "When SMS payment link was sent to parent",
                 "dateFormat": {"name": "iso"},
                 "timeFormat": {"name": "24hour"},
                 "timeZone": "Europe/London"
             }
         },
         {
             "name": "registration_completed_timestamp",
             "type": "dateTime",
             "options": {
                 "description": "When registration was marked complete",
                 "dateFormat": {"name": "iso"},
                 "timeFormat": {"name": "24hour"},
                 "timeZone": "Europe/London"
             }
         },
        
        # Additional Tracking Fields
                 {
             "name": "initial_db_write_timestamp",
             "type": "dateTime",
             "options": {
                 "description": "When routine 29 completed and data saved to DB",
                 "dateFormat": {"name": "iso"},
                 "timeFormat": {"name": "24hour"},
                 "timeZone": "Europe/London"
             }
         },
        {
            "name": "payment_follow_up_count",
            "type": "number",
            "options": {
                "description": "Number of follow-up reminders sent (for automation)",
                "precision": 0  # Integer only
            }
        },
        {
            "name": "registration_status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "pending_payment", "color": "yellowBright"},
                    {"name": "active", "color": "greenBright"},
                    {"name": "suspended", "color": "redBright"},
                    {"name": "incomplete", "color": "grayBright"}
                ],
                "description": "Current registration status"
            }
        }
    ]
    
    # Add each field
    for field_def in fields_to_add:
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
        print("✅ All fields successfully added to registrations_2526 table!")
        print()
        print("🔄 Next steps:")
        print("   1. Update the table schema file: registrations_2526.py")
        print("   2. Create the update_reg_details_to_db function")
        print("   3. Test the complete flow from routine 29")
        return True
    else:
        print("⚠️  Some fields failed to create. Check the errors above.")
        return False

def main():
    """Main execution function."""
    print("🏗️  UTJFC Registration Database Schema Update")
    print("=" * 50)
    
    # Confirm before proceeding
    response = input("This will add fields to the registrations_2526 table. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled.")
        return
    
    success = add_missing_fields()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 