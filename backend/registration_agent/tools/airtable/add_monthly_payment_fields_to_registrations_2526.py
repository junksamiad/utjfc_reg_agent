"""
Add Monthly Payment Tracking Fields to Registrations Table

Creates 18 fields total:
- 9 raw status fields (text) - Direct webhook data
- 9 formula fields (Y/N) - Clean boolean derived from status

Season: September 2024 - May 2025
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
AIRTABLE_BASE_ID = 'appBLxf3qmGIBc6ue'
REGISTRATIONS_TABLE_ID = 'tbl1D7hdjVcyHbT8a'
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def create_monthly_payment_fields():
    """Create monthly payment tracking fields using Airtable Meta API"""
    
    if not AIRTABLE_API_KEY:
        print("Error: AIRTABLE_API_KEY not found in environment variables")
        return
    
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{REGISTRATIONS_TABLE_ID}/fields'
    
    # Define months for the season
    months = [
        ('sept', 'September 2024'),
        ('oct', 'October 2024'), 
        ('nov', 'November 2024'),
        ('dec', 'December 2024'),
        ('jan', 'January 2025'),
        ('feb', 'February 2025'),
        ('mar', 'March 2025'),
        ('apr', 'April 2025'),
        ('may', 'May 2025')
    ]
    
    created_fields = []
    failed_fields = []
    
    for month_short, month_full in months:
        
        # 1. Create raw status field (text)
        status_field_name = f'{month_short}_subscription_payment_status'
        status_field_data = {
            'fields': [{
                'name': status_field_name,
                'type': 'singleLineText',
                'description': f'Raw payment status from GoCardless webhook for {month_full}. Values: confirmed, failed, cancelled, submitted, etc. Blank = no payment attempted yet.'
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=status_field_data, timeout=30)
            if response.status_code == 200:
                field_id = response.json()['fields'][0]['id']
                print(f"✅ Created status field: {status_field_name} (ID: {field_id})")
                created_fields.append((status_field_name, field_id))
            elif response.status_code == 422:
                print(f"⚠️  Status field {status_field_name} already exists")
            else:
                print(f"❌ Failed to create {status_field_name}: {response.status_code} - {response.text}")
                failed_fields.append(status_field_name)
        except Exception as e:
            print(f"❌ Error creating {status_field_name}: {str(e)}")
            failed_fields.append(status_field_name)
        
        # 2. Create clean boolean field (formula)
        boolean_field_name = f'subscription_paid_{month_short}'
        formula = f'IF({{{status_field_name}}} = "confirmed", "Y", "N")'
        
        boolean_field_data = {
            'fields': [{
                'name': boolean_field_name,
                'type': 'formula',
                'options': {
                    'formula': formula
                },
                'description': f'Clean Y/N indicator for {month_full} payment. Y = payment confirmed, N = not paid or failed. Auto-calculated from {status_field_name}.'
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=boolean_field_data, timeout=30)
            if response.status_code == 200:
                field_id = response.json()['fields'][0]['id']
                print(f"✅ Created boolean field: {boolean_field_name} (ID: {field_id})")
                created_fields.append((boolean_field_name, field_id))
            elif response.status_code == 422:
                print(f"⚠️  Boolean field {boolean_field_name} already exists")
            else:
                print(f"❌ Failed to create {boolean_field_name}: {response.status_code} - {response.text}")
                failed_fields.append(boolean_field_name)
        except Exception as e:
            print(f"❌ Error creating {boolean_field_name}: {str(e)}")
            failed_fields.append(boolean_field_name)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"✅ Successfully created: {len(created_fields)} fields")
    print(f"❌ Failed to create: {len(failed_fields)} fields")
    
    if failed_fields:
        print(f"\nFailed fields: {', '.join(failed_fields)}")
    
    print(f"\n🎯 Monthly payment tracking fields ready for webhook integration!")

if __name__ == "__main__":
    print("Adding Monthly Payment Tracking Fields to Registrations Table")
    print("=" * 70)
    create_monthly_payment_fields() 