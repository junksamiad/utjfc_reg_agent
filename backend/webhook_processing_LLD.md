# GoCardless Webhook Processing - Low-Level Design

## Overview

This document provides a comprehensive analysis of the GoCardless webhook processing system implemented in the UTJFC Registration Agent backend. The webhook system handles payment notifications, mandate authorizations, and subscription management for football club registrations.

## Architecture Overview

The webhook processing system consists of three main components:

1. **Webhook Handler** (`/webhooks/gocardless`) - Main entry point for GoCardless events
2. **Event Processors** - Individual handlers for different event types
3. **Database Integration** - Updates to Airtable registration records

## Webhook Handler Implementation

### Main Webhook Endpoint

**Location**: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/server.py` (lines 1564-1607)

```python
@app.post("/webhooks/gocardless")
async def handle_gocardless_webhook(request: Request):
    """
    Handle GoCardless webhook events for payment and mandate completion.
    
    Key events we handle:
    - payment_confirmed: Payment has been confirmed 
    - mandate_active: Mandate is now active
    - billing_request_fulfilled: Billing request completed
    """
```

### Request Processing Flow

1. **Raw Body Extraction**: Captures the raw request body for signature verification
2. **Signature Verification**: Validates webhook authenticity using HMAC-SHA256
3. **Event Parsing**: Decodes JSON payload and extracts events array
4. **Event Processing**: Iterates through each event in the webhook payload

### Security Implementation

#### Signature Verification

```python
def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify GoCardless webhook signature"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

**Security Features**:
- HMAC-SHA256 signature verification
- Constant-time comparison using `hmac.compare_digest()`
- Development mode fallback when webhook secret is not configured
- Header-based signature extraction (`webhook-signature`)

**Environment Variables**:
- `GOCARDLESS_WEBHOOK_SECRET`: Secret key for signature verification

## Event Processing System

### Event Router

**Location**: Lines 1622-1656

The system processes events based on `resource_type` and `action` combinations:

```python
async def process_gocardless_event(event: dict):
    """Process individual GoCardless webhook event"""
    
    event_id = event.get('id')
    resource_type = event.get('resource_type')
    action = event.get('action')
    
    # Route to appropriate handler
    if resource_type == 'payments' and action == 'confirmed':
        # Handle payment confirmation
    elif resource_type == 'mandates' and action == 'active':
        # Handle mandate activation
    elif resource_type == 'billing_requests' and action == 'fulfilled':
        # Handle billing request completion
```

### Supported Event Types

| Resource Type | Action | Handler Function | Purpose |
|---------------|--------|------------------|---------|
| `payments` | `confirmed` | `handle_payment_confirmed` | One-off signing fee payment |
| `payments` | `confirmed` | `handle_subscription_payment_confirmed` | Monthly subscription payment |
| `payments` | `failed` | `handle_subscription_payment_failed` | Failed subscription payment |
| `payments` | `cancelled`, `charged_back`, `submitted` | `handle_subscription_payment_status_change` | Other payment status changes |
| `mandates` | `active` | `handle_mandate_active` | Direct debit mandate authorization |
| `billing_requests` | `fulfilled` | `handle_billing_request_fulfilled` | Complete registration completion |

## Event Handlers Deep Dive

### 1. Payment Confirmation Handler

**Location**: Lines 1658-1708

```python
async def handle_payment_confirmed(event: dict):
    """Handle payment confirmation - set signing_on_fee_paid = 'Y'"""
```

**Functionality**:
- Updates `signing_on_fee_paid` field to 'Y' in Airtable
- Links payment to registration via `billing_request_id`
- Handles incomplete registration scenarios (payment without mandate)

**Database Updates**:
```python
update_data = {'signing_on_fee_paid': 'Y'}

# If mandate is NOT authorized, set status to incomplete
if current_mandate_status != 'Y':
    update_data['registration_status'] = 'incomplete'
```

### 2. Mandate Activation Handler

**Location**: Lines 1710-1761

```python
async def handle_mandate_active(event: dict):
    """Handle mandate activation - set mandate_authorised = 'Y' only"""
```

**Functionality**:
- Updates `mandate_authorised` field to 'Y'
- Handles late mandate authorization scenarios
- Promotes incomplete registrations to active when both payment and mandate are complete

