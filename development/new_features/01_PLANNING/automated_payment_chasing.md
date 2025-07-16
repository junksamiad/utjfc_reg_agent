# Automated Payment Chasing System

**Feature ID**: `automated-payment-chasing`  
**Status**: Planning  
**Priority**: High  
**Estimated Effort**: 3-4 days  
**Dependencies**: AWS Lambda, CloudWatch Events, existing Twilio/Airtable integrations  

---

## Overview

Implement a comprehensive automated payment chasing system that tracks unpaid registrations and sends escalating reminders over a 7-day period, with automatic suspension and recovery mechanisms. The system will intelligently manage payment follow-ups, notify team managers of player status changes, and handle seamless reinstatement when payments are completed.

## Business Requirements

### Problem Statement
Currently, payment follow-up for registrations is manual, leading to:
- Inconsistent follow-up timing
- Administrative overhead for staff
- Delayed identification of non-paying registrations
- Poor communication between club and team managers
- Manual tracking of payment status

### Success Criteria
- **Payment Completion Rate**: 85% within 7 days
- **Suspension Rate**: <15% of registrations
- **Recovery Rate**: >90% of suspended registrations pay and return
- **Manager Satisfaction**: Timely notifications for team management
- **Administrative Efficiency**: 90% reduction in manual payment chasing

---

## Technical Architecture

### Current System Analysis

#### Registration Status Logic
The system uses `registration_status` field with these values:
- `pending_payment`: Neither payment nor mandate complete
- `incomplete`: Payment made but mandate not authorized
- `active`: Both payment and mandate complete
- `suspended`: Registration suspended due to non-payment

#### Existing Payment Flow
1. Registration created with `registration_status = 'pending_payment'`
2. Payment webhook updates `signing_on_fee_paid = 'Y'`
3. Mandate webhook updates `mandate_authorised = 'Y'`
4. Both complete → `registration_status = 'active'`

### Database Schema Changes

#### Add to registrations_2526 Table
```sql
payment_follow_up_count: Number
  - Purpose: Track escalation level (0-4)
  - Values: 0=no chasers, 1=day 3, 2=day 5, 3=day 7, 4=suspended
  - Default: 0

suspend_date: Date  
  - Purpose: Track when registration was suspended
  - Only populated when registration_status = 'suspended'
```

#### Create suspended_registrations_2526 Table
```sql
-- Exact carbon copy of registrations_2526 structure
-- Additional considerations:
--   - All computed formula fields need manual recreation
--   - Maintain same field IDs where possible
--   - Include suspend_date for tracking
--   - Preserve all registration data for recovery
```

#### Team Info Table Requirements
```sql
-- Existing team_info table must include:
manager_name: Text field
manager_phone: Text field (UK format)
manager_email: Text field (optional)
```

---

## Payment Chasing Workflow

### 7-Day Escalation Timeline

#### Day 3: First Reminder
- **Trigger**: `registration_status = 'pending_payment'` AND `payment_follow_up_count = 0` AND `DATETIME_DIFF(NOW(), created, 'days') >= 3`
- **Action**: Send first reminder SMS to parent
- **Update**: `payment_follow_up_count = 1`

#### Day 5: Second Reminder  
- **Trigger**: `registration_status = 'pending_payment'` AND `payment_follow_up_count = 1` AND `DATETIME_DIFF(NOW(), created, 'days') >= 5`
- **Action**: Send second reminder SMS to parent
- **Update**: `payment_follow_up_count = 2`

#### Day 7: Final Reminder
- **Trigger**: `registration_status = 'pending_payment'` AND `payment_follow_up_count = 2` AND `DATETIME_DIFF(NOW(), created, 'days') >= 7`
- **Action**: Send final reminder SMS to parent
- **Update**: `payment_follow_up_count = 3`

#### Day 8: Suspension Process
- **Trigger**: `registration_status = 'pending_payment'` AND `payment_follow_up_count = 3` AND `DATETIME_DIFF(NOW(), created, 'days') >= 8`
- **Actions**:
  1. Copy record to `suspended_registrations_2526`
  2. Delete record from `registrations_2526`
  3. Update `payment_follow_up_count = 4` in suspended table
  4. Send suspension notification to parent
  5. Send notification to team manager
- **Update**: Record moved to suspended table

