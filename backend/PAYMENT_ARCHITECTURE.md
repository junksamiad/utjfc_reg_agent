# UTJFC Payment Architecture

## Overview
Decoupled payment system that separates registration completion from payment processing, providing flexible payment timing while maintaining automated tracking and follow-up.

## Core Architecture

### **Registration → Payment Flow**
```
Registration Complete (Routine 29)
↓
Create GC Billing Request (persistent)
↓
Generate secure payment token
↓
Send SMS payment link
↓
User pays when convenient
↓
Webhooks update payment status
↓
Automated follow-up & suspension logic
```

## Database Schema

### **Main Registration Table: `registrations_2526`**
```sql
-- Existing registration fields +
billing_request_id VARCHAR(255),           -- GoCardless billing request ID
payment_token VARCHAR(255) UNIQUE,         -- Secure payment link token
signing_on_fee_paid BOOLEAN DEFAULT FALSE, -- £45 one-off payment status
mandate_authorised BOOLEAN DEFAULT FALSE,  -- Direct Debit setup status  
subscription_activated BOOLEAN DEFAULT FALSE, -- Monthly subscription status
payment_link_sent_at TIMESTAMP,            -- When SMS was sent
created_date TIMESTAMP DEFAULT NOW(),      -- Registration completion date
status ENUM('ACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE'
```

### **Suspended Registrations Table: `suspended_registrations`**
```sql
-- Identical schema to registrations_2526
-- Records moved here after 7 days non-payment
-- Can be restored if late payment received
```

## Payment Flow Implementation

### **Step 1: Registration Completion (Routine 29)**
```python
def complete_registration(registration_data, preferred_payment_day):
    # 1. Save registration to registrations_2526
    registration_id = save_registration(registration_data)
    
    # 2. Create GoCardless billing request
    billing_request = create_billing_request({
        'amount': 4500,  # £45 signing-on fee
        'currency': 'GBP',
        'mandate': {
            'scheme': 'bacs',
            'interval_unit': 'monthly',
            'amount': 2750,  # £27.50 monthly
            'day_of_month': preferred_payment_day
        },
        'metadata': {
            'registration_id': registration_id,
            'player_name': registration_data['child_name'],
            'parent_name': registration_data['parent_name'],
            'team': registration_data['team'],
            'age_group': registration_data['age_group']
        }
    })
    
    # 3. Generate secure payment token
    payment_token = generate_uuid()
    
    # 4. Update registration record
    update_registration(registration_id, {
        'billing_request_id': billing_request.id,
        'payment_token': payment_token,
        'payment_link_sent_at': datetime.now()
    })
    
    # 5. Send SMS payment link
    payment_link = f"https://utjfc.com/pay/{payment_token}"
    send_sms(registration_data['parent_phone'], 
        f"Registration complete for {registration_data['child_name']}! "
        f"Pay when convenient: {payment_link} "
        f"Registration not complete until payment made.")
    
    return {
        'success': True,
        'message': 'Payment link sent via SMS. Pay when convenient.',
        'payment_token': payment_token
    }
```

### **Step 2: Payment Link Handler**
```python
def handle_payment_link(payment_token):
    # 1. Lookup registration by token
    registration = get_registration_by_token(payment_token)
    if not registration:
        return error_page("Invalid or expired payment link")
    
    # 2. Check if already paid
    if registration.signing_on_fee_paid and registration.mandate_authorised:
        return success_page("Payment already completed")
    
    # 3. Create fresh GoCardless auth URL
    auth_url = create_auth_url(registration.billing_request_id)
    
    # 4. Redirect to GoCardless
    return redirect(auth_url)
```

## Webhook Processing

### **GoCardless SDK Webhook Handler**
```python
def process_webhook(webhook_payload, signature):
    # 1. Verify webhook signature using GC SDK
    if not verify_webhook_signature(webhook_payload, signature):
        return 401
    
    # 2. Parse events using GC SDK
    events = parse_webhook_events(webhook_payload)
    
    for event in events:
        if event.resource_type == 'payments':
            handle_payment_event(event)
        elif event.resource_type == 'mandates':
            handle_mandate_event(event)
        elif event.resource_type == 'subscriptions':
            handle_subscription_event(event)
    
    return 200

def handle_payment_event(event):
    if event.action == 'confirmed':
        # Payment successful
        registration = find_registration_by_billing_request(event.metadata.registration_id)
        if registration:
            update_payment_status(registration.id, 'signing_on_fee_paid', True)
        else:
            # Check suspended registrations table
            check_and_restore_suspended_registration(event.metadata.registration_id)

def handle_mandate_event(event):
    if event.action == 'active':
        # Mandate authorised
        registration = find_registration_by_billing_request(event.metadata.registration_id)
        if registration:
            update_payment_status(registration.id, 'mandate_authorised', True)
            # Activate subscription
            activate_subscription(registration.billing_request_id)

def handle_subscription_event(event):
    if event.action == 'active':
        # Subscription activated
        registration = find_registration_by_billing_request(event.metadata.registration_id)
        if registration:
            update_payment_status(registration.id, 'subscription_activated', True)
```