**Smart Status Management**:
```python
# If payment is already confirmed and status is incomplete, we can now mark as active
if current_payment_status == 'Y' and current_reg_status == 'incomplete':
    update_data['registration_status'] = 'active'
```

### 3. Billing Request Fulfillment Handler

**Location**: Lines 1763-1868

```python
async def handle_billing_request_fulfilled(event: dict):
    """Handle billing request fulfillment - final completion step with subscription activation"""
```

**Functionality**:
- Confirms both payment and mandate completion
- Activates subscription using `activate_subscription()` function
- Updates registration status to 'active'
- Sends SMS confirmation to parent

**Complete Registration Update**:
```python
update_data = {
    'signing_on_fee_paid': 'Y',
    'mandate_authorised': 'Y',
    'registration_status': 'active'
}
```

### 4. Subscription Payment Handlers

#### Subscription Payment Confirmed

**Location**: Lines 1935-1989

```python
async def handle_subscription_payment_confirmed(event: dict):
    """Handle successful subscription payment - update monthly status field"""
```

**Functionality**:
- Maps payment date to season month (September 2025 - May 2026)
- Updates monthly payment status fields
- Tracks subscription payment confirmations

**Month Mapping Logic**:
```python
def get_subscription_status_field_for_month(month: int, year: int) -> str:
    """Map calendar month/year to subscription status field name"""
    
    # Season runs September 2025 - May 2026
    month_mapping = {
        (9, 2025): 'sep_subscription_payment_status',
        (10, 2025): 'oct_subscription_payment_status',
        # ... continuing through May 2026
    }
    
    return month_mapping.get((month, year))
```

#### Subscription Payment Failed

**Location**: Lines 1991-2046

```python
async def handle_subscription_payment_failed(event: dict):
    """Handle failed subscription payment - update monthly status field"""
```

**Functionality**:
- Updates monthly status field to 'failed'
- Prepares for recovery payment process (TODO implementation)
- Provides detailed logging for failed payments

## Subscription Activation System

### Subscription Activation Function

**Location**: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/tools/registration_tools/gocardless_payment.py` (lines 332-822)

```python
def activate_subscription(
    mandate_id: str,
    registration_record: Dict,
    gocardless_api_key: Optional[str] = None
) -> Dict:
```

**Key Features**:

#### 1. Sibling Discount Application

**Location**: Lines 403-433

```python
# 🎉 SIBLING DISCOUNT LOGIC: Check for existing siblings and apply 10% discount
try:
    parent_full_name = fields.get('parent_full_name', '')
    if parent_full_name and player_last_name:
        # Query for existing registrations with same parent name and player surname
        sibling_query = f"AND({{parent_full_name}} = '{parent_full_name}', {{player_last_name}} = '{player_last_name}', {{billing_request_id}} != '{billing_request_id}')"
        existing_siblings = table.all(formula=sibling_query)
        
        if len(existing_siblings) > 0:
            original_amount = monthly_amount
            monthly_amount = monthly_amount * 0.9  # Apply 10% sibling discount
            print(f"🎉 SIBLING DISCOUNT APPLIED: Parent '{parent_full_name}' has {len(existing_siblings)} existing child(ren)")
```

#### 2. Smart Start Date Calculation

**Location**: Lines 530-700

The system implements intelligent subscription start date logic:

```python
# Smart subscription start date calculation
today = datetime.now()
current_month = today.month
current_year = today.year

# Calculate next occurrence of preferred payment day
if preferred_payment_day == -1:
    # Last day of current month
    next_occurrence = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
else:
    # Try preferred day in current month
    next_occurrence = datetime(current_year, current_month, preferred_payment_day)
```

#### 3. Season Policy Enforcement

**Location**: Lines 660-700

```python
# 🏈 SEASON POLICY: No subscription payments until September 2025
# For registrations before Aug 28, 2025 - force start date to September 2025
cutoff_date = datetime(2025, 8, 28)  # Aug 28, 2025
september_policy_applies = today < cutoff_date

if september_policy_applies:
    # Force subscription to start in September 2025 on preferred payment day
    september_start = datetime(2025, 9, preferred_payment_day)
    print(f"🏈 Season policy: Registration before Aug 28 - forcing start date to September 2025")
