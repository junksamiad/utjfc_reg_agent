# backend/registration_agent/tools/registration_tools/gocardless_payment_tool.py
# OpenAI function tool definition for GoCardless payment link creation

import json
try:
    from .gocardless_payment import create_billing_request, create_billing_request_flow
except ImportError:
    from gocardless_payment import create_billing_request, create_billing_request_flow

# Tool definition for OpenAI Responses API
CREATE_SIGNUP_PAYMENT_LINK_TOOL = {
    "type": "function",
    "name": "create_signup_payment_link",
    "description": """Create a GoCardless payment link for UTJFC player registration.
    
    This tool creates a complete payment solution that includes:
    - One-off signing fee payment (£45.00)
    - Monthly subscription Direct Debit setup (£27.50 per month, Sep-May)
    - Returns a secure payment link for the user to complete both payments
    
    The agent should call this tool when:
    - All player registration information has been collected
    - User has confirmed they want to proceed with payment
    - User has provided their preferred payment day for monthly subscription
    
    The tool will extract required information from the conversation context including:
    - Player's full name
    - Age group/team assignment
    - Payment day preference
    
    The returned payment link connects to GoCardless which handles secure banking integration.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "player_full_name": {
                "type": "string",
                "description": "REQUIRED: Full name of the player being registered. Must be extracted from conversation history (e.g., 'Jamie Smith', 'Sarah O'Connor')"
            },
            "age_group": {
                "type": "string", 
                "description": "REQUIRED: Age group in format 'u<number>' with lowercase 'u'. Must be determined from child's date of birth (e.g., 'u16', 'u14', 'u12', 'u10', 'u8')"
            },
            "team_name": {
                "type": "string",
                "description": "REQUIRED: Team name with proper capitalization. Must be extracted from conversation history (e.g., 'Panthers', 'Tigers', 'Eagles')"
            },
            "parent_full_name": {
                "type": "string",
                "description": "REQUIRED: Full name of parent/guardian setting up the payment. Must be extracted from conversation history (e.g., 'John Smith', 'Sarah O'Connor')"
            },
            "parent_email": {
                "type": "string",
                "description": "REQUIRED: Parent's email address for payment notifications and prefilling payment form. Must be collected during registration (e.g., 'john.smith@email.com')"
            },
            "parent_address": {
                "type": "string",
                "description": "REQUIRED: Parent's full address for prefilling payment form. Must be extracted from conversation history (e.g., '123 Main Street, Manchester')"
            },
            "parent_postcode": {
                "type": "string", 
                "description": "REQUIRED: Parent's postcode for prefilling payment form. Must be extracted from conversation history (e.g., 'M41 9JJ')"
            }
        },
        "required": ["player_full_name", "age_group", "team_name", "parent_full_name", "parent_email", "parent_address", "parent_postcode"]
    }
}

def handle_create_signup_payment_link(**kwargs) -> str:
    """
    Handle the create_signup_payment_link tool call from agents.
    
    This function performs both steps of the GoCardless payment setup:
    1. Create billing request with player/payment details
    2. Create billing request flow to get the authorization URL with prefilled parent data
    
    Args:
        **kwargs: Tool call parameters including:
            - player_full_name (str): Full name of the player
            - age_group (str): Age group in format 'u<number>' (e.g., 'u16', 'u14')
            - team_name (str): Team name with proper capitalization (e.g., 'Panthers')
            - parent_full_name (str): Parent/guardian full name (required)
            - parent_email (str): Parent's email for prefilling (required)
            - parent_address (str): Parent's address for prefilling (required)
            - parent_postcode (str): Parent's postcode for prefilling (required)
        
    Returns:
        str: JSON string with payment link creation results
    """
    try:
        # Extract parameters from kwargs
        player_full_name = kwargs.get('player_full_name', '')
        age_group = kwargs.get('age_group', '')
        team_name = kwargs.get('team_name', '')
        parent_full_name = kwargs.get('parent_full_name', '')
        parent_email = kwargs.get('parent_email', '')
        parent_address = kwargs.get('parent_address', '')
        parent_postcode = kwargs.get('parent_postcode', '')
        # Validate inputs
        if not player_full_name or not player_full_name.strip():
            error_result = {
                "success": False,
                "message": "Player full name is required to create payment link",
                "payment_link": "",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "usage_note": "Missing required player name - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if not age_group or not age_group.strip():
            error_result = {
                "success": False,
                "message": "Age group is required to create payment link",
                "payment_link": "",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "usage_note": "Missing required age group - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        # Step 1: Create billing request
        billing_result = create_billing_request(
            player_full_name=player_full_name.strip(),
            team=team_name.strip(),
            age_group=age_group.strip()
        )
        
        if not billing_result["success"]:
            error_result = {
                "success": False,
                "message": f"Failed to create payment request: {billing_result['message']}",
                "payment_link": "",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "usage_note": "GoCardless billing request failed - please try again or contact support"
            }
            return json.dumps(error_result, indent=2)
        
        billing_request_id = billing_result["billing_request_id"]
        
        # Parse parent name for first/last if provided
        parent_first_name = ""
        parent_last_name = ""
        if parent_full_name and parent_full_name.strip():
            name_parts = parent_full_name.strip().split()
            if len(name_parts) >= 2:
                parent_first_name = name_parts[0]
                parent_last_name = " ".join(name_parts[1:])
            elif len(name_parts) == 1:
                parent_first_name = name_parts[0]
        
        # Parse address for city extraction if needed
        parent_city = ""
        parent_address_line1 = parent_address
        if parent_address and "," in parent_address:
            address_parts = [part.strip() for part in parent_address.split(",")]
            if len(address_parts) >= 2:
                parent_address_line1 = address_parts[0]
                # For "11 Granby Rd, Stretford, Manchester" - we want "Manchester" as city
                parent_city = address_parts[-1]  # Always use last part as city
        
        # Step 2: Create billing request flow to get payment link with prefilled data
        flow_result = create_billing_request_flow(
            billing_request_id=billing_request_id,
            parent_email=parent_email,
            parent_first_name=parent_first_name,
            parent_last_name=parent_last_name,
            parent_address_line1=parent_address_line1,
            parent_city=parent_city,
            parent_postcode=parent_postcode
        )
        
        if not flow_result["success"]:
            error_result = {
                "success": False,
                "message": f"Failed to create payment link: {flow_result['message']}",
                "payment_link": "",
                "billing_request_id": billing_request_id,
                "player_full_name": player_full_name,
                "age_group": age_group,
                "usage_note": "GoCardless payment link generation failed - please try again or contact support"
            }
            return json.dumps(error_result, indent=2)
        
        # Success - return the payment link
        success_result = {
            "success": True,
            "message": f"Payment link created successfully for {player_full_name}",
            "payment_link": flow_result["authorization_url"],
            "billing_request_id": billing_request_id,
            "player_full_name": player_full_name,
            "age_group": age_group,
            "team": team_name,
            "parent_name": parent_full_name,
            "usage_note": f"Payment link ready - provide this URL to the user. It includes both £1.00 signing fee and £1.00/month Direct Debit mandate setup for testing. Monthly payment scheduling will be handled separately."
        }
        
        return json.dumps(success_result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Payment link creation error: {str(e)}",
            "payment_link": "",
            "billing_request_id": "",
            "player_full_name": player_full_name,
            "age_group": age_group,
            "usage_note": "Tool error occurred - please try again or contact support"
        }
        return json.dumps(error_result, indent=2)


 