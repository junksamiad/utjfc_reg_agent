# Implementation Plan: Subscription Activation Fallback System

## Technical Implementation Details

### 1. Core Fallback Logic

#### Main Fallback Script (`backend/scheduled_tasks/subscription_fallback.py`)

```python
# Key implementation components:

class SubscriptionFallbackProcessor:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.airtable_api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.table = self.airtable_api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
    def find_incomplete_registrations(self):
        """Find records needing subscription activation"""
        formula = """
        AND(
            {signing_on_fee_paid} = 'Y',
            {mandate_authorised} = 'Y',
            OR(
                {subscription_activated} != 'Y',
                {subscription_activated} = ''
            )
        )
        """
        return self.table.all(formula=formula)
    
    def process_record(self, record):
        """Process individual record for subscription activation"""
        try:
            # Get billing request ID from record
            billing_request_id = record['fields'].get('billings_request_id')
            if not billing_request_id:
                return self.handle_missing_billing_request(record)
            
            # Fetch mandate_id from GoCardless billing request
            mandate_id = self.get_mandate_from_billing_request(billing_request_id)
            if not mandate_id:
                return self.handle_missing_mandate(record)
            
            # Reuse existing activation logic
            from registration_agent.tools.registration_tools.gocardless_payment import activate_subscription
            
            result = activate_subscription(
                mandate_id=mandate_id,
                registration_record=record
            )
            
            if result.get('success'):
                self.update_success(record, result)
                return True
            else:
                self.update_failure(record, result.get('message'))
                return False
                
        except Exception as e:
            self.update_failure(record, str(e))
            return False
    
    def get_mandate_from_billing_request(self, billing_request_id):
        """Fetch mandate ID from GoCardless billing request"""
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GOCARDLESS_API_KEY")}',
                'GoCardless-Version': '2015-07-06'
            }
            
            response = requests.get(
                f'https://api.gocardless.com/billing_requests/{billing_request_id}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                mandate_id = data['billing_requests']['links'].get('mandate_request_mandate')
                return mandate_id
            else:
                logger.error(f"Failed to fetch billing request {billing_request_id}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching billing request: {str(e)}")
            return None
```

#### Lambda Handler (`backend/scheduled_tasks/lambda_handler.py`)

```python
import json
import logging
from subscription_fallback import SubscriptionFallbackProcessor

def lambda_handler(event, context):
    """AWS Lambda entry point for subscription fallback"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Check if this is a dry run
        dry_run = event.get('dry_run', False)
        
        # Initialize processor
        processor = SubscriptionFallbackProcessor(dry_run=dry_run)
        
        # Find and process incomplete registrations
        incomplete_records = processor.find_incomplete_registrations()
        
        logger.info(f"Found {len(incomplete_records)} incomplete registrations")
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for record in incomplete_records:
            results['processed'] += 1
            
            if processor.process_record(record):
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"Processing complete: {results}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### 2. Database Schema Updates

#### No New Fields Required
- Will use existing `subscription_error` field for error logging
- Registration status changes to 'incomplete' on failure for manual intervention

### 3. AWS Infrastructure Setup

#### EventBridge Schedule Configuration

```yaml
# infrastructure/eventbridge_schedule.yml
Resources:
  SubscriptionFallbackSchedule:
    Type: AWS::Events::Rule
    Properties:
      Name: subscription-fallback-daily
      Description: "Daily subscription activation fallback"
      ScheduleExpression: "cron(0 8 * * ? *)"  # 8 AM UTC daily
      State: ENABLED
      Targets:
        - Arn: !GetAtt SubscriptionFallbackFunction.Arn
          Id: "SubscriptionFallbackTarget"
```

#### Lambda Function Configuration

```yaml
# infrastructure/lambda_deployment.yml
Resources:
  SubscriptionFallbackFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: subscription-fallback-utjfc
      Runtime: python3.12
      Handler: lambda_handler.lambda_handler
      Code:
        ZipFile: !Sub |
          # Code will be deployed separately
      Environment:
        Variables:
          AIRTABLE_API_KEY: !Ref AirtableApiKey
          GOCARDLESS_API_KEY: !Ref GoCardlessApiKey
          GOCARDLESS_ENVIRONMENT: live
      Timeout: 300  # 5 minutes
      MemorySize: 128
      Role: !GetAtt LambdaExecutionRole.Arn
```

### 4. Code Refactoring

#### Extract Reusable Subscription Logic

```python
# Modify gocardless_payment.py to expose activation logic

def activate_subscription_standalone(mandate_id, registration_data):
    """
    Standalone subscription activation for fallback processing
    
    Args:
        mandate_id (str): GoCardless mandate ID
        registration_data (dict): Registration record data
        
    Returns:
        dict: Activation result with success status and details
    """
    # Extract existing logic from activate_subscription()
    # Make it work with both webhook and fallback contexts
```

### 5. Testing Implementation

#### Unit Tests (`tests/test_subscription_fallback.py`)

```python
import unittest
from unittest.mock import Mock, patch
from subscription_fallback import SubscriptionFallbackProcessor

