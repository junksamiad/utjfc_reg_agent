#!/usr/bin/env python3
"""
Test script for SMS payment link tool

Tests Twilio integration and phone number formatting.
"""

import asyncio
import os
from dotenv import load_dotenv
from tools.registration_tools.send_sms_payment_link import ai_send_sms_payment_link, send_payment_sms

# Load environment variables
load_dotenv()

async def test_sms_tool():
    """Test the SMS tool with sample data"""
    
    print("🧪 Testing SMS Payment Link Tool")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Checking Twilio configuration...")
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_token = os.getenv('TWILIO_AUTH_TOKEN') 
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    payment_url = os.getenv('PAYMENT_BASE_URL', 'https://utjfc.ngrok.app')
    
    if not all([twilio_sid, twilio_token, twilio_phone]):
        print("❌ Missing Twilio configuration!")
        print(f"   TWILIO_ACCOUNT_SID: {'✅' if twilio_sid else '❌'}")
        print(f"   TWILIO_AUTH_TOKEN: {'✅' if twilio_token else '❌'}")
        print(f"   TWILIO_PHONE_NUMBER: {'✅' if twilio_phone else '❌'}")
        return
    else:
        print("✅ Twilio configuration found!")
        print(f"   Account SID: {twilio_sid[:8]}...")
        print(f"   Phone Number: {twilio_phone}")
        print(f"   Payment Base URL: {payment_url}")
    
    print("\n📱 Testing phone number formatting...")
    
    # Test phone number formatting
    from tools.registration_tools.send_sms_payment_link_tool import format_uk_phone_for_twilio, validate_uk_mobile
    
    test_numbers = [
        "07123456789",
        "+44 7123 456 789", 
        "447123456789",
        "7123456789"
    ]
    
    for number in test_numbers:
        formatted = format_uk_phone_for_twilio(number)
        valid = validate_uk_mobile(number)
        print(f"   {number} -> {formatted} {'✅' if valid else '❌'}")
    
    print("\n🚀 Testing SMS sending...")
    
    # Test data
    test_billing_request_id = "BRQ123456789TEST"
    test_parent_phone = "+447835065013"  # Send to Lee's actual phone for testing
    test_child_name = "Test Child"
    
    print(f"   Sending test SMS to: {test_parent_phone}")
    print(f"   Child name: {test_child_name}")
    print(f"   Billing Request ID: {test_billing_request_id}")
    
    # Send test SMS
    try:
        result = await send_payment_sms(
            billing_request_id=test_billing_request_id,
            parent_phone=test_parent_phone, 
            child_name=test_child_name
        )
        
        if result['success']:
            print("✅ SMS sent successfully!")
            print(f"   Message SID: {result['twilio_message_sid']}")
            print(f"   Formatted phone: {result['formatted_phone']}")
            print(f"   Payment link: {result['payment_link']}")
        else:
            print("❌ SMS sending failed!")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n🧪 Testing AI agent interface...")
    
    # Test AI agent interface
    try:
        ai_result = await ai_send_sms_payment_link(
            billing_request_id=test_billing_request_id,
            parent_phone=test_parent_phone,
            child_name=test_child_name
        )
        
        print(f"   AI Response: {ai_result}")
        
    except Exception as e:
        print(f"❌ AI interface test failed: {str(e)}")
    
    print("\n✅ SMS tool testing complete!")

if __name__ == "__main__":
    asyncio.run(test_sms_tool()) 