# Subscription Activation Fallback System

## Overview

A critical fallback system to ensure all paid registrations with authorized mandates receive their monthly subscription activation, even if the primary GoCardless webhook processing fails.

## Problem

During live registration, there have been cases where:
- GoCardless webhook successfully processes payment (`signing_on_fee_paid = 'Y'`)
- Mandate authorization is recorded (`mandate_authorised = 'Y'`)
- However, subscription activation fails silently
- Players are left in incomplete registration state despite successful payment

## Solution

Daily AWS Lambda function that:
1. Queries for records with payment + mandate but no active subscription
2. Attempts to activate missing subscriptions using existing GoCardless logic
3. Updates database with success/failure status
4. Flags persistent failures for manual intervention

## Key Features

- **Cost-Effective**: Uses AWS free tier (EventBridge Rules + Lambda)
- **Reliable**: Reuses existing, tested subscription activation logic
- **Extensible**: Framework for future automated database maintenance
- **Safe**: Idempotent operations prevent duplicate subscriptions

## Quick Start

### Testing the Feature

```bash
# Run unit tests
cd tests/
python -m pytest test_subscription_fallback.py -v

# Run integration test with test data
python test_integration.py

# Manual test with dry-run mode
python test_manual.py --dry-run
```

### Local Development

```bash
# Test fallback logic locally
cd backend/scheduled_tasks/
python subscription_fallback.py --dry-run

# Test specific record
python subscription_fallback.py --record-id rec123456 --dry-run
```

### Deploy to AWS

```bash
# Package for deployment
cd backend/scheduled_tasks/
./deploy.sh

# Test deployed function
aws lambda invoke --function-name subscription-fallback-utjfc --payload '{"dry_run": true}' response.json
```

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   EventBridge       │    │   Lambda Function   │    │   Airtable DB       │
│   Daily Schedule    │───▶│   Fallback Logic    │───▶│   Update Records    │
│   (8 AM UTC)        │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                           ┌─────────────────────┐
                           │   GoCardless API    │
                           │   Create Subscription│
                           └─────────────────────┘
```

## Database Impact

### New Fields Added
- `fallback_check_last_run` - Timestamp of last fallback check
- `fallback_attempt_count` - Number of fallback attempts
- `fallback_last_error` - Error message from last failed attempt

### Query Pattern
```sql
-- Records needing fallback processing
WHERE signing_on_fee_paid = 'Y' 
  AND mandate_authorised = 'Y' 
  AND subscription_activated != 'Y'
```

## Cost Analysis

- **Monthly Cost**: $0 (within AWS free tier)
- **EventBridge**: Free for scheduled rules
- **Lambda**: ~4 GB-seconds/month (free tier: 400,000 GB-seconds)
- **Data Transfer**: Negligible API calls

## Monitoring

### CloudWatch Metrics
- Execution count and duration
- Success/failure rates
- Error patterns and frequency

### Alerting
- Email alerts for function failures
- Slack notifications for high error rates
- Weekly summary reports

## Safety Features

### Idempotency
- Checks for existing subscriptions before creating new ones
- Safe to run multiple times on same records

### Error Handling
- Graceful failure with detailed error logging
- Automatic flagging of persistent failures
- Manual intervention workflows

### Rollback
- Emergency disable via EventBridge rule
- Data recovery procedures documented
- Minimal blast radius design

## Future Extensions

This system provides a foundation for:
- Payment failure monitoring
- Registration data quality checks
- Automated club administration tasks
- Enhanced webhook reliability

## Support

For issues or questions:
- Check CloudWatch logs for execution details
- Review Airtable records for error messages
- Contact technical support with specific record IDs

---

**Status**: Ready for immediate implementation
**Priority**: High (Registration system is live)
**Estimated Effort**: 1-2 days
**Dependencies**: AWS Lambda, EventBridge, existing GoCardless integration