## Automated Follow-up System

### **Daily Cron Job: Payment Chasing**
```python
def daily_payment_chase():
    """Run daily to chase non-payments and suspend overdue registrations"""
    
    # Day 3 chase
    day_3_registrations = get_registrations_where(
        created_date=3.days.ago(),
        status='ACTIVE',
        payment_incomplete=True
    )
    for reg in day_3_registrations:
        send_chase_sms(reg, day=3)
    
    # Day 5 chase  
    day_5_registrations = get_registrations_where(
        created_date=5.days.ago(),
        status='ACTIVE', 
        payment_incomplete=True
    )
    for reg in day_5_registrations:
        send_chase_sms(reg, day=5)
        send_chase_email(reg, day=5)
    
    # Day 7 suspension
    day_7_registrations = get_registrations_where(
        created_date=7.days.ago(),
        status='ACTIVE',
        payment_incomplete=True
    )
    for reg in day_7_registrations:
        suspend_registration(reg)

def suspend_registration(registration):
    """Move registration to suspended table and notify parent"""
    
    # 1. Copy to suspended_registrations table
    copy_to_suspended_table(registration)
    
    # 2. Delete from main registrations_2526 table
    delete_from_main_table(registration.id)
    
    # 3. Send suspension SMS
    send_sms(registration.parent_phone,
        f"Registration for {registration.child_name} suspended due to non-payment. "
        f"You can still pay using your original link to reactivate.")

def check_and_restore_suspended_registration(registration_id):
    """Check if payment webhook relates to suspended registration"""
    
    suspended_reg = get_suspended_registration(registration_id)
    if suspended_reg:
        # Restore to main table
        restore_to_main_table(suspended_reg)
        delete_from_suspended_table(suspended_reg.id)
        
        # Send reactivation SMS
        send_sms(suspended_reg.parent_phone,
            f"Great news! Registration for {suspended_reg.child_name} "
            f"has been reactivated following payment.")
```

## SMS Templates

### **Payment Link (Routine 29)**
```
"Registration complete for [CHILD_NAME]! Pay when convenient: [PAYMENT_LINK] Registration not complete until payment made."
```

### **Day 3 Chase**
```
"Hi [PARENT_NAME], payment still pending for [CHILD_NAME]'s UTJFC registration. Pay here: [PAYMENT_LINK]"
```

### **Day 5 Chase**
```
"Final reminder: [CHILD_NAME]'s registration will be suspended in 2 days without payment: [PAYMENT_LINK]"
```

### **Day 7 Suspension**
```
"Registration for [CHILD_NAME] suspended due to non-payment. You can still pay using your original link to reactivate."
```

### **Reactivation**
```
"Great news! Registration for [CHILD_NAME] has been reactivated following payment. Welcome to UTJFC!"
```

## Technical Implementation Notes

### **GoCardless SDK Integration**
- Use SDK for webhook verification and parsing
- Use SDK for billing request creation
- HTTP requests still fine for auth URL generation (if working)

### **Security Considerations**
- Payment tokens should be UUIDs (unguessable)
- Webhook signature verification is critical
- Payment links should have reasonable expiry (30 days?)

### **Error Handling**
- Webhook delivery failures handled by GC retry logic
- Cron jobs provide backup payment status checking
- Failed SMS sends should be logged and retried

### **Performance Considerations**
- Index on payment_token for fast lookups
- Index on billing_request_id for webhook processing
- Archive old suspended registrations annually

## Benefits of This Architecture

✅ **User Experience**: No payment pressure during registration
✅ **Reliability**: Webhook + cron job redundancy
✅ **Flexibility**: Pay when convenient, automatic follow-up
✅ **Traceability**: Clear audit trail of all payment states
✅ **Automation**: Minimal manual intervention required
✅ **Recovery**: Suspended registrations can be restored
✅ **Scalability**: Handles hundreds of concurrent registrations

## Next Steps

1. Implement billing request creation in routine 29
2. Build payment link handler endpoint
3. Set up GoCardless webhook endpoint with SDK
4. Create suspended_registrations table
5. Build daily cron job for payment chasing
6. Test end-to-end flow with test GoCardless environment

## Testing Strategy

- Test payment link generation and redemption
- Test webhook processing for all event types
- Test suspension and restoration flow
- Test cron job logic with various payment states
- Load test with multiple concurrent payments 