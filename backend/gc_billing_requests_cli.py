#!/usr/bin/env python3
"""
GoCardless Billing Requests Interactive CLI Tool

Interactive CLI to browse GoCardless billing requests.
- Shows numbered list of billing requests with basic info
- Select a number to view detailed information
- Press 'b' to go back to list, 'q' to quit

Run from terminal: python gc_billing_requests_cli.py

Requirements:
- GOCARDLESS_API_KEY environment variable
- gocardless-pro library (pip install gocardless-pro)
"""

import os
import sys
from datetime import datetime
from typing import List, Any

try:
    import gocardless_pro
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing required library: {e}")
    print("Install with: pip install gocardless-pro python-dotenv")
    sys.exit(1)

def setup_gocardless_client():
    """Initialize GoCardless client with API token"""
    
    # Load environment variables
    load_dotenv()
    
    access_token = os.getenv('GOCARDLESS_API_KEY')
    if not access_token:
        print("❌ Error: GOCARDLESS_API_KEY not found in environment variables")
        print("Set it with: export GOCARDLESS_API_KEY=your_token_here")
        return None
    
    # Check if we're in sandbox or live mode
    environment = 'sandbox' if 'sandbox' in access_token else 'live'
    
    try:
        client = gocardless_pro.Client(
            access_token=access_token,
            environment=environment
        )
        print(f"✅ Connected to GoCardless ({environment} mode)")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to GoCardless: {e}")
        return None

def format_datetime(iso_string: str) -> str:
    """Format ISO datetime string to readable format"""
    if not iso_string:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string

def format_currency(amount_pence: int, currency: str = "GBP") -> str:
    """Format pence amount to currency string"""
    if amount_pence is None:
        return "N/A"
    
    amount = amount_pence / 100
    currency_symbols = {"GBP": "£", "EUR": "€", "USD": "$"}
    symbol = currency_symbols.get(currency, currency)
    
    return f"{symbol}{amount:.2f}"

def get_player_name_from_payment_request(br) -> str:
    """Extract player name from payment request description"""
    payment_request = getattr(br, 'payment_request', None)
    if payment_request:
        description = getattr(payment_request, 'description', '')
        if description and ' - ' in description:
            # Extract name from "UTJFC Signing-on Fee - Player Name" format
            return description.split(' - ')[-1]
    return "N/A"

def get_metadata_summary(br) -> str:
    """Get a summary of metadata fields"""
    metadata = getattr(br, 'metadata', None)
    if not metadata:
        return "None"
    
    metadata_items = []
    for attr in dir(metadata):
        if not attr.startswith('_'):
            value = getattr(metadata, attr, None)
            if value and not callable(value):
                metadata_items.append(f"{attr}={value}")
    
    return ", ".join(metadata_items) if metadata_items else "None"

def show_billing_requests_list(billing_requests: List[Any]):
    """Display the numbered list of billing requests"""
    
    print("\n" + "="*80)
    print("🏦 GOCARDLESS BILLING REQUESTS")
    print("="*80)
    print(f"{'#':<3} {'ID':<18} {'Created':<17} {'Status':<12} {'Player':<20} {'Metadata'}")
    print("-"*80)
    
    for index, br in enumerate(billing_requests, 1):
        br_id = getattr(br, 'id', 'N/A')
        created = format_datetime(getattr(br, 'created_at', None))
        status = getattr(br, 'status', 'N/A').upper()
        player_name = get_player_name_from_payment_request(br)
        metadata = get_metadata_summary(br)
        
        # Truncate long fields for display
        player_display = player_name[:19] + "..." if len(player_name) > 22 else player_name
        metadata_display = metadata[:30] + "..." if len(metadata) > 33 else metadata
        
        print(f"{index:<3} {br_id:<18} {created:<17} {status:<12} {player_display:<20} {metadata_display}")
    
    print("-"*80)
    print(f"Total: {len(billing_requests)} billing requests")

