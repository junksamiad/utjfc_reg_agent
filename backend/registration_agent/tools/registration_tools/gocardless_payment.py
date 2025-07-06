# backend/registration_agent/tools/registration_tools/gocardless_payment.py
# GoCardless payment integration for UTJFC player registration

import os
import requests
from typing import Dict, Optional
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

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


def activate_subscription(
    mandate_id: str,
    registration_record: Dict,
    gocardless_api_key: Optional[str] = None
) -> Dict:
    """
    Activate a GoCardless subscription after mandate authorization.
    
    This should be called from the mandate_active webhook to set up the monthly
    subscription payments using the authorized mandate. Handles smart start date
    logic based on GoCardless timing requirements.
    
    GoCardless Timing Requirements:
    - 3 days advance notice (handled automatically by GoCardless)
    - Payment submission must be 2 business days before collection date
    - Minimum 3-day buffer used to ensure compliance
    
    Args:
        mandate_id (str): GoCardless mandate ID from webhook
        registration_record (dict): Complete registration record from database
        gocardless_api_key (str, optional): GoCardless API key. If not provided, will try to get from env
        
    Returns:
        dict: Result with:
            - success (bool): Whether the subscription(s) were created successfully
            - message (str): Success message or error description
            - ongoing_subscription_id (str): Main subscription ID if successful
            - interim_subscription_id (str): Interim subscription ID if created
            - subscription_data (dict): Full response data if successful
            - player_full_name (str): Player name used in request
            - start_date (str): Calculated ongoing subscription start date
            - interim_created (bool): Whether an interim subscription was needed
    """
    
    # Validate inputs
    if not mandate_id or not mandate_id.strip():
        return {
            "success": False,
            "message": "Mandate ID is required",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": "",
            "start_date": "",
            "interim_created": False
        }
    
    if not registration_record or not isinstance(registration_record, dict):
        return {
            "success": False,
            "message": "Registration record is required",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": "",
            "start_date": "",
            "interim_created": False
        }
    
    # Extract data from registration record
    fields = registration_record.get('fields', {})
    player_first_name = fields.get('player_first_name', '')
    player_last_name = fields.get('player_last_name', '')
    player_full_name = f"{player_first_name} {player_last_name}".strip()
    team = fields.get('team', '')
    age_group = fields.get('age_group', '')
    preferred_payment_day = fields.get('preferred_payment_day', 15)
    monthly_amount = fields.get('monthly_subscription_amount', 27.5)  # In pounds
    billing_request_id = fields.get('billing_request_id', '')  # Extract billing request ID
    record_id = registration_record.get('id', '')  # Get record ID for updating
    
    # 🎉 SIBLING DISCOUNT LOGIC: Check for existing siblings and apply 10% discount
    try:
        parent_full_name = fields.get('parent_full_name', '')
        if parent_full_name and player_last_name:
            # Initialize Airtable for sibling search
            from pyairtable import Api
            api = Api(os.getenv('AIRTABLE_API_KEY'))
            table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
            
            # Query for existing registrations with same parent name and player surname
            sibling_query = f"AND({{parent_full_name}} = '{parent_full_name}', {{player_last_name}} = '{player_last_name}', {{billing_request_id}} != '{billing_request_id}')"
            existing_siblings = table.all(formula=sibling_query)
            
            if len(existing_siblings) > 0:
                original_amount = monthly_amount
                monthly_amount = monthly_amount * 0.9  # Apply 10% sibling discount
                print(f"🎉 SIBLING DISCOUNT APPLIED: Parent '{parent_full_name}' has {len(existing_siblings)} existing child(ren) with surname '{player_last_name}'")
                print(f"   Original amount: £{original_amount:.2f} → Discounted amount: £{monthly_amount:.2f}")
                
                # Update the database with the discounted amount
                if record_id:
                    try:
                        table.update(record_id, {'monthly_subscription_amount': monthly_amount})
                        print(f"   ✅ Updated database with discounted amount: £{monthly_amount:.2f}")
                    except Exception as update_error:
                        print(f"   ⚠️  Warning: Failed to update database with discounted amount: {update_error}")
            else:
                print(f"ℹ️  NO SIBLING DISCOUNT: This is the first child registered for parent '{parent_full_name}' with surname '{player_last_name}'")
    except Exception as e:
        print(f"⚠️  SIBLING DISCOUNT CHECK FAILED: {str(e)} - Proceeding with original amount")
        # Continue with original amount if sibling check fails
    
    # Convert monthly amount from pounds to pence
    monthly_amount_pence = int(monthly_amount * 100) if monthly_amount else 2750
    
    # Validate extracted data
    if not player_full_name:
        return {
            "success": False,
            "message": "Player name not found in registration record",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": player_full_name,
            "start_date": "",
            "interim_created": False
        }
    
    # Validate payment day
    if preferred_payment_day != -1 and (preferred_payment_day < 1 or preferred_payment_day > 31):
        return {
            "success": False,
            "message": "Invalid preferred payment day in registration record",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": player_full_name,
            "start_date": "",
            "interim_created": False
        }
    
    # Get API key
    if not gocardless_api_key:
        gocardless_api_key = os.getenv("GOCARDLESS_API_KEY")
    
    if not gocardless_api_key:
        return {
            "success": False,
            "message": "GoCardless API key not configured. Subscription activation unavailable.",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": player_full_name,
            "start_date": "",
            "interim_created": False
        }
    
    try:
        # Clean inputs
        player_name_clean = player_full_name.strip()
        team_clean = team.strip() if team else ""
        age_group_clean = age_group.strip() if age_group else ""
        
        # Get mandate details to determine earliest valid start date
        headers = {
            "Authorization": f"Bearer {gocardless_api_key}",
            "Content-Type": "application/json",
            "GoCardless-Version": "2015-07-06"
        }
        
        print(f"🔍 Fetching mandate details for {mandate_id}...")
        mandate_response = requests.get(f"https://api.gocardless.com/mandates/{mandate_id}", 
                                      headers=headers, timeout=30)
        
        if mandate_response.status_code != 200:
            return {
                "success": False,
                "message": f"Failed to fetch mandate details: {mandate_response.status_code} - {mandate_response.text}",
                "ongoing_subscription_id": "",
                "interim_subscription_id": "",
                "subscription_data": {},
                "player_full_name": player_full_name,
                "start_date": "",
                "interim_created": False
            }
        
        mandate_data = mandate_response.json()
        mandate = mandate_data.get('mandates', {})
        next_possible_charge_date = mandate.get('next_possible_charge_date')
        mandate_status = mandate.get('status')
        
        print(f"📋 Mandate status: {mandate_status}")
        print(f"📅 Next possible charge date: {next_possible_charge_date}")
        
        if not next_possible_charge_date:
            return {
                "success": False,
                "message": f"Mandate {mandate_id} has no next_possible_charge_date",
                "ongoing_subscription_id": "",
                "interim_subscription_id": "",
                "subscription_data": {},
                "player_full_name": player_full_name,
                "start_date": "",
                "interim_created": False
            }
        
        # Parse mandate's next possible charge date
        earliest_start_date = datetime.strptime(next_possible_charge_date, "%Y-%m-%d")
        
        # Smart subscription start date calculation
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        # Calculate next occurrence of preferred payment day
        if preferred_payment_day == -1:
            # Last day of current month
            if current_month == 12:
                next_occurrence = datetime(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                next_occurrence = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
        else:
            try:
                # Try preferred day in current month
                next_occurrence = datetime(current_year, current_month, preferred_payment_day)
                if next_occurrence <= today:
                    # Already passed this month, move to next month
                    if current_month == 12:
                        next_occurrence = datetime(current_year + 1, 1, preferred_payment_day)
                    else:
                        next_occurrence = datetime(current_year, current_month + 1, preferred_payment_day)
            except ValueError:
                # Day doesn't exist in current month, try next month
                if current_month == 12:
                    try:
                        next_occurrence = datetime(current_year + 1, 1, preferred_payment_day)
                    except ValueError:
                        # Use last day of January
                        next_occurrence = datetime(current_year + 1, 2, 1) - timedelta(days=1)
                else:
                    try:
                        next_occurrence = datetime(current_year, current_month + 1, preferred_payment_day)
                    except ValueError:
                        # Use last day of next month
                        if current_month + 1 == 12:
                            next_occurrence = datetime(current_year + 1, 1, 1) - timedelta(days=1)
                        else:
                            next_occurrence = datetime(current_year, current_month + 2, 1) - timedelta(days=1)
        
        # Check if next occurrence is too soon (within 5 days - safe buffer)
        days_until_next = (next_occurrence - today).days
        interim_created = False
        interim_subscription_id = ""
        
        # Smart logic: Don't create interim if we're late in month (after 10th) AND payment is soon
        # This prevents unfair full-month charges for partial month usage
        late_in_month = today.day > 10
        payment_too_soon = days_until_next < 5
        
        if payment_too_soon and not late_in_month:
            print(f"⏰ Next payment day ({next_occurrence.strftime('%Y-%m-%d')}) is too soon ({days_until_next} days). Creating interim subscription...")
            
            # Create interim subscription for the interim start month
            interim_start = today + timedelta(days=5)
            interim_start_date = interim_start.strftime("%Y-%m-%d")
            
            # Validate that interim start date is not earlier than mandate's next_possible_charge_date
            if interim_start < earliest_start_date:
                print(f"⚠️  Calculated interim start date ({interim_start_date}) is earlier than mandate's next possible charge date ({next_possible_charge_date})")
                print(f"🔧 Adjusting interim start date to use mandate's next possible charge date: {next_possible_charge_date}")
                interim_start_date = next_possible_charge_date
                interim_start = datetime.strptime(next_possible_charge_date, "%Y-%m-%d")
            else:
                print(f"✅ Calculated interim start date ({interim_start_date}) is valid (on/after {next_possible_charge_date})")
            
            # End date is last day of the interim start month
            interim_month = interim_start.month
            interim_year = interim_start.year
            if interim_month == 12:
                interim_end_date = datetime(interim_year + 1, 1, 1) - timedelta(days=1)
            else:
                interim_end_date = datetime(interim_year, interim_month + 1, 1) - timedelta(days=1)
            interim_end_date_str = interim_end_date.strftime("%Y-%m-%d")
            
            # Create interim subscription payload
            interim_payload = {
                "subscriptions": {
                    "amount": str(monthly_amount_pence),
                    "currency": "GBP",
                    "name": f"Urmston Town Interim Payment - {player_name_clean}",
                    "interval_unit": "monthly",
                    "day_of_month": str(interim_start.day),
                    "start_date": interim_start_date,
                    "end_date": interim_end_date_str,
                    "metadata": {
                        "player_name": player_name_clean,
                        "player_team": team_clean,
                        "subscription_type": "interim"
                    },
                    "links": {
                        "mandate": mandate_id
                    }
                }
            }
            
            # Create interim subscription
            headers = {
                "Authorization": f"Bearer {gocardless_api_key}",
                "Content-Type": "application/json",
                "GoCardless-Version": "2015-07-06"
            }
            
            interim_response = requests.post("https://api.gocardless.com/subscriptions", 
                                           headers=headers, json=interim_payload, timeout=30)
            interim_response.raise_for_status()
            interim_data = interim_response.json()
            interim_subscription_id = interim_data.get("subscriptions", {}).get("id", "")
            interim_created = True
            
            print(f"✅ Interim subscription created: {interim_subscription_id} ({interim_start_date} to {interim_end_date_str})")
            
            # Move ongoing subscription to next month
            if next_occurrence.month == 12:
                ongoing_start = datetime(next_occurrence.year + 1, 1, preferred_payment_day)
            else:
                ongoing_start = datetime(next_occurrence.year, next_occurrence.month + 1, preferred_payment_day)
        elif payment_too_soon and late_in_month:
            # Skip interim due to late month registration - wait for next occurrence to be fair
            print(f"📅 Late month registration (day {today.day}) - skipping interim to avoid unfair partial month charge")
            print(f"⏭️  Will start subscription on next occurrence: {next_occurrence.strftime('%Y-%m-%d')}")
            ongoing_start = next_occurrence
        else:
            # No interim needed, use next occurrence
            ongoing_start = next_occurrence
        
        ongoing_start_date = ongoing_start.strftime("%Y-%m-%d")
        
        # 🏈 SEASON POLICY: No subscription payments until September 2025
        # For registrations before Aug 28, 2025 - force start date to September 2025
        cutoff_date = datetime(2025, 8, 28)  # Aug 28, 2025
        september_policy_applies = today < cutoff_date
        
        if september_policy_applies:
            # Force subscription to start in September 2025 on preferred payment day
            try:
                september_start = datetime(2025, 9, preferred_payment_day)
                print(f"🏈 Season policy: Registration before Aug 28 - forcing start date to September 2025")
                print(f"   Original calculated start: {ongoing_start_date}")
                print(f"   September policy start: {september_start.strftime('%Y-%m-%d')}")
                ongoing_start = september_start
                ongoing_start_date = september_start.strftime("%Y-%m-%d")
                
                # Disable interim subscription for early registrations (they wait until September)
                if interim_created:
                    print(f"🚫 Disabling interim subscription due to September policy - all payments start in September")
                    interim_created = False
                    interim_subscription_id = ""
                
            except ValueError:
                # Handle case where preferred_payment_day doesn't exist in September
                if preferred_payment_day == -1:
                    # Last day of September
                    september_start = datetime(2025, 10, 1) - timedelta(days=1)
                else:
                    # Use last day of September if preferred day doesn't exist
                    september_start = datetime(2025, 10, 1) - timedelta(days=1)
                
                print(f"🏈 Season policy: Preferred day {preferred_payment_day} doesn't exist in September, using {september_start.strftime('%Y-%m-%d')}")
                ongoing_start = september_start
                ongoing_start_date = september_start.strftime("%Y-%m-%d")
                
                if interim_created:
                    print(f"🚫 Disabling interim subscription due to September policy")
                    interim_created = False
                    interim_subscription_id = ""
        else:
            print(f"📅 Registration after Aug 28 - using existing smart logic (start: {ongoing_start_date})")
        
        # Validate that our calculated ongoing start date is not earlier than mandate's next_possible_charge_date
        if ongoing_start < earliest_start_date:
            print(f"⚠️  Calculated ongoing start date ({ongoing_start_date}) is earlier than mandate's next possible charge date ({next_possible_charge_date})")
            print(f"🔧 Adjusting ongoing start date to use mandate's next possible charge date: {next_possible_charge_date}")
            ongoing_start_date = next_possible_charge_date
        else:
            print(f"✅ Calculated ongoing start date ({ongoing_start_date}) is valid (on/after {next_possible_charge_date})")
        
        # Create main ongoing subscription
        ongoing_payload = {
            "subscriptions": {
                "amount": str(monthly_amount_pence),
                "currency": "GBP",
                "name": "Urmston Town Monthly Subs 24-25",
                "interval_unit": "monthly",
                "day_of_month": str(preferred_payment_day) if preferred_payment_day != -1 else "-1",
                "start_date": ongoing_start_date,
                "end_date": "2026-06-01",  # End of season (updated to match test subscription)
                "metadata": {
                    "player_name": player_name_clean,
                    "player_team": team_clean,
                    "subscription_type": "ongoing"
                },
                "links": {
                    "mandate": mandate_id
                }
            }
        }
        
        # Create ongoing subscription
        headers = {
            "Authorization": f"Bearer {gocardless_api_key}",
            "Content-Type": "application/json",
            "GoCardless-Version": "2015-07-06"
        }
        
        print(f"🔄 Creating subscription with payload: {ongoing_payload}")
        ongoing_response = requests.post("https://api.gocardless.com/subscriptions", 
                                       headers=headers, json=ongoing_payload, timeout=30)
        print(f"📡 GoCardless response status: {ongoing_response.status_code}")
        print(f"📡 GoCardless response body: {ongoing_response.text}")
        
        if ongoing_response.status_code != 201:
            error_detail = ongoing_response.text
            try:
                error_json = ongoing_response.json()
                if 'error' in error_json:
                    error_detail = f"{error_json['error'].get('type', 'unknown')}: {error_json['error'].get('message', 'unknown error')}"
                    if 'errors' in error_json['error']:
                        for err in error_json['error']['errors']:
                            error_detail += f" | {err.get('field', 'unknown')}: {err.get('message', 'unknown error')}"
            except:
                pass
            
            return {
                "success": False,
                "message": f"GoCardless subscription creation failed: {error_detail}",
                "ongoing_subscription_id": "",
                "interim_subscription_id": "",
                "subscription_data": {},
                "player_full_name": player_full_name,
                "start_date": ongoing_start_date,
                "interim_created": False
            }
        
        ongoing_data = ongoing_response.json()
        ongoing_subscription_id = ongoing_data.get("subscriptions", {}).get("id", "")
        
        if not ongoing_subscription_id:
            return {
                "success": False,
                "message": "GoCardless ongoing subscription created but no ID returned",
                "ongoing_subscription_id": "",
                "interim_subscription_id": interim_subscription_id,
                "subscription_data": ongoing_data,
                "player_full_name": player_full_name,
                "start_date": ongoing_start_date,
                "interim_created": interim_created
            }
        
        success_message = f"Subscription activated successfully for {player_name_clean} (starts {ongoing_start_date})"
        if interim_created:
            success_message += f" with interim payment from {interim_start_date}"
        
        return {
            "success": True,
            "message": success_message,
            "ongoing_subscription_id": ongoing_subscription_id,
            "interim_subscription_id": interim_subscription_id,
            "subscription_data": ongoing_data,
            "player_full_name": player_full_name,
            "start_date": ongoing_start_date,
            "interim_created": interim_created
        }
        
    except requests.RequestException as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_detail += f" | Status: {e.response.status_code} | Body: {e.response.text}"
        
        return {
            "success": False,
            "message": f"GoCardless API request failed: {error_detail}",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": player_full_name,
            "start_date": "",
            "interim_created": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Subscription activation error: {str(e)}",
            "ongoing_subscription_id": "",
            "interim_subscription_id": "",
            "subscription_data": {},
            "player_full_name": player_full_name,
            "start_date": "",
            "interim_created": False
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