### SMS Templates

#### Day 3 - First Reminder
```
Hi [Parent Name], your UTJFC registration for [Player Name] ([Team] [Age Group]) needs payment completion. Please pay here: [payment_link]
```

#### Day 5 - Second Reminder
```
Reminder: [Player Name]'s UTJFC registration payment is still pending. Complete payment: [payment_link]
```

#### Day 7 - Final Reminder
```
Final reminder: [Player Name]'s registration payment due by tomorrow. Please complete: [payment_link]
```

#### Day 8 - Parent Suspension Notice
```
Important: [Player Name]'s registration has been suspended due to non-payment. To reactivate, please complete payment: [payment_link]. Team manager has been notified.
```

#### Day 8 - Manager Notification
```
Hi [Manager Name], [Player Name] ([Parent Phone]) has been suspended from [Team] [Age Group] due to non-payment. They can reactivate by completing payment at their registration link.
```

#### Reinstatement - Manager Notification
```
Hi [Manager Name], [Player Name] has completed payment and been reinstated to [Team] [Age Group]. Registration is now active.
```

---

## AWS Lambda Implementation

### Lambda Function Architecture

#### Function Configuration
```yaml
Runtime: Python 3.9+
Memory: 256MB
Timeout: 15 minutes
Environment Variables:
  - AIRTABLE_API_KEY
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_PHONE_NUMBER
```

#### CloudWatch Events Schedule
```yaml
Schedule: Daily at 10:00 AM GMT
Rule: cron(0 10 * * ? *)
Target: payment-chasing-lambda
```

### Core Lambda Functions

#### Main Handler
```python
def lambda_handler(event, context):
    """
    Main entry point for payment chasing Lambda function.
    Processes all escalation levels in sequence.
    """
    try:
        # Day 3: First reminder
        result_day3 = process_payment_chasers(
            days=3, 
            follow_up_count=0, 
            message_type="first"
        )
        
        # Day 5: Second reminder  
        result_day5 = process_payment_chasers(
            days=5, 
            follow_up_count=1, 
            message_type="second"
        )
        
        # Day 7: Final reminder
        result_day7 = process_payment_chasers(
            days=7, 
            follow_up_count=2, 
            message_type="final"
        )
        
        # Day 8: Suspension
        result_day8 = process_suspensions(
            days=8, 
            follow_up_count=3
        )
        
        return {
            'statusCode': 200,
            'body': {
                'day3_processed': result_day3['count'],
                'day5_processed': result_day5['count'],
                'day7_processed': result_day7['count'],
                'day8_suspended': result_day8['count']
            }
        }
        
    except Exception as e:
        print(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
```

#### Payment Chaser Processing
```python
def process_payment_chasers(days: int, follow_up_count: int, message_type: str):
    """
    Process payment chasers for specific day and follow-up count.
    """
    # Query unpaid registrations
    unpaid_registrations = find_unpaid_registrations(days, follow_up_count)
    
    processed_count = 0
    for registration in unpaid_registrations:
        try:
            # Generate payment link
            payment_link = generate_payment_link(registration['billing_request_id'])
            
            # Send SMS reminder
            send_payment_reminder_sms(
                registration=registration,
                payment_link=payment_link,
                message_type=message_type
            )
            
            # Update follow-up count
            update_follow_up_count(
                registration['record_id'], 
                follow_up_count + 1
            )
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing registration {registration['record_id']}: {str(e)}")
            continue
    
    return {'count': processed_count}
```

#### Suspension Processing
```python
def process_suspensions(days: int, follow_up_count: int):
    """
    Process registrations for suspension on day 8.
    """
    registrations_for_suspension = find_unpaid_registrations(days, follow_up_count)
    
    suspended_count = 0
    for registration in registrations_for_suspension:
        try:
            # Copy to suspended table
            suspended_record_id = copy_to_suspended_table(registration)
            
            # Update follow-up count to 4 in suspended table
            update_suspended_follow_up_count(suspended_record_id, 4)
            
            # Delete from main table
            delete_from_main_table(registration['record_id'])
            
            # Generate payment link
            payment_link = generate_payment_link(registration['billing_request_id'])
            
            # Send suspension notice to parent
            send_suspension_notice_parent(registration, payment_link)
            
            # Get manager contact and notify
            manager_contact = get_manager_contact(
                registration['team'], 
                registration['age_group']
            )
            if manager_contact['success']:
                send_suspension_notice_manager(registration, manager_contact)
            
            suspended_count += 1
            
        except Exception as e:
            print(f"Error suspending registration {registration['record_id']}: {str(e)}")
            continue
    
    return {'count': suspended_count}
```

