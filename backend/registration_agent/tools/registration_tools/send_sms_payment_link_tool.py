"""
SMS Payment Link Tool - Twilio Integration

Sends payment SMS to parents with registration completion and payment link.
Handles UK phone number formatting and logs delivery status to Airtable.
"""

from pydantic import BaseModel, Field
from typing import Optional
import os
import re
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from .sms_metrics_queue import queue_sms_metrics
from dotenv import load_dotenv

load_dotenv()


class SendSMSPaymentLinkInput(BaseModel):
    """Input model for sending SMS payment link"""
    billing_request_id: str = Field(description="GoCardless billing request ID to include in payment link")
    parent_phone: str = Field(description="Parent's phone number (UK format)")
    child_name: str = Field(description="Child's name to personalize the SMS message")
    parent_name: str = Field(description="Parent's first name to personalize the SMS greeting")
    record_id: Optional[str] = Field(default=None, description="Airtable record ID for database logging")


def format_uk_phone_for_twilio(phone: str) -> str:
    """
    Format UK phone number for Twilio SMS sending
    
    Converts:
    - 07123456789 -> +447123456789
    - +44 7123 456789 -> +447123456789
    - 447123456789 -> +447123456789
    """
    # Remove all spaces, dashes, and brackets
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Remove any leading zeros after country code
    if cleaned.startswith('+44'):
        cleaned = '+44' + cleaned[3:].lstrip('0')
    elif cleaned.startswith('44') and len(cleaned) >= 12:
        cleaned = '+44' + cleaned[2:].lstrip('0')
    elif cleaned.startswith('07') and len(cleaned) == 11:
        cleaned = '+447' + cleaned[2:]
    elif cleaned.startswith('7') and len(cleaned) == 10:
        cleaned = '+447' + cleaned[1:]
    else:
        # If it doesn't match expected UK patterns, return as-is with + prefix
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
    
    return cleaned


def validate_uk_mobile(phone: str) -> bool:
    """Validate that the phone number is a UK mobile number"""
    formatted = format_uk_phone_for_twilio(phone)
    # UK mobile numbers start with +447 and are 13 digits total
    uk_mobile_pattern = r'^\+447[0-9]{9}$'
    return bool(re.match(uk_mobile_pattern, formatted))


async def send_sms_payment_link(input_data: SendSMSPaymentLinkInput) -> dict:
    """
    Send SMS payment link to parent via Twilio
    
    Returns:
        dict: Success/failure status with delivery information
    """
    try:
        # Get environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        payment_base_url = os.getenv('PAYMENT_BASE_URL', 'https://utjfc.ngrok.app')
        
        if not all([account_sid, auth_token, twilio_phone]):
            return {
                'success': False,
                'error': 'Missing Twilio configuration in environment variables',
                'sms_delivery_status': 'failed',
                'sms_delivery_error': 'Missing Twilio credentials'
            }
        
        # Format phone number for Twilio
        formatted_phone = format_uk_phone_for_twilio(input_data.parent_phone)
        
        # Validate UK mobile number
        if not validate_uk_mobile(input_data.parent_phone):
            return {
                'success': False,
                'error': f'Invalid UK mobile number: {input_data.parent_phone}',
                'sms_delivery_status': 'failed',
                'sms_delivery_error': f'Invalid UK mobile number format: {input_data.parent_phone}'
            }
        
        # Create payment link
        payment_link = f"{payment_base_url}/reg_setup/{input_data.billing_request_id}"
        
        # Create SMS message
        sms_message = (
            f"Hi {input_data.parent_name}, it's the registration assistant from Urmston Town Juniors FC! "
            f"{input_data.child_name}'s registration is complete. Please complete payment to secure your place: "
            f"{payment_link} Payment required."
        )
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send SMS
        message = client.messages.create(
            body=sms_message,
            from_=twilio_phone,
            to=formatted_phone
        )
        
        # Prepare SMS metrics for queuing
        current_time = datetime.utcnow().isoformat() + 'Z'
        sms_metrics = {
            'sms_sent_at': current_time,
            'sms_delivery_status': 'sent',  # Twilio queued = sent for us
            'sms_delivery_error': '',
            'twilio_message_sid': message.sid,
            'formatted_phone': formatted_phone,
            'child_name': input_data.child_name,
            'parent_name': input_data.parent_name
        }
        
        # Queue SMS metrics for background processing (non-blocking)
        queue_success = queue_sms_metrics(input_data.billing_request_id, sms_metrics)
        if queue_success:
            print(f"📊 SMS metrics queued for {input_data.billing_request_id}")
        else:
            print(f"⚠️ Failed to queue SMS metrics for {input_data.billing_request_id}")
        
        return {
            'success': True,
            'message': f'SMS sent successfully to {formatted_phone}',
            'twilio_message_sid': message.sid,
            'formatted_phone': formatted_phone,
            'payment_link': payment_link,
            'sms_delivery_status': 'sent',
            'sms_delivery_error': ''
        }
        
    except TwilioException as e:
        error_msg = f"Twilio error: {str(e)}"
        
        # Queue error metrics for background processing
        error_metrics = {
            'sms_sent_at': datetime.utcnow().isoformat() + 'Z',
            'sms_delivery_status': 'failed',
            'sms_delivery_error': error_msg,
            'child_name': input_data.child_name,
            'parent_name': input_data.parent_name,
            'formatted_phone': format_uk_phone_for_twilio(input_data.parent_phone)
        }
        
        queue_success = queue_sms_metrics(input_data.billing_request_id, error_metrics)
        if queue_success:
            print(f"📊 SMS error metrics queued for {input_data.billing_request_id}")
        else:
            print(f"⚠️ Failed to queue SMS error metrics")
        
        return {
            'success': False,
            'error': error_msg,
            'sms_delivery_status': 'failed',
            'sms_delivery_error': error_msg
        }
        
    except Exception as e:
        error_msg = f"Unexpected error sending SMS: {str(e)}"
        
        # Queue error metrics for background processing
        error_metrics = {
            'sms_sent_at': datetime.utcnow().isoformat() + 'Z',
            'sms_delivery_status': 'failed',
            'sms_delivery_error': error_msg,
            'child_name': input_data.child_name,
            'parent_name': input_data.parent_name,
            'formatted_phone': format_uk_phone_for_twilio(input_data.parent_phone)
        }
        
        queue_success = queue_sms_metrics(input_data.billing_request_id, error_metrics)
        if queue_success:
            print(f"📊 SMS error metrics queued for {input_data.billing_request_id}")
        else:
            print(f"⚠️ Failed to queue SMS error metrics")
        
        return {
            'success': False,
            'error': error_msg,
            'sms_delivery_status': 'failed',
            'sms_delivery_error': error_msg
        } 