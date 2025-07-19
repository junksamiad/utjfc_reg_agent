# ISSUE-006: GoCardless Payment Date Validation

**Priority**: High  
**Type**: Bug  
**Component**: Backend - GoCardless Integration  
**Created**: 2025-07-19  
**Status**: CLOSED (19th July 2025 - Deployed v1.6.28)  

## Executive Summary

The GoCardless subscription activation is failing for parents who enter preferred payment dates of 29, 30, or 31. GoCardless API only accepts `day_of_month` values between 1-28 or -1 (for last day of month). Our validation allows values up to 31, causing API errors when these invalid values are passed to GoCardless.

## Current Implementation

### 1. Data Model Validation (`registration_data_models.py` lines 265-270)
```python
preferred_payment_day: int = Field(
    ..., 
    ge=-1, 
    le=31,  # Allows 29, 30, 31 which GoCardless rejects
    description="Day of month for monthly payments (1-31 or -1 for last day) - validated in routine 29"
)
```

### 2. Subscription Activation (`gocardless_payment.py` lines 451-462)
```python
# Validate payment day
if preferred_payment_day != -1 and (preferred_payment_day < 1 or preferred_payment_day > 31):
    return {
        "success": False,
        "message": "Invalid preferred payment day in registration record",
        # ... error response
    }
```

### 3. API Call (`gocardless_payment.py` line 716)
```python
"day_of_month": str(preferred_payment_day) if preferred_payment_day != -1 else "-1",
```

## Problems Identified

1. **Invalid API Values**: GoCardless API only accepts:
   - Values 1-28 for specific days
   - Value -1 for last day of month
   - Values 29, 30, 31 are NOT accepted and cause API errors

2. **Validation Gap**: Our validation allows values 29-31 which will always fail at the API level

3. **User Experience**: Parents selecting days 29-31 experience failed subscriptions without clear guidance

## Proposed Solution

### Option 1: Auto-Convert to -1 (Recommended)
Convert payment days 29, 30, or 31 to -1 (last day of month) before sending to GoCardless API.

**Implementation in `gocardless_payment.py` around line 716:**
```python
# Convert days 29-31 to -1 (last day of month) for GoCardless compatibility
adjusted_payment_day = preferred_payment_day
if preferred_payment_day >= 29:
    adjusted_payment_day = -1
    print(f"📅 Converting payment day {preferred_payment_day} to -1 (last day) for GoCardless compatibility")

"day_of_month": str(adjusted_payment_day) if adjusted_payment_day != -1 else "-1",
```

### Option 2: Validation at Entry Point
Update the data model validation to prevent 29-31 from being entered:

```python
preferred_payment_day: int = Field(
    ..., 
    ge=-1, 
    le=28,  # Changed from 31 to 28
    description="Day of month for monthly payments (1-28 or -1 for last day)"
)
```

However, this would require updating the user interface and potentially re-validating existing records.

## Implementation Checklist

- [x] Update `activate_subscription()` function to convert days 29-31 to -1
- [x] Add logging to track when conversions occur
- [x] Test with sample data containing days 29, 30, 31
- [x] Verify GoCardless API accepts the converted values
- [ ] Update any user-facing documentation about payment dates
- [ ] Consider adding a note in the UI that days 29-31 will charge on last day of month

## Resolution Summary (19th July 2025)

**Fixed in**: Branch `bug-fixes`
**Files Modified**: `backend/registration_agent/tools/registration_tools/gocardless_payment.py`
**Implementation**: Option 1 (Auto-Convert to -1) - Recommended solution
**Changes Made**: 
- Added conversion logic for both ongoing and interim subscriptions
- Days 29, 30, 31 are automatically converted to -1 (last day of month)
- Added logging messages when conversions occur
- Applied fix to both `ongoing_payload` and `interim_payload` creation

**Code Changes**:
1. **Lines 709-713**: Added conversion logic for ongoing subscriptions
2. **Lines 607-611**: Added conversion logic for interim subscriptions  
3. **Lines 722 & 620**: Updated `day_of_month` parameter to use converted values

**Testing**: ✅ Verified with automated test script covering all edge cases
**Deployment**: Ready for production deployment

**Impact**: 
- Prevents GoCardless API errors for payment days 29-31
- Improves user experience for parents selecting end-of-month payment dates
- Maintains backward compatibility (existing subscriptions unaffected)

## Testing Instructions

1. Create test registrations with preferred_payment_day values:
   - 28 (should work as-is)
   - 29 (should convert to -1)
   - 30 (should convert to -1)
   - 31 (should convert to -1)
   - -1 (should work as-is)

2. Verify in logs that conversion messages appear for 29-31

3. Check GoCardless dashboard to confirm subscriptions created successfully

4. Verify subscription charges occur on correct days:
   - For -1: Last day of each month
   - For 1-28: Specified day

## Additional Context

### GoCardless API Documentation
- The `day_of_month` parameter accepts values 1-28 or -1 only
- Using -1 ensures charges on the last day regardless of month length
- This handles February (28/29 days) and months with 30/31 days automatically

### Impact
- Affects all new registrations where parents select payment days 29-31
- Does not affect existing subscriptions already created
- Prevents failed subscription activations and improves user experience

### References
- GoCardless API Reference: https://developer.gocardless.com/api-reference/
- GoCardless Subscription Guide: https://support.gocardless.com/hc/en-us/articles/360000765509