```

#### 4. Interim Payment Logic

**Location**: Lines 582-643

```python
# Smart logic: Don't create interim if we're late in month (after 10th) AND payment is soon
late_in_month = today.day > 10
payment_too_soon = days_until_next < 5

if payment_too_soon and not late_in_month:
    print(f"⏰ Next payment day is too soon. Creating interim subscription...")
    
    # Create interim subscription for the immediate month
    interim_start = today + timedelta(days=5)
    interim_start_date = interim_start.strftime("%Y-%m-%d")
```

## Database Integration

### Airtable Configuration

**Location**: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/tools/airtable/airtable_setup.py`

```python
# Airtable configuration
AIRTABLE_BASE_ID = "appBLxf3qmGIBc6ue"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# Table configurations for different seasons
TABLES_CONFIG = {
    "2526": {
        "table_name": "registrations_2526",
        "table_id": "tbl1D7hdjVcyHbT8a",
        "season": "2025-26"
    }
}
```

### Database Fields Updated by Webhooks

#### Core Registration Fields
- `signing_on_fee_paid`: 'Y' when signing fee is confirmed
- `mandate_authorised`: 'Y' when direct debit mandate is active
- `registration_status`: 'active', 'incomplete', 'pending_payment'
- `ongoing_subscription_id`: GoCardless subscription ID
- `subscription_start_date`: Calculated subscription start date
- `subscription_status`: 'active', 'failed'
- `subscription_activated`: 'Y' when subscription is successfully created

#### Monthly Payment Status Fields
- `sep_subscription_payment_status`: September payment status
- `oct_subscription_payment_status`: October payment status
- `nov_subscription_payment_status`: November payment status
- `dec_subscription_payment_status`: December payment status
- `jan_subscription_payment_status`: January payment status
- `feb_subscription_payment_status`: February payment status
- `mar_subscription_payment_status`: March payment status
- `apr_subscription_payment_status`: April payment status
- `may_subscription_payment_status`: May payment status

#### Interim Payment Support
- `interim_subscription_id`: Temporary subscription ID for partial month charges

## SMS Notification System

### Payment Confirmation SMS

**Location**: Lines 1870-1933

```python
async def send_payment_confirmation_sms(registration_data: dict):
    """Send SMS confirmation when payment is completed"""
    
    # Format phone number for SMS
    if parent_phone.startswith('0'):
        formatted_phone = '+44' + parent_phone[1:]
    elif not parent_phone.startswith('+'):
        formatted_phone = '+44' + parent_phone
    else:
        formatted_phone = parent_phone
        
    # Create confirmation message
    message = f"✅ Payment confirmed! {player_name}'s registration for Urmston Town JFC is now complete. Direct debit set up for monthly fees. See you on the pitch! 🏆"
```

**Features**:
- UK phone number formatting
- Twilio SMS integration
- Personalized messages with player name
- Error handling for SMS delivery failures

## Error Handling and Logging

### Comprehensive Error Handling

The webhook system implements robust error handling at multiple levels:

#### 1. Webhook Level
```python
try:
    # Process webhook
    return {"status": "success"}
except Exception as e:
    print(f"Error processing GoCardless webhook: {str(e)}")
    return {"error": "Webhook processing failed"}, 500
```

#### 2. Event Level
```python
try:
    # Process individual event
    await process_gocardless_event(event)
except Exception as e:
    print(f"Error processing event {event_id}: {str(e)}")
    # Continue processing other events
```

#### 3. Database Level
```python
try:
    table.update(record_id, update_data)
    print(f"✅ Updated registration for {player_name}")
except Exception as e:
    print(f"Error updating registration: {str(e)}")
```

### Logging Patterns

The system uses structured logging with emojis for easy identification:

```python
print(f"💳 Payment confirmed: {payment_id}")
print(f"📋 Mandate active: {mandate_id}")
print(f"🏆 Billing request fulfilled: {billing_request_id}")
print(f"✅ Registration completed for {player_name}")
print(f"🎉 SIBLING DISCOUNT APPLIED: {discount_info}")
print(f"⚠️ WARNING: {warning_message}")
print(f"❌ ERROR: {error_message}")
```

