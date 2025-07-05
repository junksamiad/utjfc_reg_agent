# backend/registration_agent/tools/registration_tools/create_payment_token.py
# Core function for creating GoCardless billing request (first part of payment flow)

import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import GoCardless SDK
try:
    import gocardless_pro
except ImportError:
    gocardless_pro = None

def create_payment_token(
    player_full_name: str,
    team_name: str,
    age_group: str,
    parent_full_name: str,
    parent_first_name: str,
    preferred_payment_day: int,
    parent_phone: str,
    signing_fee_amount: int = 100,    # £1.00 in pence (test amount)
    monthly_amount: int = 300,        # £3.00 in pence (test amount - allows 10% sibling discount = £2.70, above £1.00 minimum)
    gocardless_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a GoCardless billing request for UTJFC player registration.
    
    This creates both a one-off payment request (signing fee) and a mandate request 
    (monthly subscription) in a single billing request. Returns the billing_request_id
    which can be used later to create payment links when the user is ready to pay.
    
    Args:
        player_full_name (str): Full name of the player being registered
        team_name (str): Team the player is joining
        age_group (str): Age group (e.g., "U16", "U14", etc.)
        parent_full_name (str): Full name of parent/guardian
        preferred_payment_day (int): Day of month for monthly payments (1-31, or -1 for last day)
        parent_phone (str): Phone number of parent/guardian
        signing_fee_amount (int): One-off signing fee in pence (default: 100 = £1.00 for testing)
        monthly_amount (int): Monthly subscription in pence (default: 300 = £3.00 for testing, allows 10% sibling discount = £2.70, above £1.00 minimum)
        gocardless_api_key (str, optional): GoCardless API key. If not provided, will try to get from env
        
    Returns:
        dict: Result with:
            - success (bool): Whether the billing request was created successfully
            - message (str): Success message or error description
            - billing_request_id (str): GoCardless billing request ID (also serves as payment token)
            - player_full_name (str): Player name used in request
            - team_name (str): Team name used in request
            - age_group (str): Age group used in request
            - parent_full_name (str): Parent name used in request
            - preferred_payment_day (int): Payment day for monthly subscription
    """
    
    # DEBUG: Log function entry and parameters
    print("🎯 DEBUG: create_payment_token function called")
    print(f"   Received parameters:")
    print(f"     player_full_name='{player_full_name}'")
    print(f"     team_name='{team_name}'")
    print(f"     age_group='{age_group}'")
    print(f"     parent_full_name='{parent_full_name}'")
    print(f"     preferred_payment_day={preferred_payment_day}")
    print(f"     parent_phone='{parent_phone}'")
    print(f"     signing_fee_amount={signing_fee_amount}")
    print(f"     monthly_amount={monthly_amount}")
    
    # Validate inputs
    if not player_full_name or not player_full_name.strip():
        return {
            "success": False,
            "message": "Player full name is required",
            "billing_request_id": "",
            "player_full_name": player_full_name or "",
            "team_name": team_name or "",
            "age_group": age_group or "",
            "parent_full_name": parent_full_name or "",
            "preferred_payment_day": preferred_payment_day
        }
    
    if not team_name or not team_name.strip():
        return {
            "success": False,
            "message": "Team name is required",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name or "",
            "age_group": age_group or "",
            "parent_full_name": parent_full_name or "",
            "preferred_payment_day": preferred_payment_day
        }
    
    if not age_group or not age_group.strip():
        return {
            "success": False,
            "message": "Age group is required",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name or "",
            "age_group": age_group or "",
            "parent_full_name": parent_full_name or "",
            "preferred_payment_day": preferred_payment_day
        }
    
    if not parent_full_name or not parent_full_name.strip():
        return {
            "success": False,
            "message": "Parent full name is required",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name or "",
            "preferred_payment_day": preferred_payment_day
        }
    
    # Validate payment day
    if preferred_payment_day != -1 and (preferred_payment_day < 1 or preferred_payment_day > 31):
        return {
            "success": False,
            "message": "Preferred payment day must be 1-31 or -1 for last day of month",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name,
            "preferred_payment_day": preferred_payment_day
        }
    
    # Check SDK availability
    if not gocardless_pro:
        return {
            "success": False,
            "message": "GoCardless SDK not installed. Please install gocardless-pro package.",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name,
            "preferred_payment_day": preferred_payment_day
        }
    
    # Get API key
    if not gocardless_api_key:
        gocardless_api_key = os.getenv("GOCARDLESS_API_KEY")
    
    if not gocardless_api_key:
        return {
            "success": False,
            "message": "GoCardless API key not configured. Payment setup unavailable.",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name,
            "preferred_payment_day": preferred_payment_day
        }
    
    try:
        # Clean inputs
        player_name_clean = player_full_name.strip()
        team_clean = team_name.strip()
        age_group_clean = age_group.strip()
        parent_name_clean = parent_full_name.strip()
        
        # Initialize GoCardless client
        client = gocardless_pro.Client(
            access_token=gocardless_api_key,
            environment='live'  # Change to 'sandbox' for testing
        )
        
        # Create billing request using SDK
        billing_request = client.billing_requests.create(
            params={
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
                        "type": "signing_fee",
                        "team": team_clean
                    }
                },
                "mandate_request": {
                    "currency": "GBP",
                    "description": f"UTJFC Monthly Subscription - {player_name_clean}",
                    "metadata": {
                        "player_name": player_name_clean,
                        "type": "subscription",
                        "payment_day": str(preferred_payment_day)
                    }
                }
            }
        )
        
        # Extract billing request ID (this serves as our payment token)
        billing_request_id = billing_request.id
        
        if not billing_request_id:
            return {
                "success": False,
                "message": "GoCardless billing request created but no ID returned",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "team_name": team_name,
                "age_group": age_group,
                "parent_full_name": parent_full_name,
                "parent_first_name": parent_first_name,
                "preferred_payment_day": preferred_payment_day,
                "signing_fee_amount_pence": signing_fee_amount,
                "monthly_amount_pence": monthly_amount,
                "signing_fee_amount_pounds": round(signing_fee_amount / 100, 2),
                "monthly_amount_pounds": round(monthly_amount / 100, 2)
            }
        
        return {
            "success": True,
            "message": f"Payment token created successfully for {player_name_clean}",
            "billing_request_id": billing_request_id,  # This serves as payment token
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name,
            "parent_first_name": parent_first_name,
            "preferred_payment_day": preferred_payment_day,
            "signing_fee_amount_pence": signing_fee_amount,
            "monthly_amount_pence": monthly_amount,
            "signing_fee_amount_pounds": round(signing_fee_amount / 100, 2),
            "monthly_amount_pounds": round(monthly_amount / 100, 2)
        }
        
    except Exception as e:
        # Handle both GoCardless API errors and general exceptions
        error_message = "GoCardless API request failed. Please try again."
        if hasattr(e, 'error') and hasattr(e.error, 'message'):
            # GoCardless API error
            error_message = f"GoCardless error: {e.error.message}"
        elif str(e):
            # General error
            error_message = f"Payment setup error: {str(e)}"
            
        return {
            "success": False,
            "message": error_message,
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "team_name": team_name,
            "age_group": age_group,
            "parent_full_name": parent_full_name,
            "preferred_payment_day": preferred_payment_day,
            "signing_fee_amount_pence": signing_fee_amount,
            "monthly_amount_pence": monthly_amount,
            "signing_fee_amount_pounds": round(signing_fee_amount / 100, 2),
            "monthly_amount_pounds": round(monthly_amount / 100, 2)
        }


# Test function for development/debugging
if __name__ == "__main__":
    print("Testing Create Payment Token:")
    print("-" * 60)
    
    # Test case
    test_case = {
        "player_full_name": "Jamie Smith",
        "team_name": "Under 16s",
        "age_group": "U16",
        "parent_full_name": "Sarah Smith",
        "preferred_payment_day": 15
    }
    
    print(f"Test: {test_case['player_full_name']}")
    
    # Create payment token
    result = create_payment_token(**test_case)
    print(f"Success: {result['success']} - {result['message']}")
    
    if result['success']:
        print(f"Billing Request ID: {result['billing_request_id']}")
        print(f"Payment Day: {result['preferred_payment_day']}")
        print(f"Note: billing_request_id serves as payment token") 