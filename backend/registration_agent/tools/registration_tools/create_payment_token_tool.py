# backend/registration_agent/tools/registration_tools/create_payment_token_tool.py
# OpenAI function tool definition for GoCardless payment token creation

import json
try:
    from .create_payment_token import create_payment_token
except ImportError:
    from create_payment_token import create_payment_token

# Tool definition for OpenAI Responses API
CREATE_PAYMENT_TOKEN_TOOL = {
    "type": "function",
    "name": "create_payment_token",
        "description": """Create a GoCardless billing request for UTJFC player registration.
    
    This tool creates the first part of the payment flow by generating a persistent 
    billing request ID that can be used later to create payment links when the user 
    is ready to pay. This decouples registration from immediate payment.
    
    The tool creates:
    - One-off signing fee payment request (£45.00)
    - Monthly subscription Direct Debit mandate (£27.50 per month)
    - Billing request ID that serves as payment token for later link generation
    
    The agent should call this tool when:
    - User has confirmed all registration information is correct
    - User has provided their preferred payment day for monthly subscription
    - Ready to complete the registration and setup payment for later
    
    The tool will extract required information from the conversation context including:
    - Player's full name
    - Parent's full name  
    - Age group/team assignment
    - Preferred payment day
    
    Returns a billing request ID for database storage (also serves as payment token).
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
            "preferred_payment_day": {
                "type": "integer",
                "description": "REQUIRED: Day of month for monthly subscription payments (1-31, or -1 for last day of month). Must be collected from user in routine 29."
            },
            "parent_phone": {
                "type": "string",
                "description": "REQUIRED: Parent's phone number for SMS payment link. Must be extracted from conversation history (e.g., '07835065013', '0161 123 4567')"
            }
        },
        "required": ["player_full_name", "age_group", "team_name", "parent_full_name", "preferred_payment_day", "parent_phone"]
    }
}

def handle_create_payment_token(**kwargs) -> str:
    """
    Handle the create_payment_token tool call from agents.
    
    This function creates a GoCardless billing request for the registration and
    returns the billing request ID and payment token for storage in the database.
    
    Args:
        **kwargs: Tool call parameters including:
            - player_full_name (str): Full name of the player
            - age_group (str): Age group in format 'u<number>' (e.g., 'u16', 'u14')
            - team_name (str): Team name with proper capitalization (e.g., 'Panthers')
            - parent_full_name (str): Parent/guardian full name (required)
            - preferred_payment_day (int): Day of month for monthly payments (1-31 or -1)
            - parent_phone (str): Parent's phone number for SMS payment link
        
    Returns:
        str: JSON string with payment token creation results
    """
    try:
        # Extract parameters from kwargs
        player_full_name = kwargs.get('player_full_name', '')
        age_group = kwargs.get('age_group', '')
        team_name = kwargs.get('team_name', '')
        parent_full_name = kwargs.get('parent_full_name', '')
        preferred_payment_day = kwargs.get('preferred_payment_day')
        parent_phone = kwargs.get('parent_phone', '')
        
        # Validate inputs
        if not player_full_name or not player_full_name.strip():
            error_result = {
                "success": False,
                "message": "Player full name is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required player name - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if not age_group or not age_group.strip():
            error_result = {
                "success": False,
                "message": "Age group is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required age group - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if not team_name or not team_name.strip():
            error_result = {
                "success": False,
                "message": "Team name is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required team name - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if not parent_full_name or not parent_full_name.strip():
            error_result = {
                "success": False,
                "message": "Parent full name is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required parent name - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if preferred_payment_day is None:
            error_result = {
                "success": False,
                "message": "Preferred payment day is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required payment day - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        if not parent_phone or not parent_phone.strip():
            error_result = {
                "success": False,
                "message": "Parent phone number is required to create payment token",
                "billing_request_id": "",
                "player_full_name": player_full_name,
                "age_group": age_group,
                "team_name": team_name,
                "parent_full_name": parent_full_name,
                "preferred_payment_day": preferred_payment_day,
                "parent_phone": parent_phone,
                "usage_note": "Missing required parent phone - please collect this information first"
            }
            return json.dumps(error_result, indent=2)
        
        # Create payment token
        result = create_payment_token(
            player_full_name=player_full_name.strip(),
            team=team_name.strip(),
            age_group=age_group.strip(),
            parent_full_name=parent_full_name.strip(),
            preferred_payment_day=int(preferred_payment_day)
        )
        
        # Add usage guidance based on result
        if result["success"]:
            # Add parent phone to the result for reference
            result["parent_phone"] = parent_phone.strip()
            
            result["usage_note"] = (
                f"Payment token created successfully for {result['player_full_name']}. "
                f"Use the billing_request_id to save to database (it serves as the payment token). "
                f"Monthly payments will be taken on day {result['preferred_payment_day']} of each month "
                f"{'(last day)' if result['preferred_payment_day'] == -1 else ''}. "
                f"SMS payment link sent automatically to {parent_phone}."
            )
            
            # PROGRAMMATIC SMS TRIGGER: Send SMS automatically when payment token is created
            try:
                # Import SMS function for background execution
                import asyncio
                from .send_sms_payment_link import send_payment_sms
                
                # Extract data for SMS from the successful result
                billing_request_id = result.get("billing_request_id", "")
                child_name = result.get("player_full_name", "")
                parent_phone_clean = parent_phone.strip()
                
                print(f"🚀 PROGRAMMATIC SMS TRIGGER: Sending SMS for billing_request_id={billing_request_id}")
                print(f"📱 SMS details: child={child_name}, phone={parent_phone_clean}")
                
                # Send SMS asynchronously (non-blocking)
                try:
                    # Create async task to send SMS in background
                    loop = asyncio.get_event_loop()
                    loop.create_task(send_payment_sms(billing_request_id, parent_phone_clean, child_name))
                    print("✅ SMS task created successfully")
                except RuntimeError:
                    # If no event loop is running, run the SMS function directly
                    asyncio.run(send_payment_sms(billing_request_id, parent_phone_clean, child_name))
                    print("✅ SMS sent directly (no event loop)")
                
            except Exception as sms_error:
                print(f"⚠️ SMS trigger failed (non-blocking): {sms_error}")
                # Don't fail the payment token creation if SMS fails
                result["sms_error"] = str(sms_error)
        else:
            result["usage_note"] = (
                f"Payment token creation failed: {result['message']}. "
                f"Please check all required information is collected and try again."
            )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Payment token creation error: {str(e)}",
            "billing_request_id": "",
            "player_full_name": kwargs.get('player_full_name', ''),
            "age_group": kwargs.get('age_group', ''),
            "team_name": kwargs.get('team_name', ''),
            "parent_full_name": kwargs.get('parent_full_name', ''),
            "preferred_payment_day": kwargs.get('preferred_payment_day'),
            "parent_phone": kwargs.get('parent_phone', ''),
            "usage_note": "Tool error occurred - please try again or contact support"
        }
        return json.dumps(error_result, indent=2) 