### Database Query Functions

#### Find Unpaid Registrations
```python
def find_unpaid_registrations(days_since_creation: int, follow_up_count: int):
    """
    Query registrations_2526 for records needing payment chasing.
    """
    formula = f"""
    AND(
        {{registration_status}} = 'pending_payment',
        {{payment_follow_up_count}} = {follow_up_count},
        DATETIME_DIFF(NOW(), {{created}}, 'days') >= {days_since_creation}
    )
    """
    
    # Execute Airtable query
    api = Api(AIRTABLE_API_KEY)
    table = api.table(BASE_ID, REGISTRATIONS_TABLE_ID)
    
    records = table.all(
        formula=formula,
        fields=[
            'record_id', 'player_first_name', 'player_last_name',
            'parent_first_name', 'parent_last_name', 'parent_phone',
            'team', 'age_group', 'billing_request_id', 'created',
            'payment_follow_up_count'
        ]
    )
    
    return records
```

#### Manager Contact Lookup
```python
def get_manager_contact(team_name: str, age_group: str):
    """
    Get manager contact details from team_info table.
    """
    formula = f"AND({{short_team_name}} = '{team_name}', {{age_group}} = '{age_group}')"
    
    api = Api(AIRTABLE_API_KEY)
    table = api.table(BASE_ID, TEAM_INFO_TABLE_ID)
    
    records = table.all(
        formula=formula,
        fields=['manager_name', 'manager_phone', 'manager_email']
    )
    
    if records:
        manager = records[0]['fields']
        return {
            'success': True,
            'manager_name': manager.get('manager_name', 'Team Manager'),
            'manager_phone': manager.get('manager_phone', ''),
            'manager_email': manager.get('manager_email', '')
        }
    else:
        return {
            'success': False,
            'error': f'No manager found for {team_name} {age_group}'
        }
```

### Suspension Management Functions

#### Copy to Suspended Table
```python
def copy_to_suspended_table(registration_record):
    """
    Copy registration record to suspended_registrations_2526.
    """
    # Extract all fields from registration
    fields = registration_record['fields'].copy()
    
    # Add suspension timestamp
    fields['suspend_date'] = datetime.now().isoformat()
    
    # Create record in suspended table
    api = Api(AIRTABLE_API_KEY)
    suspended_table = api.table(BASE_ID, SUSPENDED_REGISTRATIONS_TABLE_ID)
    
    new_record = suspended_table.create(fields)
    
    return new_record['id']
```

#### Recovery Function (For Webhook Processing)
```python
def recover_suspended_registration(billing_request_id: str):
    """
    Recover suspended registration when payment is completed.
    Called from enhanced webhook processing.
    """
    # Find in suspended table
    api = Api(AIRTABLE_API_KEY)
    suspended_table = api.table(BASE_ID, SUSPENDED_REGISTRATIONS_TABLE_ID)
    
    records = suspended_table.all(
        formula=f"{{billing_request_id}} = '{billing_request_id}'"
    )
    
    if not records:
        return {'success': False, 'error': 'No suspended registration found'}
    
    suspended_record = records[0]
    
    # Copy back to main table
    fields = suspended_record['fields'].copy()
    
    # Update payment status
    fields['signing_on_fee_paid'] = 'Y'
    fields['mandate_authorised'] = 'Y'  # Assumption: both completed in webhook
    fields['registration_status'] = 'active'
    
    # Remove suspend_date
    if 'suspend_date' in fields:
        del fields['suspend_date']
    
    # Create in main table
    main_table = api.table(BASE_ID, REGISTRATIONS_TABLE_ID)
    restored_record = main_table.create(fields)
    
    # Delete from suspended table
    suspended_table.delete(suspended_record['id'])
    
    # Notify manager of reinstatement
    manager_contact = get_manager_contact(fields['team'], fields['age_group'])
    if manager_contact['success']:
        send_reinstatement_notice_manager(fields, manager_contact)
    
    return {
        'success': True,
        'restored_record_id': restored_record['id'],
        'player_name': f"{fields['player_first_name']} {fields['player_last_name']}"
    }
```

