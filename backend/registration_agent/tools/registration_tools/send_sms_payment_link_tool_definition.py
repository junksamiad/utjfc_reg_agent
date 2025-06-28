"""
OpenAI Tool Definition for SMS Payment Link Tool

This defines the SMS function schema for AI agents to call.
"""

# OpenAI function schema for the SMS payment link tool
SEND_SMS_PAYMENT_LINK_TOOL = {
    "type": "function",
    "name": "ai_send_sms_payment_link",
    "description": """Send SMS payment link to parent after registration completion.
    
    This function should be called IN PARALLEL with update_reg_details_to_db in routine 29.
    It sends an SMS to the parent containing a payment link with the billing_request_id.
    
    Call this function immediately after create_payment_token succeeds to send the payment 
    link via SMS while the database write happens in parallel.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "billing_request_id": {
                "type": "string",
                "description": "The billing request ID returned from create_payment_token - this will be included in the payment link"
            },
            "parent_phone": {
                "type": "string", 
                "description": "Parent's phone number (UK format) - will be automatically formatted for SMS delivery"
            },
            "child_name": {
                "type": "string",
                "description": "Child's name to personalize the SMS message"
            },
            "parent_name": {
                "type": "string",
                "description": "Parent's first name to personalize the SMS greeting"
            },
            "record_id": {
                "type": "string",
                "description": "Optional Airtable record ID from update_reg_details_to_db for SMS delivery logging"
            }
        },
        "required": ["billing_request_id", "parent_phone", "child_name", "parent_name"]
    }
} 