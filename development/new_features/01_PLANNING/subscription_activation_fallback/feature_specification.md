# Subscription Activation Fallback System

**Feature ID**: `subscription-activation-fallback`  
**Status**: Planning  
**Priority**: High  
**Estimated Effort**: 1-2 days  
**Dependencies**: Existing GoCardless integration, AWS Lambda/EventBridge  
**Implementation Date**: TBD  
**Implemented By**: TBD  
**Branch**: TBD  

---

## Overview

Implement a daily fallback system to catch and resolve cases where GoCardless webhook processing successfully sets `mandate_authorised = 'Y'` but fails to activate the monthly subscription. This ensures no registrations are left in limbo and provides a foundation for future automated database maintenance tasks.

## Business Requirements

### Problem Statement
Registration is currently live, and there have been cases where:
- GoCardless webhook successfully processes mandate authorization (`mandate_authorised = 'Y'`)
- Payment confirmation is recorded (`signing_on_fee_paid = 'Y'`)
- However, the subscription activation step fails silently
- This leaves players in an incomplete registration state despite successful payment and mandate

### Success Criteria
- 100% of eligible registrations (paid + mandate authorized) have active subscriptions within 24 hours
- Failed subscription attempts are flagged with clear error status for manual intervention
- System provides daily automated "mop-up" of missed subscription activations
- Cost-effective implementation using AWS free tier where possible

### User Stories
- **As a club administrator**, I want confidence that all paid registrations automatically get their monthly subscriptions activated
- **As a parent**, I want assurance that my successful payment and mandate setup results in complete registration
- **As a developer**, I want a reliable fallback system that catches edge cases in webhook processing

## Technical Changes Required

### Code Locations to Update

#### New Files to Create
- `backend/scheduled_tasks/subscription_fallback.py` - Main fallback logic
- `backend/scheduled_tasks/lambda_handler.py` - AWS Lambda wrapper
- `backend/scheduled_tasks/requirements.txt` - Lambda dependencies
- `infrastructure/lambda_deployment.yml` - CloudFormation/SAM template
- `infrastructure/eventbridge_schedule.yml` - Daily cron schedule configuration

#### Existing Files to Modify
- `backend/registration_agent/tools/registration_tools/gocardless_payment.py` - Export activation logic for reuse
- **No schema changes required** - Using existing database fields

### Database Considerations

#### New Fields in Registrations Table
- **No new fields required** - Will use existing `subscription_error` field for error logging

#### Query Patterns
- Daily query for records where `signing_on_fee_paid = 'Y'` AND `mandate_authorised = 'Y'` AND `subscription_activated != 'Y'`
- Update patterns for successful and failed fallback attempts using existing fields

### API Changes
- No public API changes required
- Internal scheduled task endpoint for testing: `POST /admin/run-subscription-fallback`

### Frontend Changes
- No frontend changes required for core functionality
- Optional: Admin dashboard showing fallback statistics

## Implementation Notes

### Architecture Considerations
- **Serverless Design**: Use AWS Lambda for cost-effective scheduled execution
- **Idempotent Operations**: Ensure multiple runs don't create duplicate subscriptions
- **Error Handling**: Graceful failure with detailed logging for manual intervention
- **Reusable Logic**: Extract subscription activation from webhook handler for reuse

### Security Considerations
- Lambda execution role with minimal required permissions
- Secure handling of GoCardless API credentials in Lambda environment
- Rate limiting to prevent API abuse
- Audit logging for all fallback operations

### Performance Considerations
- **Batch Processing**: Process multiple records efficiently in single Lambda execution
- **API Rate Limits**: Respect GoCardless API limits (avoid overwhelming their service)
- **Database Optimization**: Use targeted queries to minimize Airtable API calls
- **Timeout Handling**: Lambda timeout consideration for large batches

### Integration Points
- **GoCardless API**: Reuse existing subscription activation logic
- **Airtable API**: Query and update registration records
- **AWS EventBridge**: Schedule daily execution
- **Existing Webhook Handler**: Share common subscription activation code

## Testing Strategy

### Unit Testing
- Test subscription activation logic in isolation
- Mock GoCardless API responses for various scenarios
- Test error handling and retry logic
- Validate database update operations

### Integration Testing
- End-to-end test with real Airtable records (test environment)
- Test Lambda deployment and execution
- Verify EventBridge scheduling triggers correctly
- Test with various edge cases (missing data, API failures)

### Manual Testing
- Create test records in incomplete state
- Run fallback process manually
- Verify subscription creation in GoCardless dashboard
- Confirm database updates are correct

### Edge Cases
- Records with missing mandate IDs
- GoCardless API failures/timeouts
- Airtable API rate limiting
- Lambda cold start and timeout scenarios
- Duplicate subscription prevention

## Risk Assessment

### Risk Level
**Medium** - Critical for registration integrity but well-defined scope