---

## Enhanced Webhook Processing

### Current Webhook Flow
```
GoCardless Webhook → Find in registrations_2526 → Update payment status
```

### New Enhanced Flow
```
GoCardless Webhook → Find in registrations_2526 → Update payment status
    ↓ (if record not found)
Check suspended_registrations_2526 → Recover to registrations_2526
    ↓
Update payment status → Delete from suspended → Notify manager
```

### Webhook Enhancement Implementation

#### Modified Webhook Handler
```python
async def handle_payment_confirmed(event: dict):
    """
    Enhanced payment confirmation handler with suspension recovery.
    """
    billing_request_id = event.get('links', {}).get('billing_request')
    
    if not billing_request_id:
        return
    
    # Try to find in main registrations table first
    api = Api(AIRTABLE_API_KEY)
    table = api.table(BASE_ID, REGISTRATIONS_TABLE_ID)
    
    records = table.all(
        formula=f"{{billing_request_id}} = '{billing_request_id}'"
    )
    
    if records:
        # Normal flow - update main table
        record = records[0]
        update_payment_status(record['id'], 'signing_on_fee_paid', 'Y')
        print(f"✅ Payment confirmed for active registration")
        
    else:
        # Check suspended registrations
        print(f"🔍 Registration not found in main table, checking suspended...")
        
        recovery_result = recover_suspended_registration(billing_request_id)
        
        if recovery_result['success']:
            print(f"🎉 Suspended registration recovered: {recovery_result['player_name']}")
        else:
            print(f"❌ No registration found for billing_request_id: {billing_request_id}")
```

---

## SMS Integration

### Twilio Configuration
```python
# Use existing Twilio setup from registration tools
from registration_agent.tools.registration_tools.send_sms_payment_link import send_sms_with_retry

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN') 
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
```

### SMS Sending Functions

#### Payment Reminder SMS
```python
def send_payment_reminder_sms(registration: dict, payment_link: str, message_type: str):
    """
    Send payment reminder SMS to parent.
    """
    parent_name = f"{registration['parent_first_name']} {registration['parent_last_name']}"
    player_name = f"{registration['player_first_name']} {registration['player_last_name']}"
    team_info = f"{registration['team']} {registration['age_group']}"
    parent_phone = registration['parent_phone']
    
    # Select message template
    if message_type == "first":
        message = f"Hi {parent_name}, your UTJFC registration for {player_name} ({team_info}) needs payment completion. Please pay here: {payment_link}"
    elif message_type == "second":
        message = f"Reminder: {player_name}'s UTJFC registration payment is still pending. Complete payment: {payment_link}"
    elif message_type == "final":
        message = f"Final reminder: {player_name}'s registration payment due by tomorrow. Please complete: {payment_link}"
    
    # Send SMS using existing infrastructure
    result = send_sms_with_retry(
        to_phone=parent_phone,
        message_body=message,
        max_retries=3
    )
    
    return result
```

#### Manager Notification SMS
```python
def send_suspension_notice_manager(registration: dict, manager_contact: dict):
    """
    Send suspension notification to team manager.
    """
    player_name = f"{registration['player_first_name']} {registration['player_last_name']}"
    parent_phone = registration['parent_phone']
    team_info = f"{registration['team']} {registration['age_group']}"
    manager_name = manager_contact['manager_name']
    manager_phone = manager_contact['manager_phone']
    
    message = f"Hi {manager_name}, {player_name} ({parent_phone}) has been suspended from {team_info} due to non-payment. They can reactivate by completing payment at their registration link."
    
    result = send_sms_with_retry(
        to_phone=manager_phone,
        message_body=message,
        max_retries=3
    )
    
    return result

def send_reinstatement_notice_manager(registration: dict, manager_contact: dict):
    """
    Send reinstatement notification to team manager.
    """
    player_name = f"{registration['player_first_name']} {registration['player_last_name']}"
    team_info = f"{registration['team']} {registration['age_group']}"
    manager_name = manager_contact['manager_name']
    manager_phone = manager_contact['manager_phone']
    
    message = f"Hi {manager_name}, {player_name} has completed payment and been reinstated to {team_info}. Registration is now active."
    
    result = send_sms_with_retry(
        to_phone=manager_phone,
        message_body=message,
        max_retries=3
    )
    
    return result
```