class TestSubscriptionFallback(unittest.TestCase):
    
    def setUp(self):
        self.processor = SubscriptionFallbackProcessor(dry_run=True)
    
    @patch('subscription_fallback.Api')
    def test_find_incomplete_registrations(self, mock_api):
        # Test finding records needing fallback
        pass
    
    @patch('registration_agent.tools.registration_tools.gocardless_payment.activate_subscription')
    def test_successful_activation(self, mock_activate):
        # Test successful subscription activation
        pass
    
    def test_missing_mandate_handling(self):
        # Test handling of records without mandate_id
        pass
```

#### Integration Test (`tests/test_integration.py`)

```python
def test_end_to_end_fallback():
    """Test complete fallback process with test data"""
    # Create test registration record in incomplete state
    # Run fallback processor
    # Verify subscription creation
    # Verify database updates
```

### 6. Deployment Steps

#### Step 1: Code Preparation
```bash
# Create deployment package
cd backend/scheduled_tasks
pip install -r requirements.txt -t .
zip -r subscription-fallback.zip .
```

#### Step 2: AWS Lambda Deployment
```bash
# Create Lambda function
aws lambda create-function \
    --function-name subscription-fallback-utjfc \
    --runtime python3.12 \
    --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://subscription-fallback.zip \
    --timeout 300 \
    --memory-size 128
```

#### Step 3: EventBridge Configuration
```bash
# Create schedule rule
aws events put-rule \
    --name subscription-fallback-daily \
    --schedule-expression "cron(0 8 * * ? *)" \
    --description "Daily subscription activation fallback"

# Add Lambda target
aws events put-targets \
    --rule subscription-fallback-daily \
    --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:subscription-fallback-utjfc"
```

#### Step 4: Environment Configuration
```bash
# Set Lambda environment variables
aws lambda update-function-configuration \
    --function-name subscription-fallback-utjfc \
    --environment Variables='{
        "AIRTABLE_API_KEY":"pat_xxx",
        "GOCARDLESS_API_KEY":"live_xxx",
        "GOCARDLESS_ENVIRONMENT":"live"
    }'
```

### 7. Monitoring and Alerting

#### CloudWatch Logging
```python
# Enhanced logging in fallback processor
import logging
logger = logging.getLogger(__name__)

def process_record(self, record):
    player_name = f"{record['fields'].get('player_first_name')} {record['fields'].get('player_last_name')}"
    logger.info(f"Processing fallback for {player_name}")
    
    # ... processing logic ...
    
    if success:
        logger.info(f"✅ Subscription activated for {player_name}")
    else:
        logger.error(f"❌ Failed to activate subscription for {player_name}: {error}")
```

#### CloudWatch Alarms
```yaml
SubscriptionFallbackErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: subscription-fallback-errors
    AlarmDescription: "Alert when subscription fallback has errors"
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
```

### 8. Performance Optimization

#### Batch Processing Strategy
```python
def process_in_batches(self, records, batch_size=10):
    """Process records in batches to manage API rate limits"""
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        for record in batch:
            self.process_record(record)
            
        # Rate limiting delay between batches
        if i + batch_size < len(records):
            time.sleep(2)  # 2 second delay between batches
```

#### API Rate Limit Handling
```python
import time
from requests.exceptions import RequestException

def safe_api_call(self, api_func, *args, **kwargs):
    """Execute API call with retry logic for rate limits"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except RequestException as e:
            if '429' in str(e):  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception("Max retries exceeded")
```

### 9. Error Handling Strategy

#### Graceful Degradation
```python
def handle_processing_error(self, record, error):
    """Handle errors gracefully with detailed logging"""
    record_id = record['id']
    player_name = f"{record['fields'].get('player_first_name')} {record['fields'].get('player_last_name')}"
    
    # Update with error and set status to incomplete
    update_data = {
        'subscription_error': str(error),
        'registration_status': 'incomplete'
    }
    
    logger.error(f"❌ Failed to activate subscription for {player_name}: {error}")
    logger.info(f"📋 Record flagged as incomplete for manual intervention")
    
    self.table.update(record_id, update_data)
```

### 10. Rollback Procedures

#### Emergency Disable
```bash
# Disable EventBridge rule immediately
aws events disable-rule --name subscription-fallback-daily

# Delete Lambda function if needed
aws lambda delete-function --function-name subscription-fallback-utjfc
```

#### Data Recovery
```python
def rollback_subscription_activations(activation_date):
    """Rollback subscriptions activated on specific date"""
    # Query records activated by fallback on given date
    # Cancel GoCardless subscriptions
    # Reset database fields to pre-activation state
```

---

## Implementation Timeline

### Day 1: Core Development
- [ ] Create fallback processor logic
- [ ] Extract reusable subscription activation code
- [ ] Write unit tests
- [ ] Test locally with development environment

### Day 2: AWS Deployment
- [ ] Create Lambda deployment package
- [ ] Deploy to AWS Lambda
- [ ] Configure EventBridge schedule
- [ ] Set up CloudWatch monitoring
- [ ] Test end-to-end with dry-run mode

### Day 3: Production Validation
- [ ] Test with real incomplete records
- [ ] Monitor execution logs
- [ ] Validate subscription creation in GoCardless
- [ ] Enable live processing

### Ongoing: Monitoring
- [ ] Daily review of CloudWatch logs
- [ ] Weekly analysis of fallback statistics
- [ ] Monthly cost review and optimization

---

*Implementation plan designed for rapid deployment to support live registration system.*