### Potential Issues
1. **API Rate Limits**: GoCardless or Airtable API limits could cause failures
2. **Duplicate Subscriptions**: Multiple activations could create billing issues
3. **Cost Escalation**: Lambda costs if batch sizes grow unexpectedly
4. **Data Inconsistency**: Partial failures leaving records in inconsistent state

### Mitigation
1. **Rate Limiting**: Implement delays and batch size limits
2. **Idempotency**: Check existing subscriptions before creating new ones
3. **Cost Monitoring**: Use AWS free tier; monitor usage with CloudWatch
4. **Transaction Safety**: Update database only after successful GoCardless operations

### Rollback Plan
1. **Disable Schedule**: Turn off EventBridge rule immediately
2. **Manual Cleanup**: Admin interface to review and correct any issues
3. **Database Restoration**: Restore registration records from backup if needed
4. **GoCardless Cleanup**: Manual cancellation of any erroneous subscriptions

## Deployment

### Changes Required

#### AWS Infrastructure
1. **Create Lambda Function**:
   ```bash
   # Package and deploy Lambda
   cd backend/scheduled_tasks
   zip subscription-fallback.zip lambda_handler.py subscription_fallback.py requirements.txt
   aws lambda create-function --function-name subscription-fallback-utjfc
   ```

2. **Create EventBridge Schedule**:
   ```bash
   # Create daily schedule (8 AM UTC = 9 AM GMT)
   aws events put-rule --name subscription-fallback-daily --schedule-expression "cron(0 8 * * ? *)"
   aws events put-targets --rule subscription-fallback-daily --targets "Id"="1","Arn"="arn:aws:lambda:region:account:function:subscription-fallback-utjfc"
   ```

3. **Set IAM Permissions**:
   - Lambda execution role
   - EventBridge trigger permissions
   - CloudWatch Logs access

#### Environment Variables
```bash
# Lambda environment variables
AIRTABLE_API_KEY=pat_xxx
GOCARDLESS_API_KEY=live_xxx
GOCARDLESS_ENVIRONMENT=live
LOGGING_LEVEL=INFO
```

#### Migration Steps
1. Deploy Lambda function to AWS
2. Configure EventBridge schedule
3. Test with dry-run mode first
4. Enable live processing after validation

#### Verification Steps
1. Confirm Lambda function deploys successfully
2. Test manual Lambda invocation
3. Verify EventBridge triggers Lambda correctly
4. Monitor CloudWatch logs for execution
5. Check Airtable for successful record updates

## Future Considerations

### Extensibility
- **Additional Database Checks**: Framework for other automated maintenance tasks
- **Enhanced Monitoring**: Integration with club's monitoring systems
- **Webhook Recovery**: Extend to catch other webhook processing failures
- **Payment Monitoring**: Monitor for failed monthly payments

### Maintenance
- **Monthly Review**: Check fallback statistics and tune batch sizes
- **Cost Monitoring**: Track AWS usage and optimize if needed
- **Error Analysis**: Regular review of failed activation attempts
- **API Updates**: Keep GoCardless integration current with API changes

### Related Features
- **Payment Failure Handling**: Automated response to failed monthly payments
- **Registration Status Dashboard**: Admin view of all registration states
- **Automated Reporting**: Daily/weekly registration summary emails
- **Data Quality Checks**: Broader database validation and cleanup tasks

## Cost Analysis

### AWS Pricing (Based on 2025 rates)

#### EventBridge Scheduler
- **Free Tier**: 14 million invocations per month
- **Cost**: $1 per million invocations after free tier
- **Our Usage**: 1 daily execution = 365 executions/year = FREE

#### Lambda Execution
- **Free Tier**: 1 million requests + 400,000 GB-seconds compute time
- **Estimated Usage**: 1 daily run × 30 seconds × 128MB = ~4 GB-seconds/month
- **Cost**: FREE (well within free tier limits)

#### Data Transfer
- **Airtable API**: Existing subscription covers API calls
- **GoCardless API**: No additional charges for subscription management
- **AWS Data Transfer**: Negligible for API calls

#### **Total Monthly Cost: $0** (within AWS free tier)

### Alternative Options Considered
1. **Cron Job on Existing Server**: Higher risk, server dependency
2. **Third-party Scheduling Service**: Additional cost and complexity
3. **Manual Daily Checks**: Not scalable, human error prone

### Recommended Approach
Use AWS Lambda with EventBridge Rules (not Scheduler) for completely free operation within the 100,000 monthly invocations limit.

## Implementation Priority

### Phase 1: Core Fallback (Immediate - Registration Live)
- Basic subscription activation fallback
- Daily execution schedule
- Error logging and status updates

### Phase 2: Enhanced Monitoring (Within 1 week)
- CloudWatch dashboards
- Error alerting
- Admin testing interface

### Phase 3: Extended Automation (Future)
- Additional database maintenance tasks
- Payment failure monitoring
- Enhanced reporting

---

*Feature specification created for immediate implementation to support live registration system.*