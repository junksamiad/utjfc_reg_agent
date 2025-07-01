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

## 🏈 Season Payment Policy (2025)

### Overview
**No subscription payments until September 2025** - regardless of registration date.

### Policy Rules
1. **Early Registrations (Before Aug 28, 2025)**:
   - Force subscription start to `preferred_payment_day + September 2025`
   - No interim subscriptions created
   - All players wait until September for first payment

2. **Late Registrations (Aug 28, 2025 onwards)**:
   - Use existing smart logic (naturally results in September+ dates)
   - GoCardless mandate validation applies
   - Interim subscriptions may be created if needed

### Cutoff Date Logic
- **Aug 28, 2025** chosen to avoid "free month" edge cases
- Late August registrations (Aug 29-31) with early payment days (1st-3rd) would otherwise get Sept payment pushed to Oct by GoCardless buffers
- Post-cutoff registrations use normal smart logic which naturally handles September+ start dates

### Implementation Examples

#### Early Registration Example
- **Registration Date**: July 15, 2025
- **Preferred Payment Day**: 10th
- **Policy Applied**: YES (before Aug 28)
- **Result**: Start date = September 10, 2025
- **Interim**: None created

#### Edge Case Example  
- **Registration Date**: August 25, 2025
- **Preferred Payment Day**: 31st (doesn't exist in September)
- **Policy Applied**: YES (before Aug 28)
- **Result**: Start date = September 30, 2025 (last day of September)
- **Interim**: None created

#### Late Registration Example
- **Registration Date**: August 29, 2025
- **Preferred Payment Day**: 2nd
- **Policy Applied**: NO (after Aug 28)
- **Result**: Smart logic applies - respects GoCardless `next_possible_charge_date`
- **Interim**: May be created if needed by smart logic

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

### 🆕 Season Policy Integration
The September 2025 policy is applied **after** the smart logic calculates subscription start dates but **before** GoCardless mandate validation. This ensures:

- Early registrations bypass smart logic entirely
- Late registrations still benefit from fairness logic
- All subscriptions respect GoCardless technical requirements

## Example Scenarios

### Scenario 1: Early Month Registration (Pre-Sept Policy)
- **Today:** July 8th (day 8) 
- **Preferred Day:** 10th
- **Season Policy:** Applied (before Aug 28)
- **Result:**
  - No interim subscription
  - Ongoing: September 10, 2025 onwards (£27.50/month)

### Scenario 2: Late Month Registration (Post-Sept Policy)
- **Today:** August 29th (day 29)  
- **Preferred Day:** 28th
- **Season Policy:** Not applied (after Aug 28)
- **Smart Logic:** Late month + sufficient time
- **Result:**
  - No interim subscription
  - Ongoing: September 28, 2025 onwards (£27.50/month)

### Scenario 3: Edge Case Registration (Pre-Sept Policy)
- **Today:** August 20th (day 20)
- **Preferred Day:** 31st (doesn't exist in September)
- **Season Policy:** Applied (before Aug 28)
- **Result:**
  - No interim subscription  
  - Ongoing: September 30, 2025 onwards (£27.50/month)

### Scenario 4: Late August Edge Case (Post-Sept Policy)
- **Today:** August 30th (day 30)
- **Preferred Day:** 2nd  
- **Season Policy:** Not applied (after Aug 28)
- **GoCardless Buffer:** `next_possible_charge_date` = September 5th
- **Smart Logic:** Payment too soon + late month → skip interim
- **Result:**
  - No interim subscription
  - Ongoing: September 5, 2025 onwards (£27.50/month)

## Boundary Conditions

### 10th Day Boundary
- **Day 10:** Considered "early month" - will create interim if needed
- **Day 11:** Considered "late month" - will skip interim for fairness

### August 28th Cutoff
- **August 27th:** September policy applies - force September start
- **August 28th:** Smart logic applies - natural September+ dates

### Month Transitions
- System handles December → January transitions correctly
- Accounts for varying month lengths (28, 30, 31 days)
- Handles invalid dates (e.g., Feb 31st → Feb 28th, Sept 31st → Sept 30th)

### Edge Cases
- **Last day of month (-1):** Properly calculates last day for each month
- **Leap years:** Handled automatically by Python datetime
- **Invalid dates:** Gracefully falls back to last valid day

## Benefits

### For Parents
- ✅ **Fair pricing:** No full charges for partial month usage
- ✅ **Predictable:** Consistent monthly payment on preferred day
- ✅ **No confusion:** Clear payment schedule
- ✅ **Season alignment:** No payments until season starts (September)

### For Club
- ✅ **Reliable payments:** GoCardless minimum timing requirements met
- ✅ **Automated:** No manual intervention required
- ✅ **Flexible:** Handles all registration timing scenarios
- ✅ **Cash flow:** Predictable September start for all subscriptions

### For System
- ✅ **No double charging:** Prevents same-month interim + ongoing payments
- ✅ **Clean data:** All subscription fields populated consistently
- ✅ **Error handling:** Graceful failure with detailed logging
- ✅ **Policy compliance:** Enforces club payment policies automatically

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
- **Interim subscription:** One-time payment for remainder of current month (disabled for early registrations)
- **Metadata:** Player name, team, subscription type for tracking

### Error Handling
- Failed subscriptions don't block mandate authorization
- Detailed error messages stored in `subscription_error` field
- Comprehensive logging for debugging

## Maintenance Notes

### Key Configuration
- **Buffer days:** Currently 5 days (minimum GoCardless requirement)
- **Cutoff day:** 10th of month (fairness boundary)
- **Season cutoff:** August 28, 2025 (policy boundary)
- **Season end:** June 1st, 2026 (update annually)

### Monitoring
- Check `subscription_status = 'failed'` records for manual follow-up
- Monitor `subscription_error` field for recurring issues
- Verify `interim_subscription_id` population during testing
- Confirm September policy application in logs

### Future Considerations
- Buffer days could be adjusted based on experience
- Cutoff day (10th) could be made configurable
- Season policy cutoff date should be reviewed annually
- Season end date should be updated annually
- Consider pro-rata calculations for micro-payments if needed

### Annual Updates Required
- **Season end date:** Update to following year's June 1st
- **Policy cutoff:** Review August cutoff date for next season
- **Payment amounts:** Update production vs test amounts as needed
