#!/usr/bin/env python3
"""
Script to add photo-related fields to the registrations_2526 Airtable.

This script adds three new fields:
1. id_image_link - Text field for storing S3 URL
2. id_photo_required - Single select Y/N, defaults to Y
3. id_photo_provided - Computed field based on id_image_link presence

Run this script once to update the table schema.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def add_photo_fields():
    """Add photo-related fields to the registrations_2526 table"""
    
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
            "name": "id_image_link",
            "type": "url",
            "description": "S3 URL link to the player's ID photo uploaded during registration"
        },
        {
            "name": "id_photo_required", 
            "type": "singleSelect",
            "description": "Whether an ID photo is required for this registration",
            "options": {
                "choices": [
                    {"name": "Y", "color": "greenBright"},
                    {"name": "N", "color": "redBright"}
                ]
            }
        },
        {
            "name": "id_photo_provided",
            "type": "formula", 
            "description": "Computed field: Y if id_image_link exists, N if empty",
            "options": {
                "formula": "IF({id_image_link}, 'Y', 'N')"
            }
        }
    ]
    
    print("🔧 Adding photo-related fields to registrations_2526 table...")
    
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
    
    print("\n🎉 Photo fields addition complete!")
    print("\nNew fields added:")
    print("  • id_image_link (URL) - Stores S3 photo URL")
    print("  • id_photo_required (Single Select) - Y/N, defaults to Y") 
    print("  • id_photo_provided (Formula) - Auto-computed based on link presence")
    
    return True

if __name__ == "__main__":
    add_photo_fields() 