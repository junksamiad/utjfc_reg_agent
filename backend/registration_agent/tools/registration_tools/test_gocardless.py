#!/usr/bin/env python3
# backend/registration_agent/tools/registration_tools/test_gocardless.py
# Test script for GoCardless payment integration

import os
import sys
from dotenv import load_dotenv

# Add the current directory to path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables
load_dotenv()

try:
    from gocardless_payment import create_billing_request, create_billing_request_flow
    from gocardless_payment_tool import handle_create_signup_payment_link
except ImportError:
    # Handle relative imports when running as script
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from gocardless_payment import create_billing_request, create_billing_request_flow
    from gocardless_payment_tool import handle_create_signup_payment_link
import json

def test_gocardless_integration():
    """Test the complete GoCardless payment integration"""
    
    print("🧪 TESTING GOCARDLESS PAYMENT INTEGRATION")
    print("=" * 60)
    
    # Check if API key is configured
    api_key = os.getenv("GOCARDLESS_API_KEY")
    if not api_key:
        print("❌ GOCARDLESS_API_KEY not found in environment variables")
        print("Please add your GoCardless API key to .env file:")
        print("GOCARDLESS_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ GoCardless API Key found: {api_key[:10]}...")
    print()
    
    # Single test case for live system with £1 test amounts
    test_cases = [
        {
            "name": "Live Test: £1 Payment Integration with Prefilled Data",
            "player_full_name": "Seb Hayton",
            "age_group": "u11",
            "team_name": "Panthers",
            "parent_full_name": "Lee Hayton",
            "parent_email": "junksamiad@gmail.com",
            "parent_address": "11 Granby Rd, Stretford, Manchester",
            "parent_postcode": "M32 8JL"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 {test_case['name']}")
        print(f"   Player: {test_case['player_full_name']}")
        print(f"   Age Group: {test_case['age_group']}")
        print(f"   Team: {test_case.get('team_name', 'N/A')}")
        print(f"   Parent: {test_case.get('parent_full_name', 'N/A')}")
        print(f"   Email: {test_case.get('parent_email', 'N/A')}")
        print(f"   Address: {test_case.get('parent_address', 'N/A')}")
        print(f"   Postcode: {test_case.get('parent_postcode', 'N/A')}")
        print()
        
        try:
            # Test the complete tool function
            result_json = handle_create_signup_payment_link(
                player_full_name=test_case['player_full_name'],
                age_group=test_case['age_group'],
                team_name=test_case.get('team_name', ''),
                parent_full_name=test_case.get('parent_full_name', ''),
                parent_email=test_case.get('parent_email', ''),
                parent_address=test_case.get('parent_address', ''),
                parent_postcode=test_case.get('parent_postcode', '')
            )
            
            result = json.loads(result_json)
            
            if result.get('success'):
                print(f"   ✅ SUCCESS: {result['message']}")
                print(f"   📋 Billing Request ID: {result['billing_request_id']}")
                print(f"   👥 Team: {result.get('team', 'N/A')}")
                print()
                print(f"   🚀 CLICK THIS PAYMENT LINK TO TEST PREFILLED DATA:")
                print(f"   🔗 {result['payment_link']}")
                print()
                print(f"   💰 Payment Setup: £1.00 signing fee + £1.00/month DD mandate")
                print(f"   📧 Should prefill with: {test_case.get('parent_email', 'N/A')}")
                print(f"   🏠 Should prefill with: {test_case.get('parent_address', 'N/A')}")
                print(f"   📅 Note: Monthly payment scheduling handled separately")
                success_count += 1
            else:
                print(f"   ❌ FAILED: {result['message']}")
                print(f"   📝 Note: {result.get('usage_note', 'N/A')}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {str(e)}")
        
        print("-" * 60)
        print()
    
    # Summary
    print(f"📊 TEST SUMMARY")
    print(f"   Successful: {success_count}/{len(test_cases)}")
    print(f"   Failed: {len(test_cases) - success_count}/{len(test_cases)}")
    
    if success_count == len(test_cases):
        print("🎉 ALL TESTS PASSED - GoCardless integration is working!")
        return True
    else:
        print("⚠️  Some tests failed - check configuration and API key")
        return False


def test_individual_functions():
    """Test individual functions separately for debugging"""
    
    print("\n🔧 TESTING INDIVIDUAL FUNCTIONS")
    print("=" * 60)
    
    # Test data
    player_name = "Test Player"
    team = "Under 16s"
    age_group = "U16"
    
    print(f"Testing with: {player_name}, {team}, {age_group}")
    print()
    
    # Test Step 1: Create billing request
    print("Step 1: Creating billing request...")
    billing_result = create_billing_request(
        player_full_name=player_name,
        team=team,
        age_group=age_group
    )
    
    print(f"Result: {billing_result['success']} - {billing_result['message']}")
    if billing_result['success']:
        print(f"Billing Request ID: {billing_result['billing_request_id']}")
        
        # Test Step 2: Create billing request flow
        print("\nStep 2: Creating billing request flow...")
        flow_result = create_billing_request_flow(billing_result['billing_request_id'])
        
        print(f"Result: {flow_result['success']} - {flow_result['message']}")
        if flow_result['success']:
            print(f"Authorization URL: {flow_result['authorization_url']}")
            return True
    
    return False


if __name__ == "__main__":
    print("Starting GoCardless Integration Tests...\n")
    
    # Run main integration test
    main_success = test_gocardless_integration()
    
    # If main test fails, run individual function tests for debugging
    if not main_success:
        print("\n" + "=" * 60)
        print("RUNNING INDIVIDUAL FUNCTION TESTS FOR DEBUGGING")
        test_individual_functions()
    
    print("\nTest completed.") 