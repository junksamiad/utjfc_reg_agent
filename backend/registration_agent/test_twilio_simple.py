#!/usr/bin/env python3
"""
Simple Twilio API test to verify credentials and basic functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twilio_basic():
    """Test basic Twilio connection and send a simple SMS"""
    
    print("🔧 Basic Twilio API Test")
    print("=" * 40)
    
    # Get credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    print(f"Account SID: {account_sid}")
    print(f"Auth Token: {auth_token[:8]}...")
    print(f"Phone Number: {twilio_phone}")
    
    try:
        # Import Twilio
        from twilio.rest import Client
        print("✅ Twilio SDK imported successfully")
        
        # Create client
        client = Client(account_sid, auth_token)
        print("✅ Twilio client created")
        
        # Test 1: Get account info
        print("\n📋 Testing account access...")
        try:
            account = client.api.accounts(account_sid).fetch()
            print(f"✅ Account status: {account.status}")
            print(f"✅ Account friendly name: {account.friendly_name}")
        except Exception as e:
            print(f"❌ Account access failed: {str(e)}")
            return False
        
        # Test 2: List phone numbers
        print("\n📱 Testing phone number access...")
        try:
            incoming_phone_numbers = client.incoming_phone_numbers.list(limit=5)
            print(f"✅ Found {len(incoming_phone_numbers)} phone numbers")
            for number in incoming_phone_numbers:
                print(f"   - {number.phone_number} ({number.friendly_name})")
        except Exception as e:
            print(f"❌ Phone number access failed: {str(e)}")
            return False
        
        # Test 3: Send SMS to your number
        print("\n💬 Testing SMS sending...")
        try:
            message = client.messages.create(
                body="Test SMS from UTJFC registration system - please ignore",
                from_=twilio_phone,
                to='+447835065013'  # Your number
            )
            print(f"✅ SMS sent successfully!")
            print(f"   Message SID: {message.sid}")
            print(f"   Status: {message.status}")
            print(f"   To: {message.to}")
            print(f"   From: {message.from_}")
            return True
            
        except Exception as e:
            print(f"❌ SMS sending failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # More detailed error info
            if hasattr(e, 'code'):
                print(f"   Error code: {e.code}")
            if hasattr(e, 'status'):
                print(f"   HTTP status: {e.status}")
            if hasattr(e, 'uri'):
                print(f"   Request URI: {e.uri}")
            return False
            
    except ImportError:
        print("❌ Twilio SDK not available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_twilio_basic()
    if success:
        print("\n🎉 Twilio test completed successfully!")
    else:
        print("\n💥 Twilio test failed!") 