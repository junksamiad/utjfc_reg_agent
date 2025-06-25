#!/usr/bin/env python3
# backend/registration_agent/tools/registration_tools/debug_gocardless.py
# Debug script for GoCardless API issues

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_gocardless_api():
    """Debug the GoCardless API connection and request"""
    
    print("🔍 DEBUGGING GOCARDLESS API")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOCARDLESS_API_KEY")
    if not api_key:
        print("❌ No GOCARDLESS_API_KEY found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:15]}...")
    print(f"✅ API Key length: {len(api_key)} characters")
    print()
    
    # Test data (max 3 metadata properties per GoCardless requirement)
    test_payload = {
        "billing_requests": {
            "metadata": {
                "player_name": "Seb Hayton",
                "team": "Panthers",
                "age_group": "u11"
            },
            "payment_request": {
                "description": "UTJFC Signing-on Fee - Seb Hayton",
                "amount": 100,  # £1.00 in pence
                "currency": "GBP",
                "metadata": {
                    "player_name": "Seb Hayton",
                    "team": "Panthers",
                    "type": "signing_fee"
                }
            },
            "mandate_request": {
                "currency": "GBP",
                "description": "UTJFC Monthly Subscription - Seb Hayton",
                "metadata": {
                    "player_name": "Seb Hayton",
                    "team": "Panthers",
                    "type": "monthly_subscription"
                }
            }
        }
    }
    
    # API request details
    url = "https://api.gocardless.com/billing_requests"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "GoCardless-Version": "2015-07-06"
    }
    
    print("🚀 Making API request...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print("Payload:")
    print(json.dumps(test_payload, indent=2))
    print()
    
    try:
        response = requests.post(url, headers=headers, json=test_payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            print("✅ SUCCESS!")
            print("Response:")
            print(json.dumps(response_data, indent=2))
            
            billing_request_id = response_data.get("billing_requests", {}).get("id", "")
            if billing_request_id:
                print(f"\n🆔 Billing Request ID: {billing_request_id}")
                
        else:
            print(f"❌ HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print("Error details:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Raw response:")
                print(response.text)
                
    except requests.RequestException as e:
        print(f"💥 Request Exception: {str(e)}")
    except Exception as e:
        print(f"💥 General Exception: {str(e)}")


if __name__ == "__main__":
    debug_gocardless_api() 