# Subscription Payment Logic

## Overview

This document explains the smart subscription timing logic implemented in the UTJFC registration system for GoCardless monthly subscription payments. The system automatically activates subscriptions when mandate authorization webhooks are received, using intelligent date calculations to ensure fair pricing and avoid payment timing issues.

## Key Components

### Files Involved
- `backend/registration_agent/tools/registration_tools/gocardless_payment.py` - Contains `activate_subscription()` function
- `backend/server.py` - Webhook handlers that trigger subscription activation

### Database Fields Updated
- `ongoing_subscription_id` - Main monthly subscription ID from GoCardless
- `interim_subscription_id` - Temporary subscription ID (if created)
- `subscription_start_date` - When ongoing monthly payments begin
- `subscription_status` - 'active', 'failed', or 'pending'
- `subscription_error` - Error message if subscription setup failed

## Webhook Flow

### 1. Payment Confirmed (`payments.confirmed`)
- Sets `signing_on_fee_paid = 'Y'`
- If mandate not yet authorized: `registration_status = 'incomplete'`

### 2. Mandate Active (`mandates.active`) ⭐ **SUBSCRIPTION ACTIVATION**
- Sets `mandate_authorised = 'Y'`
- Calls `activate_subscription()` function
- Updates all subscription database fields
- Creates GoCardless subscription(s) using smart timing logic

### 3. Billing Request Fulfilled (`billing_requests.fulfilled`)
- Final confirmation of complete payment flow
- Sends SMS confirmation to parent

## Smart Subscription Timing Logic

### Core Rules

The system uses a **5-day minimum buffer** (GoCardless requirement) with smart fairness logic:

1. **Early Month (≤ 10th) + Payment Too Soon (< 5 days)**
   - ✅ Create interim subscription
   - Covers remainder of current month
   - Ongoing subscription starts next month

2. **Late Month (> 10th) + Payment Too Soon (< 5 days)**
   - 🚫 Skip interim subscription (fairness)
   - Wait for next occurrence of preferred payment day
   - Prevents unfair full-month charges for partial usage

3. **Any Time + Sufficient Time (≥ 5 days)**
   - ✅ No interim needed
   - Start ongoing subscription on preferred day

### Decision Matrix

| Today's Day | Days Until Payment | Action | Reason |
|-------------|-------------------|---------|---------|
| ≤ 10th | < 5 days | Create interim | Early month, safe to charge full month |
| > 10th | < 5 days | Skip interim | Late month, unfair to charge full month |
| Any | ≥ 5 days | No interim | Sufficient time for normal start |

## Example Scenarios

### Scenario 1: Early Month Registration
- **Today:** June 8th (day 8)
- **Preferred Day:** 10th
- **Next Payment:** June 10th (2 days away)
- **Logic:** Early month + too soon → Create interim
- **Result:**
  - Interim: June 13th - June 30th (£27.50)
  - Ongoing: July 10th onwards (£27.50/month)

### Scenario 2: Late Month Registration
- **Today:** June 27th (day 27)  
- **Preferred Day:** 28th
- **Next Payment:** June 28th (1 day away)
- **Logic:** Late month + too soon → Skip interim (fairness)
- **Result:**
  - No interim subscription
  - Ongoing: June 28th onwards (£27.50/month)

### Scenario 3: Late Month with Time
- **Today:** June 20th (day 20)
- **Preferred Day:** 18th
- **Next Payment:** July 18th (28 days away)
- **Logic:** Late month + sufficient time → No interim needed
- **Result:**
  - No interim subscription
  - Ongoing: July 18th onwards (£27.50/month)

### Scenario 4: Early Month with Time
- **Today:** June 3rd (day 3)
- **Preferred Day:** 25th
- **Next Payment:** June 25th (22 days away)
- **Logic:** Early month + sufficient time → No interim needed
- **Result:**
  - No interim subscription
  - Ongoing: June 25th onwards (£27.50/month)

## Boundary Conditions

### 10th Day Boundary
- **Day 10:** Considered "early month" - will create interim if needed
- **Day 11:** Considered "late month" - will skip interim for fairness

### Month Transitions
- System handles December → January transitions correctly
- Accounts for varying month lengths (28, 30, 31 days)
- Handles invalid dates (e.g., Feb 31st → Feb 28th)

### Edge Cases
- **Last day of month (-1):** Properly calculates last day for each month
- **Leap years:** Handled automatically by Python datetime
- **Invalid dates:** Gracefully falls back to last valid day

## Benefits

### For Parents
- ✅ **Fair pricing:** No full charges for partial month usage
- ✅ **Predictable:** Consistent monthly payment on preferred day
- ✅ **No confusion:** Clear payment schedule

### For Club
- ✅ **Reliable payments:** GoCardless minimum timing requirements met
- ✅ **Automated:** No manual intervention required
- ✅ **Flexible:** Handles all registration timing scenarios

### For System
- ✅ **No double charging:** Prevents same-month interim + ongoing payments
- ✅ **Clean data:** All subscription fields populated consistently
- ✅ **Error handling:** Graceful failure with detailed logging

## Technical Implementation

### Function Signature
```python
def activate_subscription(
    mandate_id: str,
    registration_record: Dict,
    gocardless_api_key: Optional[str] = None
) -> Dict
```

### Data Sources
- All subscription data pulled from registration database record
- No hardcoded values or external data dependencies
- Uses GoCardless API for subscription creation

### API Structure
- **Ongoing subscription:** Regular monthly payments until season end
- **Interim subscription:** One-time payment for remainder of current month
- **Metadata:** Player name, team, subscription type for tracking

### Error Handling
- Failed subscriptions don't block mandate authorization
- Detailed error messages stored in `subscription_error` field
- Comprehensive logging for debugging

## Maintenance Notes

### Key Configuration
- **Buffer days:** Currently 5 days (minimum GoCardless requirement)
- **Cutoff day:** 10th of month (fairness boundary)
- **Season end:** June 1st, 2025 (update annually)

### Monitoring
- Check `subscription_status = 'failed'` records for manual follow-up
- Monitor `subscription_error` field for recurring issues
- Verify `interim_subscription_id` population during testing

### Future Considerations
- Buffer days could be adjusted based on experience
- Cutoff day (10th) could be made configurable
- Season end date should be updated annually
- Consider pro-rata calculations for micro-payments if needed
