#!/usr/bin/env python3
"""
Script to add SMS tracking fields to the registrations_2526 Airtable table.

Fields to add:
1. sms_sent_at (Date and time field)
2. sms_delivery_status (Single select field with options)
3. sms_delivery_error (Long text field)
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"  # registrations_2526 table ID
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def add_sms_fields():
    """Add SMS tracking fields to the registrations_2526 table"""
    
    if not AIRTABLE_API_KEY:
        print("❌ Error: AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Airtable Meta API endpoint for adding fields
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Fields to add
    fields_to_add = [
        {
            "name": "sms_sent_at",
            "type": "dateTime",
            "description": "Timestamp when the payment SMS was sent to the parent",
            "options": {
                "dateFormat": {
                    "name": "european"  # DD/MM/YYYY format
                },
                "timeFormat": {
                    "name": "24hour"
                },
                "timeZone": "Europe/London"
            }
        },
        {
            "name": "sms_delivery_status", 
            "type": "singleSelect",
            "description": "Status of the SMS delivery via Twilio",
            "options": {
                "choices": [
                    {"name": "pending", "color": "grayBright2"},
                    {"name": "sent", "color": "blueBright2"},
                    {"name": "delivered", "color": "greenBright2"},
                    {"name": "failed", "color": "redBright2"},
                    {"name": "undelivered", "color": "orangeBright2"}
                ]
            }
        },
        {
            "name": "sms_delivery_error",
            "type": "multilineText",
            "description": "Error message if SMS delivery failed (empty if successful)"
        }
    ]
    
    print("🔧 Adding SMS tracking fields to registrations_2526 table...")
    
    for field in fields_to_add:
        print(f"   Adding field: {field['name']} ({field['type']})")
        
        try:
            response = requests.post(url, headers=headers, json=field)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Successfully added {field['name']} (ID: {result.get('id', 'unknown')})")
            else:
                print(f"   ❌ Failed to add {field['name']}: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error adding {field['name']}: {str(e)}")
    
    print("\n🎉 SMS tracking fields addition complete!")
    print("\nNew fields added:")
    print("  • sms_sent_at (Date/Time) - When SMS was sent")
    print("  • sms_delivery_status (Single Select) - SMS delivery status") 
    print("  • sms_delivery_error (Long Text) - Error messages if any")
    
    return True

if __name__ == "__main__":
    success = add_sms_fields()
    if success:
        print("\n✅ SMS tracking fields setup complete!")
    else:
        print("\n❌ SMS tracking fields setup failed!") 