---

## Integration Points

### Reused Components

#### Payment Link Generation
```python
def generate_payment_link(billing_request_id: str):
    """
    Generate payment link using existing /reg_setup endpoint.
    """
    base_url = os.getenv('PAYMENT_BASE_URL', 'https://urmstontownjfc.co.uk')
    return f"{base_url}/api/reg_setup/{billing_request_id}"
```

#### Existing Infrastructure
- **Twilio SMS**: Reuse existing `send_sms_payment_link` functionality
- **Airtable Operations**: Leverage existing database tools
- **Payment Processing**: Use existing GoCardless webhook handlers
- **Error Handling**: Adopt existing retry mechanisms

### New Components Required

#### Lambda-Specific Modules
```
lambda_functions/
├── payment_chasing.py          # Main Lambda function
├── requirements.txt            # Lambda dependencies  
├── database_operations.py      # Airtable CRUD functions
├── sms_operations.py          # SMS sending functions
├── suspension_management.py    # Suspension/recovery logic
└── config.py                  # Configuration management
```

#### CloudFormation Template
```yaml
# cloudformation/payment-chasing-stack.yml
Resources:
  PaymentChasingLambda:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.9
      Handler: payment_chasing.lambda_handler
      Environment:
        Variables:
          AIRTABLE_API_KEY: !Ref AirtableApiKey
          TWILIO_ACCOUNT_SID: !Ref TwilioAccountSid
          # ... other environment variables
  
  PaymentChasingSchedule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: "cron(0 10 * * ? *)"
      Targets:
        - Arn: !GetAtt PaymentChasingLambda.Arn
          Id: PaymentChasingTarget
```

---

## Testing Strategy

### Unit Testing

#### Test Coverage Areas
```python
# test_payment_chasing.py
def test_find_unpaid_registrations():
    # Test query logic for different scenarios
    
def test_payment_reminder_sms():
    # Test SMS template generation
    
def test_suspension_process():
    # Test record copying and deletion
    
def test_recovery_process():
    # Test suspended registration recovery
    
def test_manager_notifications():
    # Test manager contact lookup and SMS
```

#### Mock Data Setup
```python
# Create test registrations with various states
test_registrations = [
    {
        'registration_status': 'pending_payment',
        'payment_follow_up_count': 0,
        'created': '2025-01-01T10:00:00Z'  # 3+ days ago
    },
    {
        'registration_status': 'pending_payment', 
        'payment_follow_up_count': 2,
        'created': '2025-01-01T10:00:00Z'  # 7+ days ago
    }
]
```

### Integration Testing

#### End-to-End Flow Tests
1. **Create test registration** with `pending_payment` status
2. **Run Lambda function** manually
3. **Verify SMS sent** and `payment_follow_up_count` updated
4. **Simulate payment completion** via webhook
5. **Verify recovery process** if suspended

#### Webhook Testing
```python
def test_webhook_with_suspended_registration():
    # Create suspended registration
    # Send payment webhook
    # Verify recovery to main table
    # Verify manager notification sent
```

### Manual Testing Scenarios

#### Scenario 1: Normal Payment Chasing
1. Create registration with `pending_payment` status
2. Wait or manually trigger for day 3, 5, 7
3. Verify SMS messages sent with correct templates
4. Complete payment and verify no more chasers

#### Scenario 2: Suspension and Recovery
1. Let registration reach day 8 without payment
2. Verify suspension process (copy to suspended table)
3. Verify manager notification sent
4. Complete payment and verify recovery process
5. Verify manager reinstatement notification

---

## Monitoring & Alerting

### CloudWatch Metrics

#### Lambda Metrics
- **Execution Duration**: Monitor for performance issues
- **Error Rate**: Track failed executions
- **Invocation Count**: Verify daily scheduling
- **Memory Utilization**: Optimize resource allocation

