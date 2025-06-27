#!/usr/bin/env python3
"""
Script to add the sms_delivery_status field without colors (let Airtable assign default colors).
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

def add_simple_sms_delivery_status():
    """Add the sms_delivery_status field without color specifications"""
    
    if not AIRTABLE_API_KEY:
        print("❌ Error: AIRTABLE_API_KEY not found in environment variables")
        return False
    
    # Airtable Meta API endpoint for adding fields
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{TABLE_ID}/fields"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # SMS Delivery Status field without colors
    field_to_add = {
        "name": "sms_delivery_status", 
        "type": "singleSelect",
        "description": "Status of the SMS delivery via Twilio",
        "options": {
            "choices": [
                {"name": "pending"},
                {"name": "sent"},
                {"name": "delivered"},
                {"name": "failed"},
                {"name": "undelivered"}
            ]
        }
    }
    
    print("🔧 Adding sms_delivery_status field (simple version)...")
    print(f"   Adding field: {field_to_add['name']} ({field_to_add['type']})")
    
    try:
        response = requests.post(url, headers=headers, json=field_to_add)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Successfully added {field_to_add['name']} (ID: {result.get('id', 'unknown')})")
            print("\n🎉 SMS delivery status field added successfully!")
            print("\nField added:")
            print("  • sms_delivery_status (Single Select) - 5 delivery status options")
            return True
        else:
            print(f"   ❌ Failed to add {field_to_add['name']}: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error adding {field_to_add['name']}: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_simple_sms_delivery_status()
    if success:
        print("\n✅ SMS delivery status field setup complete!")
        print("You can manually set colors in the Airtable UI if desired.")
    else:
        print("\n❌ SMS delivery status field setup failed!") 