def show_detailed_view(br, index: int):
    """Show detailed information for a specific billing request"""
    
    print(f"\n{'='*80}")
    print(f"📋 BILLING REQUEST #{index} - DETAILED VIEW")
    print(f"{'='*80}")
    
    # Basic info
    print(f"🆔 ID: {getattr(br, 'id', 'N/A')}")
    print(f"📅 Created: {format_datetime(getattr(br, 'created_at', None))}")
    print(f"🔄 Status: {getattr(br, 'status', 'N/A').upper()}")
    
    # Purpose
    purpose = getattr(br, 'purpose_code', 'N/A')
    print(f"🎯 Purpose: {purpose}")
    
    # Mandate request details
    mandate_request = getattr(br, 'mandate_request', None)
    if mandate_request:
        print(f"\n💳 MANDATE REQUEST:")
        print(f"   Scheme: {getattr(mandate_request, 'scheme', 'N/A')}")
        print(f"   Currency: {getattr(mandate_request, 'currency', 'N/A')}")
        verify = getattr(mandate_request, 'verify', None)
        if verify:
            verify_amount = getattr(verify, 'amount', 0)
            verify_currency = getattr(verify, 'currency', 'GBP')
            print(f"   Verify: {verify_currency} {format_currency(verify_amount, verify_currency)}")
    
    # Payment request details
    payment_request = getattr(br, 'payment_request', None)
    if payment_request:
        print(f"\n💰 PAYMENT REQUEST:")
        amount = getattr(payment_request, 'amount', None)
        currency = getattr(payment_request, 'currency', 'GBP')
        print(f"   Amount: {format_currency(amount, currency)}")
        print(f"   Description: {getattr(payment_request, 'description', 'N/A')}")
        print(f"   Reference: {getattr(payment_request, 'reference', 'N/A')}")
    
    # Subscription request details
    subscription_request = getattr(br, 'subscription_request', None)
    if subscription_request:
        print(f"\n🔁 SUBSCRIPTION REQUEST:")
        amount = getattr(subscription_request, 'amount', None)
        currency = getattr(subscription_request, 'currency', 'GBP')
        print(f"   Amount: {format_currency(amount, currency)}")
        print(f"   Name: {getattr(subscription_request, 'name', 'N/A')}")
        print(f"   Interval: {getattr(subscription_request, 'interval', 'N/A')}")
        print(f"   Interval Unit: {getattr(subscription_request, 'interval_unit', 'N/A')}")
        print(f"   Day of Month: {getattr(subscription_request, 'day_of_month', 'N/A')}")
    
    # Customer details
    customer_details = getattr(br, 'customer_details', None)
    if customer_details:
        print(f"\n👤 CUSTOMER DETAILS:")
        given_name = getattr(customer_details, 'given_name', '')
        family_name = getattr(customer_details, 'family_name', '')
        print(f"   Name: {given_name} {family_name}")
        print(f"   Email: {getattr(customer_details, 'email', 'N/A')}")
        print(f"   Phone: {getattr(customer_details, 'phone_number', 'N/A')}")
        print(f"   Company: {getattr(customer_details, 'company_name', 'N/A')}")
        
        # Address
        address_parts = []
        if getattr(customer_details, 'address_line1', None):
            address_parts.append(customer_details.address_line1)
        if getattr(customer_details, 'address_line2', None):
            address_parts.append(customer_details.address_line2)
        if getattr(customer_details, 'city', None):
            address_parts.append(customer_details.city)
        if getattr(customer_details, 'postal_code', None):
            address_parts.append(customer_details.postal_code)
        if getattr(customer_details, 'country_code', None):
            address_parts.append(customer_details.country_code)
        
        if address_parts:
            print(f"   Address: {', '.join(address_parts)}")
    
    # Resources (created items)
    resources = getattr(br, 'resources', None)
    if resources:
        print(f"\n🔗 CREATED RESOURCES:")
        for attr_name in ['customer', 'customer_bank_account', 'mandate', 'payment', 'subscription']:
            resource_id = getattr(resources, attr_name, None)
            if resource_id:
                print(f"   {attr_name.replace('_', ' ').title()}: {resource_id}")
    
    # Links (relationships)
    links = getattr(br, 'links', None)
    if links:
        print(f"\n🔗 LINKS:")
        link_items = []
        for attr in dir(links):
            if not attr.startswith('_'):
                value = getattr(links, attr, None)
                if value and not callable(value):
                    link_items.append(f"   {attr.replace('_', ' ').title()}: {value}")
        
        for item in sorted(link_items):
            print(item)
    
    # Metadata
    metadata = getattr(br, 'metadata', None)
    if metadata:
        print(f"\n📊 METADATA:")
        metadata_items = []
        for attr in dir(metadata):
            if not attr.startswith('_'):
                value = getattr(metadata, attr, None)
                if value and not callable(value):
                    metadata_items.append(f"   {attr}: {value}")
        
        if metadata_items:
            for item in sorted(metadata_items):
                print(item)
        else:
            print("   None")
    else:
        print(f"\n📊 METADATA: None")

def get_user_selection(max_number: int) -> str:
    """Get user input for selection"""
    print(f"\n💡 Enter a number (1-{max_number}) to view details, or 'q' to quit: ", end='')
    return input().strip().lower()

def get_detail_command() -> str:
    """Get user input in detail view"""
    print(f"\n💡 Press 'b' to go back to list, 'q' to quit: ", end='')
    return input().strip().lower()

def get_recent_billing_requests(client, limit: int = 20) -> List[Any]:
    """Fetch recent billing requests from GoCardless"""
    
    try:
        print(f"🔍 Fetching last {limit} billing requests...")
        
        # Get billing requests (sorted by created_at desc by default)
        billing_requests = client.billing_requests.list(
            params={
                "limit": limit
            }
        ).records
        
        if not billing_requests:
            print("📭 No billing requests found")
            return []
        
        print(f"✅ Found {len(billing_requests)} billing request(s)")
        return billing_requests
        
    except Exception as e:
        print(f"❌ Error fetching billing requests: {e}")
        return []

def main():
    """Main interactive CLI function"""
    
    print("🏦 GoCardless Billing Requests Interactive CLI")
    print("=" * 50)
    
    # Setup client
    client = setup_gocardless_client()
    if not client:
        return 1
    
    # Get recent billing requests
    billing_requests = get_recent_billing_requests(client, limit=20)
    
    if not billing_requests:
        return 1
    
    # Main interactive loop
    while True:
        # Show the list
        show_billing_requests_list(billing_requests)
        
        # Get user selection
        selection = get_user_selection(len(billing_requests))
        
        if selection == 'q':
            print("\n👋 Goodbye!")
            break
        
        # Try to parse as number
        try:
            record_num = int(selection)
            if 1 <= record_num <= len(billing_requests):
                # Show detailed view
                selected_br = billing_requests[record_num - 1]
                
                while True:
                    show_detailed_view(selected_br, record_num)
                    
                    # Get command in detail view
                    command = get_detail_command()
                    
                    if command == 'b':
                        break  # Go back to list
                    elif command == 'q':
                        print("\n👋 Goodbye!")
                        return 0
                    else:
                        print("❌ Invalid command. Use 'b' to go back or 'q' to quit.")
            else:
                print(f"❌ Please enter a number between 1 and {len(billing_requests)}")
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 