#### Business Metrics
```python
# Custom CloudWatch metrics
cloudwatch = boto3.client('cloudwatch')

# Track payment chasing effectiveness
cloudwatch.put_metric_data(
    Namespace='UTJFC/PaymentChasing',
    MetricData=[
        {
            'MetricName': 'ChasesSent',
            'Value': chases_sent_count,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Day', 'Value': str(chase_day)}
            ]
        },
        {
            'MetricName': 'SuspensionsCount',
            'Value': suspensions_count,
            'Unit': 'Count'
        },
        {
            'MetricName': 'RecoveriesCount', 
            'Value': recoveries_count,
            'Unit': 'Count'
        }
    ]
)
```

#### SMS Delivery Tracking
```python
def track_sms_delivery(sms_sid: str, recipient_type: str):
    """
    Track SMS delivery status using Twilio webhooks.
    """
    # Monitor delivery status
    # Log failed deliveries for retry
    # Alert on high failure rates
```

### Alerting Strategy

#### Critical Alerts
- **Lambda execution failures**: >5% failure rate
- **SMS delivery failures**: >10% failure rate  
- **Database operation failures**: Any failures
- **Webhook processing failures**: Payment recovery issues

#### Business Alerts
- **High suspension rate**: >20% of registrations suspended
- **Low recovery rate**: <80% of suspended registrations recovered
- **Manager contact failures**: Missing manager details

---

## Performance Considerations

### Lambda Optimization

#### Memory and Timeout Tuning
```yaml
# Based on estimated workload
Memory: 256MB  # Start conservative, monitor and adjust
Timeout: 15 minutes  # Allow for large batches during peak season
Reserved Concurrency: 1  # Prevent concurrent executions
```

#### Batch Processing Strategy
```python
def process_in_batches(records: list, batch_size: int = 50):
    """
    Process records in batches to avoid timeout and rate limiting.
    """
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        process_batch(batch)
        
        # Rate limiting pause between batches
        time.sleep(2)
```

### Airtable Rate Limiting
```python
class AirtableRateLimiter:
    def __init__(self, calls_per_second: float = 5):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Ensure we don't exceed Airtable rate limits."""
        time_since_last_call = time.time() - self.last_call_time
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last_call < min_interval:
            time.sleep(min_interval - time_since_last_call)
        
        self.last_call_time = time.time()
```

### Cost Optimization

#### Lambda Cost Estimation
```yaml
# Monthly cost estimation (assuming peak registration season)
Invocations: 30 per month (daily)
Duration: ~5 minutes average
Memory: 256MB
Estimated Cost: ~$2-3/month

# SMS Costs (Twilio)
SMS per month: ~200-500 messages
Cost per SMS: ~£0.04
Estimated SMS Cost: £8-20/month

Total Additional Cost: ~£10-25/month
```

---

## Error Handling

### Error Classification

#### Recoverable Errors
- **Temporary API failures**: Retry with exponential backoff
- **Rate limit exceeded**: Implement backoff and retry
- **Network timeouts**: Retry with longer timeout

#### Non-Recoverable Errors  
- **Invalid billing request ID**: Log and skip
- **Malformed phone numbers**: Log and alert
- **Missing required fields**: Log and alert

### Error Handling Implementation

#### Retry Mechanism
```python
import time
from functools import wraps

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    
                    wait_time = backoff_factor ** attempt
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def send_sms_with_retry(phone: str, message: str):
    # SMS sending logic with automatic retry
    pass
```

#### Dead Letter Queue
```yaml
# For failed Lambda executions
DeadLetterQueue:
  Type: AWS::SQS::Queue
  Properties:
    MessageRetentionPeriod: 1209600  # 14 days
    
PaymentChasingLambda:
  Properties:
    DeadLetterConfig:
      TargetArn: !GetAtt DeadLetterQueue.Arn
```

---

## Security Considerations

### Data Protection

#### Sensitive Data Handling
```python
# Mask phone numbers in logs
def mask_phone_number(phone: str) -> str:
    if len(phone) > 4:
        return f"{phone[:2]}***{phone[-2:]}"
    return "***"

# Secure environment variable access
def get_secure_env_var(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Required environment variable {var_name} not found")
    return value
```

#### Access Control
```yaml
# Lambda execution role with minimal permissions
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: CloudWatchMetrics
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - cloudwatch:PutMetricData
              Resource: '*'
```

### API Security

#### Environment Variable Encryption
```yaml
# Use AWS Systems Manager Parameter Store for secrets
Parameters:
  AirtableApiKey:
    Type: AWS::SSM::Parameter::Value<String>
    NoEcho: true
    
  TwilioAuthToken:
    Type: AWS::SSM::Parameter::Value<String>
    NoEcho: true
```