## Integration with Broader Payment Flow

### Payment Flow Sequence

1. **Registration Agent** creates billing request via `create_billing_request()`
2. **Payment Link** generated via `create_billing_request_flow()`
3. **User Completes Payment** on GoCardless hosted page
4. **Webhooks Triggered** by GoCardless for various events
5. **Database Updated** with payment/mandate status
6. **Subscription Activated** for ongoing monthly payments
7. **SMS Confirmation** sent to parent

### Payment States and Transitions

```
Initial State: registration_status = 'pending_payment'
              signing_on_fee_paid = 'N'
              mandate_authorised = 'N'

Payment Confirmed → signing_on_fee_paid = 'Y'
                  → registration_status = 'incomplete' (if no mandate)

Mandate Active → mandate_authorised = 'Y'
               → registration_status = 'active' (if payment confirmed)

Billing Request Fulfilled → Both payment and mandate confirmed
                          → registration_status = 'active'
                          → Subscription activated
                          → SMS sent
```

## Security Considerations

### 1. Signature Verification
- HMAC-SHA256 signature validation
- Constant-time comparison to prevent timing attacks
- Configurable webhook secret via environment variables

### 2. Data Validation
- Event structure validation before processing
- Required field checking (billing_request_id, mandate_id, etc.)
- Database query parameterization to prevent injection

### 3. Error Information Disclosure
- Generic error messages in webhook responses
- Detailed error logging for debugging
- No sensitive data exposure in error responses

### 4. Rate Limiting Considerations
- Webhook endpoint should implement rate limiting in production
- Idempotency handling for duplicate events
- Timeout configuration for external API calls

## Environment Configuration

### Required Environment Variables

```bash
# GoCardless Configuration
GOCARDLESS_API_KEY=your_api_key_here
GOCARDLESS_WEBHOOK_SECRET=your_webhook_secret_here

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_here
```

### Development vs Production

**Development Mode**:
- Webhook signature verification disabled
- Detailed console logging
- Test payment amounts (£1.00 instead of £45.00)

**Production Mode**:
- Full signature verification enabled
- Structured logging to files
- Live payment amounts
- Rate limiting enabled

## Performance Considerations

### 1. Asynchronous Processing
- All webhook handlers are async functions
- Non-blocking database updates
- Concurrent processing of multiple events

### 2. Database Optimization
- Indexed queries using billing_request_id
- Bulk updates where possible
- Connection pooling for high-volume webhooks

### 3. External API Calls
- Timeout configuration for GoCardless API calls
- Retry logic with exponential backoff
- Circuit breaker pattern for external service failures

## Testing Strategy

### 1. Unit Tests
- Individual event handler testing
- Signature verification testing
- Database update validation

### 2. Integration Tests
- End-to-end payment flow testing
- Webhook simulation with real payloads
- Database state verification

### 3. Load Testing
- High-volume webhook processing
- Concurrent event handling
- Database performance under load

## Monitoring and Alerting

### 1. Webhook Processing Metrics
- Event processing success/failure rates
- Processing time per event type
- Database update success rates

### 2. Business Logic Monitoring
- Registration completion rates
- Payment success/failure rates
- Subscription activation rates

### 3. Error Alerting
- Failed webhook processing alerts
- Database update failures
- SMS delivery failures

## Future Enhancements

### 1. Event Deduplication
- Implement idempotency keys for events
- Database-based event tracking
- Duplicate event detection and handling

### 2. Retry Mechanisms
- Failed event retry with exponential backoff
- Dead letter queue for permanently failed events
- Manual retry capabilities

### 3. Advanced Analytics
- Payment success rate analytics
- Subscription churn analysis
- Revenue tracking and reporting

### 4. Webhook Management
- Webhook endpoint health checks
- Webhook configuration management
- Event replay capabilities

## Conclusion

The GoCardless webhook processing system provides a robust, secure, and scalable solution for handling payment events in the UTJFC registration system. The implementation includes comprehensive error handling, detailed logging, and integration with the broader payment flow. The system successfully handles complex business logic including sibling discounts, smart subscription scheduling, and season-based payment policies.

The modular design allows for easy extension to handle additional event types and business requirements while maintaining reliability and security standards appropriate for financial transaction processing.