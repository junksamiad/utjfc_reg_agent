# backend/registration_agent/tools/registration_tools/gocardless_payment.py
# GoCardless payment integration for UTJFC player registration

import os
import requests
from typing import Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_billing_request(
    player_full_name: str,
    team: str,
    age_group: str,
    signing_fee_amount: int = 100,   # £1.00 in pence (for testing)
    monthly_amount: int = 100,       # £1.00 in pence (for testing)
    gocardless_api_key: Optional[str] = None
) -> Dict:
    """
    Create a GoCardless billing request for UTJFC player registration.
    
    This creates both a one-off payment request (signing fee) and a mandate request 
    (monthly subscription) in a single billing request.
    
    Args:
        player_full_name (str): Full name of the player being registered
        team (str): Team the player is joining
        age_group (str): Age group (e.g., "U16", "U14", etc.)
        signing_fee_amount (int): One-off signing fee in pence (default: 4500 = £45.00)
        monthly_amount (int): Monthly subscription in pence (default: 2750 = £27.50)
        gocardless_api_key (str, optional): GoCardless API key. If not provided, will try to get from env
        
    Returns:
        dict: Result with:
            - success (bool): Whether the billing request was created successfully
            - message (str): Success message or error description
            - billing_request_id (str): GoCardless billing request ID if successful
            - billing_request_data (dict): Full response data if successful
            - player_full_name (str): Player name used in request
            - team (str): Team name used in request
            - age_group (str): Age group used in request
    """
    
    # Validate inputs
    if not player_full_name or not player_full_name.strip():
        return {
            "success": False,
            "message": "Player full name is required",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name or "",
            "team": team or "",
            "age_group": age_group or ""
        }
    
    if not team or not team.strip():
        return {
            "success": False,
            "message": "Team name is required",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name,
            "team": team or "",
            "age_group": age_group or ""
        }
    
    if not age_group or not age_group.strip():
        return {
            "success": False,
            "message": "Age group is required",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name,
            "team": team or "",
            "age_group": age_group or ""
        }
    
    # Get API key
    if not gocardless_api_key:
        gocardless_api_key = os.getenv("GOCARDLESS_API_KEY")
    
    if not gocardless_api_key:
        return {
            "success": False,
            "message": "GoCardless API key not configured. Payment setup unavailable.",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name,
            "team": team,
            "age_group": age_group
        }
    
    try:
        # Clean inputs
        player_name_clean = player_full_name.strip()
        team_clean = team.strip()
        age_group_clean = age_group.strip()
        
        # Construct the billing request payload
        payload = {
            "billing_requests": {
                "metadata": {
                    "player_name": player_name_clean,
                    "team": team_clean,
                    "age_group": age_group_clean
                },
                "payment_request": {
                    "description": f"UTJFC Signing-on Fee - {player_name_clean}",
                    "amount": signing_fee_amount,
                    "currency": "GBP",
                    "metadata": {
                        "player_name": player_name_clean,
                        "team": team_clean,
                        "type": "signing_fee"
                    }
                },
                "mandate_request": {
                    "currency": "GBP",
                    "description": f"UTJFC Monthly Subscription - {player_name_clean}",
                    "metadata": {
                        "player_name": player_name_clean,
                        "team": team_clean,
                        "type": "monthly_subscription"
                    }
                }
            }
        }
        
        # Make the API request
        url = "https://api.gocardless.com/billing_requests"
        headers = {
            "Authorization": f"Bearer {gocardless_api_key}",
            "Content-Type": "application/json",
            "GoCardless-Version": "2015-07-06"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
        # Extract billing request ID
        billing_request_id = response_data.get("billing_requests", {}).get("id", "")
        
        if not billing_request_id:
            return {
                "success": False,
                "message": "GoCardless billing request created but no ID returned",
                "billing_request_id": "",
                "billing_request_data": response_data,
                "player_full_name": player_full_name,
                "team": team,
                "age_group": age_group
            }
        
        return {
            "success": True,
            "message": f"Billing request created successfully for {player_name_clean}",
            "billing_request_id": billing_request_id,
            "billing_request_data": response_data,
            "player_full_name": player_full_name,
            "team": team,
            "age_group": age_group
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"GoCardless API request failed. Please try again.",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name,
            "team": team,
            "age_group": age_group
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Payment setup error. Please try again.",
            "billing_request_id": "",
            "billing_request_data": {},
            "player_full_name": player_full_name,
            "team": team,
            "age_group": age_group
        }


def create_billing_request_flow(
    billing_request_id: str, 
    parent_email: str = "",
    parent_first_name: str = "",
    parent_last_name: str = "",
    parent_address_line1: str = "",
    parent_city: str = "",
    parent_postcode: str = "",
    gocardless_api_key: Optional[str] = None
) -> Dict:
    """
    Create a GoCardless billing request flow to get the authorization URL.
    
    This is the second step that generates the actual payment link that users click.
    Includes prefilled customer data to auto-populate the payment form.
    
    Args:
        billing_request_id (str): The billing request ID from create_billing_request()
        parent_email (str): Parent's email address for prefilling
        parent_first_name (str): Parent's first name for prefilling
        parent_last_name (str): Parent's last name for prefilling
        parent_address_line1 (str): Parent's address line 1 for prefilling
        parent_city (str): Parent's city for prefilling
        parent_postcode (str): Parent's postcode for prefilling
        gocardless_api_key (str, optional): GoCardless API key. If not provided, will try to get from env
        
    Returns:
        dict: Result with:
            - success (bool): Whether the flow was created successfully
            - message (str): Success message or error description
            - authorization_url (str): The payment link URL if successful
            - billing_request_id (str): The billing request ID used
            - flow_data (dict): Full response data if successful
    """
    
    # Validate inputs
    if not billing_request_id or not billing_request_id.strip():
        return {
            "success": False,
            "message": "Billing request ID is required",
            "authorization_url": "",
            "billing_request_id": billing_request_id or "",
            "flow_data": {}
        }
    
    # Get API key
    if not gocardless_api_key:
        gocardless_api_key = os.getenv("GOCARDLESS_API_KEY")
    
    if not gocardless_api_key:
        return {
            "success": False,
            "message": "GoCardless API key not configured. Payment flow unavailable.",
            "authorization_url": "",
            "billing_request_id": billing_request_id,
            "flow_data": {}
        }
    
    try:
        # Construct the billing request flow payload
        payload = {
            "billing_request_flows": {
                "links": {
                    "billing_request": billing_request_id
                }
            }
        }
        
        # Add prefilled customer data if provided
        if any([parent_email, parent_first_name, parent_last_name, parent_address_line1, parent_city, parent_postcode]):
            prefilled_customer = {}
            
            if parent_email and parent_email.strip():
                prefilled_customer["email"] = parent_email.strip()
            if parent_first_name and parent_first_name.strip():
                prefilled_customer["given_name"] = parent_first_name.strip()
            if parent_last_name and parent_last_name.strip():
                prefilled_customer["family_name"] = parent_last_name.strip()
            if parent_address_line1 and parent_address_line1.strip():
                prefilled_customer["address_line1"] = parent_address_line1.strip()
            if parent_city and parent_city.strip():
                prefilled_customer["city"] = parent_city.strip()
            if parent_postcode and parent_postcode.strip():
                prefilled_customer["postal_code"] = parent_postcode.strip()
            
            # Always set country to GB for UK customers
            prefilled_customer["country_code"] = "GB"
            
            payload["billing_request_flows"]["prefilled_customer"] = prefilled_customer
        
        # Make the API request
        url = "https://api.gocardless.com/billing_request_flows"
        headers = {
            "Authorization": f"Bearer {gocardless_api_key}",
            "Content-Type": "application/json",
            "GoCardless-Version": "2015-07-06"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
        # Extract authorization URL
        authorization_url = response_data.get("billing_request_flows", {}).get("authorisation_url", "")
        
        if not authorization_url:
            return {
                "success": False,
                "message": "GoCardless flow created but no authorization URL returned",
                "authorization_url": "",
                "billing_request_id": billing_request_id,
                "flow_data": response_data
            }
        
        return {
            "success": True,
            "message": f"Payment link generated successfully",
            "authorization_url": authorization_url,
            "billing_request_id": billing_request_id,
            "flow_data": response_data
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"GoCardless flow API request failed. Please try again.",
            "authorization_url": "",
            "billing_request_id": billing_request_id,
            "flow_data": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Payment link generation error. Please try again.",
            "authorization_url": "",
            "billing_request_id": billing_request_id,
            "flow_data": {}
        }


# Test function for development/debugging
if __name__ == "__main__":
    print("Testing GoCardless Billing Request Creation:")
    print("-" * 60)
    
    # Test cases
    test_cases = [
        {
            "player_full_name": "Jamie Smith",
            "team": "Under 16s",
            "age_group": "U16"
        },
        {
            "player_full_name": "Sarah O'Connor",
            "team": "Under 14s Girls",
            "age_group": "U14"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['player_full_name']}")
        
        # Create billing request
        billing_result = create_billing_request(**test_case)
        print(f"Billing Request: {billing_result['success']} - {billing_result['message']}")
        
        if billing_result['success']:
            print(f"Billing Request ID: {billing_result['billing_request_id']}")
            
            # Create billing request flow
            flow_result = create_billing_request_flow(billing_result['billing_request_id'])
            print(f"Flow Creation: {flow_result['success']} - {flow_result['message']}")
            
            if flow_result['success']:
                print(f"Authorization URL: {flow_result['authorization_url']}") 