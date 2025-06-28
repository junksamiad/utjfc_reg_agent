"""
AI-Friendly SMS Payment Link Tool

Wrapper for sending payment SMS to parents after registration completion.
This tool should be called in parallel with update_reg_details_to_db in routine 29.
"""

from .send_sms_payment_link_tool import send_sms_payment_link, SendSMSPaymentLinkInput
import asyncio


async def send_payment_sms(billing_request_id: str, parent_phone: str, child_name: str, parent_name: str, record_id: str = None) -> dict:
    """
    Send SMS payment link to parent (AI-friendly interface)
    
    Args:
        billing_request_id: GoCardless billing request ID from create_payment_token
        parent_phone: Parent's phone number (UK format - will be formatted automatically)
        child_name: Child's name for personalization
        parent_name: Parent's first name for personalization
        record_id: Optional Airtable record ID for database logging
    
    Returns:
        dict: Success status and delivery information
    """
    
    # Create input data
    input_data = SendSMSPaymentLinkInput(
        billing_request_id=billing_request_id,
        parent_phone=parent_phone,
        child_name=child_name,
        parent_name=parent_name,
        record_id=record_id
    )
    
    # Send SMS
    result = await send_sms_payment_link(input_data)
    
    return result


def send_payment_sms_sync(billing_request_id: str, parent_phone: str, child_name: str, parent_name: str, record_id: str = None) -> dict:
    """
    Synchronous wrapper for send_payment_sms (for non-async contexts)
    
    Args:
        billing_request_id: GoCardless billing request ID from create_payment_token
        parent_phone: Parent's phone number (UK format)
        child_name: Child's name for personalization
        parent_name: Parent's first name for personalization
        record_id: Optional Airtable record ID for database logging
    
    Returns:
        dict: Success status and delivery information
    """
    
    # Run async function in sync context
    return asyncio.run(send_payment_sms(billing_request_id, parent_phone, child_name, parent_name, record_id))


# For AI agent tool calling
async def ai_send_sms_payment_link(billing_request_id: str, parent_phone: str, child_name: str, parent_name: str, record_id: str = None) -> str:
    """
    AI agent interface for sending payment SMS
    
    This function will be called by the AI agent in routine 29 after create_payment_token.
    
    Args:
        billing_request_id: The billing request ID returned from create_payment_token 
        parent_phone: Parent's phone number from registration data
        child_name: Child's name from registration data
        parent_name: Parent's first name from registration data
        record_id: Airtable record ID from update_reg_details_to_db (optional)
    
    Returns:
        str: Human-readable success/failure message for the AI agent
    """
    
    try:
        result = await send_payment_sms(billing_request_id, parent_phone, child_name, parent_name, record_id)
        
        if result['success']:
            return (
                f"✅ Payment SMS sent successfully to {result['formatted_phone']} for {child_name}. "
                f"Parent will receive link: {result['payment_link']} "
                f"Twilio Message ID: {result['twilio_message_sid']}"
            )
        else:
            return (
                f"❌ Failed to send payment SMS to {parent_phone} for {child_name}. "
                f"Error: {result['error']}"
            )
            
    except Exception as e:
        return f"❌ Unexpected error sending payment SMS: {str(e)}" 