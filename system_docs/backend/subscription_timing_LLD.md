# Subscription Timing Logic Low-Level Design (LLD)
## UTJFC Smart Payment Scheduling & Season Policies

### Table of Contents
1. [Subscription Timing Overview](#subscription-timing-overview)
2. [September 2025 Season Policy](#september-2025-season-policy)
3. [Smart Timing Logic](#smart-timing-logic)
4. [Interim Subscription Handling](#interim-subscription-handling)
5. [Implementation Details](#implementation-details)
6. [Decision Matrix & Examples](#decision-matrix--examples)
7. [Boundary Conditions](#boundary-conditions)
8. [Database Schema Integration](#database-schema-integration)
9. [Error Handling & Monitoring](#error-handling--monitoring)

---

## Subscription Timing Overview

### Purpose
The UTJFC subscription system implements sophisticated timing logic to ensure fair pricing, avoid payment issues, and align with club policies. The system automatically calculates optimal subscription start dates based on registration timing, preferred payment days, and business rules.

### Core Components
- **Season Policy Engine**: Enforces "no payments until September 2025" rule
- **Smart Timing Logic**: Prevents unfair partial-month charges
- **Interim Subscription Handler**: Manages pro-rata payments when needed
- **GoCardless Integration**: Respects 5-day minimum payment buffer requirements

### Implementation Location
- **Primary Function**: `activate_subscription()` in `gocardless_payment.py:332-822`
- **Webhook Trigger**: Called during `mandates.active` webhook processing
- **Database Updates**: Multiple subscription-related fields updated

---

## September 2025 Season Policy

### Policy Overview
**No subscription payments until September 2025** - regardless of registration date.

This ensures all players start monthly payments when the football season begins, preventing confusion and aligning cash flow with the club's operational calendar.

### Implementation (`gocardless_payment.py:660-700`)

#### Policy Cutoff Date
```python
# 🏈 SEASON POLICY: No subscription payments until September 2025
cutoff_date = datetime(2025, 8, 28)  # Aug 28, 2025
september_policy_applies = today < cutoff_date

if september_policy_applies:
    # Force subscription to start in September 2025 on preferred payment day
    september_start = datetime(2025, 9, preferred_payment_day)
    print(f"🏈 Season policy: Registration before Aug 28 - forcing start date to September 2025")
```

#### Policy Rules

##### 1. Early Registrations (Before August 28, 2025)
- **Action**: Force subscription start to September 2025
- **No Interim**: No partial-month charges created
- **Start Date**: `preferred_payment_day` in September 2025
- **Rationale**: All players wait until season starts

##### 2. Late Registrations (August 28, 2025 onwards)
- **Action**: Use smart timing logic (naturally results in September+ dates)
- **GoCardless Rules**: 5-day minimum buffer still applies
- **Interim Logic**: May create interim subscriptions if smart logic determines fairness
- **Rationale**: Close to season start, normal logic applies

### Date Selection Rationale

#### Why August 28th?
```python
# Chosen to avoid "free month" edge cases
# Late August registrations (Aug 29-31) with early payment days (1st-3rd) 
# would get September payment pushed to October by GoCardless 5-day buffer
```

**Example Edge Case Avoided**:
- **Registration**: August 30th
- **Preferred Day**: 2nd  
- **Without Policy**: September 2nd payment gets pushed to October 2nd (5-day buffer)
- **With Policy**: August 30th is after cutoff, so smart logic applies naturally

### Policy Application Examples

#### Example 1: Early Summer Registration
```python
registration_date = datetime(2025, 7, 15)  # July 15
preferred_payment_day = 10
september_policy_applies = True  # Before Aug 28

# Result:
subscription_start = datetime(2025, 9, 10)  # September 10, 2025
interim_subscription = None  # No interim created
```

#### Example 2: Invalid September Date Handling
```python
registration_date = datetime(2025, 8, 20)  # August 20  
preferred_payment_day = 31  # September has only 30 days
september_policy_applies = True  # Before Aug 28

# Result:
subscription_start = datetime(2025, 9, 30)  # September 30, 2025 (last day)
interim_subscription = None  # No interim created
```

---

## Smart Timing Logic

### Core Principles

The smart timing system prevents unfair charging scenarios while respecting GoCardless technical requirements:

1. **5-Day Buffer Rule**: GoCardless requires minimum 5 days between mandate authorization and first payment
2. **Fairness Principle**: Avoid charging full month for partial usage
3. **Predictability**: Maintain consistent payment schedules

### Decision Algorithm (`gocardless_payment.py:530-643`)

#### Step 1: Calculate Next Payment Occurrence
```python
# Calculate next occurrence of preferred payment day
today = datetime.now()
current_month = today.month
current_year = today.year

if preferred_payment_day == -1:
    # Last day of current month
    next_occurrence = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
else:
    # Try preferred day in current month
    try:
        next_occurrence = datetime(current_year, current_month, preferred_payment_day)
        if next_occurrence <= today:
            # Already passed this month, move to next month
            next_occurrence = datetime(current_year, current_month + 1, preferred_payment_day)
    except ValueError:
        # Invalid date (e.g., Feb 31), use last day of month
        next_occurrence = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
```

#### Step 2: Apply Fairness Logic
```python
days_until_next = (next_occurrence - today).days

# Smart logic: Don't create interim if we're late in month AND payment is soon
late_in_month = today.day > 10
payment_too_soon = days_until_next < 5

if payment_too_soon and not late_in_month:
    # Early in month + payment soon = create interim subscription
    print(f"⏰ Next payment day is too soon. Creating interim subscription...")
    create_interim = True
elif payment_too_soon and late_in_month:
    # Late in month + payment soon = skip interim (fairness)
    print(f"📅 Late in month ({today.day}) and payment soon - skipping interim for fairness")
    create_interim = False
else:
    # Sufficient time for normal start
    create_interim = False
```

### Decision Matrix

| Today's Day | Days Until Payment | Action | Reason |
|-------------|-------------------|---------|---------|
| ≤ 10th | < 5 days | Create interim | Early month, fair to charge full month |
| > 10th | < 5 days | Skip interim | Late month, unfair to charge full month |
| Any | ≥ 5 days | No interim | Sufficient time for normal start |

### Timing Logic Examples

#### Scenario 1: Early Month, Payment Soon
```python
today = datetime(2025, 8, 29, day=8)  # 8th of month
preferred_payment_day = 10
days_until_next = 2  # Payment in 2 days

# Decision:
late_in_month = False  # Day 8 ≤ 10
payment_too_soon = True  # 2 days < 5
create_interim = True

# Result: 
# - Interim subscription: Aug 29 - Aug 31 (3 days pro-rata)
# - Ongoing subscription: September 10 onwards (full months)
```

#### Scenario 2: Late Month, Payment Soon
```python
today = datetime(2025, 8, 29, day=27)  # 27th of month
preferred_payment_day = 30
days_until_next = 3  # Payment in 3 days

# Decision:
late_in_month = True   # Day 27 > 10
payment_too_soon = True  # 3 days < 5
create_interim = False  # Skip for fairness

# Result:
# - No interim subscription
# - Ongoing subscription: September 30 onwards (wait for next occurrence)
```

---

## Interim Subscription Handling

### Interim Subscription Purpose
Interim subscriptions handle partial-month charges when it's fair to do so, ensuring parents don't get charged full month rates for a few days of service.

### Implementation Logic (`gocardless_payment.py:582-643`)

#### Interim Creation Conditions
```python
if create_interim:
    # Create interim subscription for the immediate month
    interim_start = today + timedelta(days=5)  # Respect GoCardless buffer
    interim_start_date = interim_start.strftime("%Y-%m-%d")
    
    # Calculate interim end date (end of current month)
    last_day_current_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).day
    interim_end = datetime(current_year, current_month, last_day_current_month)
    interim_end_date = interim_end.strftime("%Y-%m-%d")
    
    print(f"📅 Creating interim subscription: {interim_start_date} to {interim_end_date}")
```

#### Interim Subscription Configuration
```python
interim_subscription_data = {
    "amount": monthly_amount_pence,  # Full monthly amount
    "currency": "GBP",
    "name": f"UTJFC Interim Subscription - {player_name}",
    "interval_unit": "monthly",
    "count": 1,  # One-time payment
    "links": {
        "mandate": mandate_id
    },
    "metadata": {
        "subscription_type": "interim",
        "player_name": player_name,
        "team": team,
        "start_date": interim_start_date,
        "end_date": interim_end_date
    }
}
```

### Database Integration

#### Interim Subscription Fields
```python
# Database fields updated for interim subscriptions
update_data = {
    "interim_subscription_id": interim_subscription["id"],
    "interim_start_date": interim_start_date,
    "interim_end_date": interim_end_date,
    "interim_amount_pounds": monthly_amount
}
```

#### Ongoing Subscription Configuration
```python
# Main subscription starts after interim period
ongoing_start = datetime(current_year, current_month + 1, preferred_payment_day)
ongoing_start_date = ongoing_start.strftime("%Y-%m-%d")

ongoing_subscription_data = {
    "amount": monthly_amount_pence,
    "currency": "GBP", 
    "name": f"UTJFC Monthly Subscription - {player_name}",
    "interval_unit": "monthly",
    "day_of_month": preferred_payment_day if preferred_payment_day != -1 else None,
    "start_date": ongoing_start_date,
    "end_date": "2026-05-31",  # End of season
    "links": {
        "mandate": mandate_id
    }
}
```

---

## Implementation Details

### Function Flow (`activate_subscription()`)

#### 1. Data Extraction and Validation
```python
def activate_subscription(mandate_id: str, registration_record: Dict, gocardless_api_key: Optional[str] = None) -> Dict:
    # Extract registration data
    fields = registration_record.get('fields', {})
    player_name = f"{fields.get('player_first_name', '')} {fields.get('player_last_name', '')}"
    team = fields.get('team', 'Unknown')
    monthly_amount = float(fields.get('monthly_subscription_amount', 27.50))
    preferred_payment_day = int(fields.get('preferred_payment_day', 1))
```

#### 2. Sibling Discount Application
```python
# 🎉 SIBLING DISCOUNT LOGIC: Check for existing siblings
parent_full_name = fields.get('parent_full_name', '')
if parent_full_name and player_last_name:
    sibling_query = f"AND({{parent_full_name}} = '{parent_full_name}', {{player_last_name}} = '{player_last_name}', {{billing_request_id}} != '{billing_request_id}')"
    existing_siblings = table.all(formula=sibling_query)
    
    if len(existing_siblings) > 0:
        original_amount = monthly_amount
        monthly_amount = monthly_amount * 0.9  # Apply 10% sibling discount
        print(f"🎉 SIBLING DISCOUNT APPLIED: Parent '{parent_full_name}' has {len(existing_siblings)} existing child(ren)")
```

#### 3. Smart Date Calculation
```python
# Step 1: Calculate smart subscription start date
today = datetime.now()

# Step 2: Apply September 2025 policy if applicable
september_policy_applies = today < datetime(2025, 8, 28)

if september_policy_applies:
    subscription_start_date = datetime(2025, 9, preferred_payment_day)
    create_interim = False  # No interim for early registrations
else:
    # Apply smart timing logic
    subscription_start_date, create_interim = calculate_smart_start_date(today, preferred_payment_day)
```

#### 4. Subscription Creation
```python
# Step 3: Create interim subscription if needed
if create_interim:
    interim_result = create_interim_subscription(mandate_id, monthly_amount, player_name, team)
    
# Step 4: Create ongoing subscription
ongoing_result = create_ongoing_subscription(
    mandate_id, 
    monthly_amount, 
    preferred_payment_day,
    subscription_start_date,
    player_name,
    team
)
```

#### 5. Database Updates
```python
# Step 5: Update database with all subscription information
update_data = {
    "ongoing_subscription_id": ongoing_subscription["id"],
    "subscription_start_date": subscription_start_date.strftime("%Y-%m-%d"),
    "subscription_status": "active",
    "subscription_activated": "Y",
    "monthly_subscription_amount": monthly_amount
}

if create_interim and interim_subscription:
    update_data.update({
        "interim_subscription_id": interim_subscription["id"],
        "interim_start_date": interim_start_date,
        "interim_end_date": interim_end_date
    })

table.update(record_id, update_data)
```

---

## Decision Matrix & Examples

### Complete Scenario Matrix

#### Scenario 1: Early Registration + Early Month
```python
registration_date = datetime(2025, 7, 8)  # July 8th
preferred_payment_day = 10
september_policy = True  # Before Aug 28

# Result:
subscription_start = datetime(2025, 9, 10)  # September 10, 2025
interim_subscription = None
reasoning = "Season policy overrides smart logic"
```

#### Scenario 2: Late Registration + Early Month + Payment Soon
```python
registration_date = datetime(2025, 8, 29)  # August 29th (after cutoff)
today_day = 8  # 8th of month
preferred_payment_day = 10
days_until = 2  # Payment in 2 days

# Smart Logic:
september_policy = False  # After Aug 28
late_in_month = False  # Day 8 ≤ 10
payment_too_soon = True  # 2 days < 5
create_interim = True

# Result:
interim_subscription = {
    "start": "2025-09-03",  # 5 days from today
    "end": "2025-09-30",
    "amount": 27.50
}
ongoing_subscription = {
    "start": "2025-10-10",  # Next month on preferred day
    "amount": 27.50
}
```

#### Scenario 3: Late Registration + Late Month + Payment Soon
```python
registration_date = datetime(2025, 8, 29)  # August 29th
today_day = 27  # 27th of month
preferred_payment_day = 30
days_until = 3  # Payment in 3 days

# Smart Logic:
september_policy = False  # After Aug 28
late_in_month = True   # Day 27 > 10
payment_too_soon = True  # 3 days < 5
create_interim = False  # Skip for fairness

# Result:
interim_subscription = None
ongoing_subscription = {
    "start": "2025-09-30",  # Wait for next occurrence
    "amount": 27.50
}
reasoning = "Late month + payment soon = unfair to charge full month"
```

#### Scenario 4: Invalid Date Handling
```python
registration_date = datetime(2025, 8, 20)
preferred_payment_day = 31  # September only has 30 days
september_policy = True

# Date Correction:
try:
    subscription_start = datetime(2025, 9, 31)  # Invalid
except ValueError:
    subscription_start = datetime(2025, 9, 30)  # Use last day of month

# Result:
subscription_start = datetime(2025, 9, 30)  # September 30, 2025
interim_subscription = None
```

---

## Boundary Conditions

### Critical Boundary Dates

#### 1. 10th Day Boundary (Fairness)
```python
fairness_boundary = 10

# Day 10: Considered "early month"
if today.day <= fairness_boundary:
    # Will create interim if payment too soon
    considered_early_month = True
    
# Day 11: Considered "late month"  
if today.day > fairness_boundary:
    # Will skip interim for fairness
    considered_late_month = True
```

#### 2. August 28th Cutoff (Season Policy)
```python
season_cutoff = datetime(2025, 8, 28)

# August 27th: September policy applies
if registration_date < season_cutoff:
    force_september_start = True
    
# August 28th: Smart logic applies
if registration_date >= season_cutoff:
    use_smart_logic = True
```

#### 3. 5-Day Buffer (GoCardless Requirement)
```python
gocardless_buffer = 5  # days

if days_until_payment < gocardless_buffer:
    payment_too_soon = True
    # Triggers interim creation logic or date pushing
```

### Month Transition Handling

#### December → January Transition
```python
def handle_year_transition(current_date, preferred_day):
    if current_date.month == 12:
        # Calculate next occurrence in January
        next_year = current_date.year + 1
        next_occurrence = datetime(next_year, 1, preferred_day)
    return next_occurrence
```

#### Invalid Date Correction
```python
def get_valid_payment_date(year, month, preferred_day):
    try:
        return datetime(year, month, preferred_day)
    except ValueError:
        # Handle invalid dates (e.g., Feb 31, Sept 31)
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day)
```

#### Last Day of Month (-1) Handling
```python
def handle_last_day_preference(year, month):
    if preferred_payment_day == -1:
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day)
```

---

## Database Schema Integration

### Subscription-Related Fields

#### Core Subscription Fields
```python
subscription_fields = {
    "ongoing_subscription_id": str,        # GoCardless subscription ID
    "subscription_start_date": str,        # YYYY-MM-DD format
    "subscription_status": str,            # 'active', 'failed', 'pending'
    "subscription_activated": str,         # Y/N
    "subscription_error": str,             # Error message if failed
    "monthly_subscription_amount": float,  # With sibling discounts
    "preferred_payment_day": int,          # 1-28 or -1 for last day
}
```

#### Interim Subscription Fields
```python
interim_fields = {
    "interim_subscription_id": str,        # GoCardless interim subscription ID
    "interim_start_date": str,             # YYYY-MM-DD format
    "interim_end_date": str,               # YYYY-MM-DD format
    "interim_amount_pounds": float,        # Usually same as monthly amount
}
```

#### Sibling Discount Tracking
```python
discount_fields = {
    "sibling_discount_applied": str,       # Y/N
    "original_monthly_amount": float,      # Before discount (£27.50)
    "discounted_monthly_amount": float,    # After discount (£24.75)
    "sibling_count": int,                  # Number of existing siblings found
}
```

### Database Update Sequence

#### 1. Initial Subscription Activation
```python
update_data = {
    "subscription_status": "processing",
    "subscription_activated": "N",
    "subscription_start_calculation": datetime.now().isoformat()
}
table.update(record_id, update_data)
```

#### 2. Successful Subscription Creation
```python
success_data = {
    "ongoing_subscription_id": subscription["id"],
    "subscription_start_date": start_date.strftime("%Y-%m-%d"),
    "subscription_status": "active",
    "subscription_activated": "Y",
    "monthly_subscription_amount": final_amount,
    "subscription_created_at": datetime.now().isoformat()
}

if interim_created:
    success_data.update({
        "interim_subscription_id": interim["id"],
        "interim_start_date": interim_start.strftime("%Y-%m-%d"),
        "interim_end_date": interim_end.strftime("%Y-%m-%d")
    })

table.update(record_id, success_data)
```

#### 3. Error Handling
```python
error_data = {
    "subscription_status": "failed",
    "subscription_error": str(error),
    "subscription_failed_at": datetime.now().isoformat()
}
table.update(record_id, error_data)
```

---

## Error Handling & Monitoring

### Error Categories

#### 1. GoCardless API Errors
```python
try:
    subscription = gocardless_client.subscriptions.create(subscription_data)
except Exception as e:
    error_details = {
        "error_type": "gocardless_api_error",
        "error_message": str(e),
        "subscription_data": subscription_data,
        "mandate_id": mandate_id
    }
    print(f"❌ GoCardless subscription creation failed: {e}")
    return {"success": False, "error": error_details}
```

#### 2. Date Calculation Errors
```python
try:
    subscription_start = calculate_smart_start_date(today, preferred_payment_day)
except Exception as e:
    error_details = {
        "error_type": "date_calculation_error",
        "today": today.isoformat(),
        "preferred_day": preferred_payment_day,
        "error_message": str(e)
    }
    print(f"❌ Date calculation failed: {e}")
    return {"success": False, "error": error_details}
```

#### 3. Database Update Errors
```python
try:
    table.update(record_id, update_data)
except Exception as e:
    error_details = {
        "error_type": "database_update_error",
        "record_id": record_id,
        "update_data": update_data,
        "error_message": str(e)
    }
    print(f"❌ Database update failed: {e}")
    # Subscription created but database not updated - requires manual intervention
```

### Monitoring & Alerting

#### Key Metrics to Monitor
```python
monitoring_metrics = {
    "subscription_success_rate": "Percentage of successful subscription activations",
    "interim_creation_rate": "Percentage of registrations requiring interim subscriptions",
    "september_policy_applications": "Count of early registrations affected by season policy",
    "average_subscription_start_delay": "Days between registration and first payment",
    "sibling_discount_applications": "Count and percentage of sibling discounts applied"
}
```

#### Alert Conditions
```python
alert_conditions = {
    "subscription_failure_rate_high": "subscription_success_rate < 95%",
    "unexpected_interim_creation": "interim_creation_rate > 30%",
    "date_calculation_errors": "Any date calculation exceptions",
    "database_update_failures": "Any database update failures after subscription creation"
}
```

#### Logging for Debugging
```python
def log_subscription_decision(registration_data, decision_data):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "registration_id": registration_data.get("id"),
        "player_name": f"{registration_data.get('player_first_name')} {registration_data.get('player_last_name')}",
        "preferred_payment_day": registration_data.get("preferred_payment_day"),
        "registration_date": registration_data.get("created_date"),
        "september_policy_applied": decision_data.get("september_policy_applied"),
        "create_interim": decision_data.get("create_interim"),
        "subscription_start_date": decision_data.get("subscription_start_date"),
        "reasoning": decision_data.get("reasoning")
    }
    print(f"📊 Subscription Decision Log: {json.dumps(log_entry, indent=2)}")
```

---

## Maintenance & Configuration

### Annual Updates Required

#### 1. Season End Date
```python
# Update annually for next season
SEASON_END_DATE = "2026-05-31"  # Update to 2027-05-31 for next season
```

#### 2. Season Policy Cutoff
```python
# Review and update for next season
SEASON_CUTOFF_DATE = datetime(2025, 8, 28)  # Update to 2026 dates
```

#### 3. Payment Amounts
```python
# Review annually for price changes
DEFAULT_MONTHLY_AMOUNT = 27.50  # Update if club changes fees
SIBLING_DISCOUNT_RATE = 0.9     # 10% discount, review if policy changes
```

### Configuration Parameters

#### Tunable Parameters
```python
configuration = {
    "gocardless_buffer_days": 5,          # Minimum days before first payment
    "fairness_boundary_day": 10,          # Early/late month boundary
    "sibling_discount_rate": 0.9,         # 10% discount for siblings
    "season_start_month": 9,              # September start for subscriptions
    "season_end_date": "2026-05-31",     # End of football season
    "interim_creation_enabled": True,     # Enable/disable interim subscriptions
}
```

#### Performance Monitoring
```python
def get_subscription_performance_stats():
    """Generate performance statistics for subscription system"""
    stats = {
        "total_activations": get_total_subscription_activations(),
        "success_rate": calculate_subscription_success_rate(),
        "average_start_delay": calculate_average_start_delay(),
        "interim_usage_rate": calculate_interim_usage_rate(),
        "september_policy_usage": calculate_september_policy_usage()
    }
    return stats
```

---

## Conclusion

The UTJFC subscription timing system represents a sophisticated balance between business requirements, user fairness, and technical constraints. The implementation ensures that:

### Business Benefits
- **Aligned Cash Flow**: All subscriptions start in September when the season begins
- **Fair Pricing**: No full-month charges for partial usage
- **Predictable Payments**: Consistent monthly payment dates
- **Automated Discounts**: Sibling discounts applied automatically

### Technical Excellence
- **GoCardless Compliance**: Respects all API requirements and constraints
- **Error Resilience**: Comprehensive error handling and recovery
- **Monitoring Support**: Detailed logging and metrics for operational visibility
- **Maintenance Friendly**: Clear configuration parameters and annual update requirements

### User Experience
- **Transparency**: Clear payment schedules and timing
- **Fairness**: No unexpected charges or unfair partial-month billing
- **Consistency**: Reliable payment dates aligned with user preferences
- **Flexibility**: Accommodates various registration timing scenarios

The system successfully handles the complex intersection of user preferences, business policies, and payment processor constraints while maintaining fairness and predictability for all stakeholders.