---

## Deployment Strategy

### Phase 1: Database Schema (Week 1)
1. **Add payment_follow_up_count field** to registrations_2526
2. **Create suspended_registrations_2526 table**
3. **Verify manager contact fields** in team_info table
4. **Update webhook processing** for suspension recovery
5. **Test webhook changes** with existing payments

### Phase 2: Lambda Development (Week 2)  
1. **Develop Lambda function** with payment chasing logic
2. **Create CloudFormation template** for AWS resources
3. **Implement unit tests** for core functionality
4. **Deploy to development environment**
5. **Test with small dataset**

### Phase 3: Integration Testing (Week 3)
1. **End-to-end testing** with real Airtable data
2. **SMS delivery testing** with test phone numbers
3. **Manager notification testing**
4. **Performance testing** with large datasets
5. **Error handling validation**

### Phase 4: Production Deployment (Week 4)
1. **Deploy Lambda to production**
2. **Configure CloudWatch monitoring**
3. **Enable daily scheduling**
4. **Monitor initial executions**
5. **Adjust timing and templates based on feedback**

### Rollback Plan
```bash
# Emergency rollback procedure
aws lambda update-function-configuration \
  --function-name payment-chasing-lambda \
  --environment Variables='{ENABLED="false"}'

# Disable CloudWatch Events rule
aws events disable-rule --name payment-chasing-schedule
```

---

## Future Enhancements

### Separate Feature: Mandate-Only Payment Links
**Issue**: Registrations with `registration_status = 'incomplete'` (payment made but no mandate)
**Solution**: Create separate chasing workflow with mandate-only payment links
**Priority**: Medium (separate feature document required)

### Advanced Features (Future Consideration)
- **Dynamic scheduling** based on payment behavior patterns
- **Email notifications** in addition to SMS
- **Manager dashboard** for team payment status
- **Payment plan options** for financial hardship cases
- **Seasonal timing adjustments** based on registration periods

### Analytics and Reporting
- **Payment completion rate trends**
- **Optimal chasing timing analysis**
- **Team-by-team payment performance**
- **Manager notification effectiveness**

---

## Success Metrics

### Key Performance Indicators

#### Financial Impact
- **Payment Completion Rate**: Target 85% within 7 days (baseline: unknown)
- **Revenue Recovery**: Track additional payments from chasing
- **Suspension Rate**: Target <15% of total registrations
- **Recovery Rate**: Target >90% of suspended registrations pay and return

#### Operational Efficiency  
- **Administrative Time Saved**: Target 90% reduction in manual chasing
- **Manager Notification Accuracy**: 100% of suspensions/reinstatements notified
- **System Reliability**: 99.9% successful Lambda executions
- **SMS Delivery Rate**: >95% successful delivery

#### User Experience
- **Payment Link Engagement**: Track click-through rates
- **Time to Payment**: Measure days from reminder to payment
- **Manager Satisfaction**: Qualitative feedback on notification usefulness

### Monitoring Dashboard

#### Business Metrics
```yaml
Dashboard Widgets:
  - Daily Payment Chasers Sent (by day type)
  - Suspension vs Recovery Rate Trends  
  - Payment Completion Rate by Team/Age Group
  - SMS Delivery Success Rate
  - Manager Notification Coverage
```

#### Technical Metrics
```yaml
Technical Monitoring:
  - Lambda Execution Success Rate
  - Average Execution Duration
  - Airtable API Error Rate
  - Twilio SMS Error Rate
  - Webhook Processing Success Rate
```

---

## Conclusion

This automated payment chasing system will significantly improve the efficiency of registration payment collection while maintaining professional communication standards. The 7-day escalation process provides multiple opportunities for parents to complete payments before suspension, while the manager notification system ensures team leaders stay informed of player status changes.

The system leverages existing infrastructure (Twilio, Airtable, GoCardless webhooks) while adding minimal additional AWS costs (~£10-25/month). The comprehensive error handling, monitoring, and recovery mechanisms ensure reliable operation during critical registration periods.

**Next Steps**: Await approval to begin Phase 1 development, starting with database schema updates and webhook enhancement for suspension recovery functionality.