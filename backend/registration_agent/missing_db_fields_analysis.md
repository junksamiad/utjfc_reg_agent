# Missing Database Fields Analysis for registrations_2526

## Current Status
This analysis compares the existing registrations_2526 table schema with the data we collect in our registration routines and the new payment architecture requirements.

## Missing Fields Required

### 1. Parent Contact Information
- **parent_telephone**: Parent's phone number (UK format: mobile 07... or Manchester landline 0161...)
- **parent_email**: Parent's email address (validated format)
- **parent_dob**: Parent's date of birth (DD-MM-YYYY format)

### 2. Communication Preferences
- **communication_consent**: Parent's consent for email/SMS club communications (Y/N)

### 3. Previous Club Information
- **previous_team_name**: Name of previous football team (if child played elsewhere last season)
- **played_elsewhere_last_season**: Whether child played for another team last season (Y/N)

### 4. U16+ Player Contact Details (Conditional)
- **player_telephone**: Player's own mobile number (required for U16+, different from parent)
- **player_email**: Player's own email address (required for U16+, different from parent)

### 5. Registration Meta Information
- **registration_type**: Type of registration (100 = re-registration, 200 = new registration)
- **season**: Season code (2526)
- **original_registration_code**: Full registration code entered by user

### 6. Payment Architecture Fields
- **billing_request_id**: GoCardless billing request ID (serves as payment token)
- **preferred_payment_day**: Day of month for monthly payments (1-31 or -1 for last day)
- **signing_on_fee_paid**: Boolean - whether £45 signing fee has been paid (Y/N)
- **mandate_authorised**: Boolean - whether Direct Debit mandate has been authorised (Y/N)
- **subscription_activated**: Boolean - whether monthly subscription is active (Y/N)
- **payment_link_sent_timestamp**: When SMS payment link was sent
- **registration_completed_timestamp**: When registration was marked complete

### 7. Additional Tracking Fields
- **routine_completion_timestamp**: When routine 29 completed and data saved to DB
- **payment_follow_up_count**: Number of follow-up reminders sent (for automation)
- **registration_status**: Current status (pending_payment, active, suspended, etc.)

## Field Types and Validation Rules

### Text Fields
- **parent_telephone**: UK phone format validation
- **parent_email**: Email format validation, lowercase
- **player_telephone**: UK mobile format validation (U16+ only)
- **player_email**: Email format validation, lowercase (U16+ only)
- **previous_team_name**: Free text (optional)
- **registration_type**: Must be "100" or "200"
- **season**: Must be "2526"
- **original_registration_code**: Store as-entered
- **billing_request_id**: GoCardless ID format
- **registration_status**: Enum values

### Date Fields
- **parent_dob**: Date format (DD-MM-YYYY)
- **payment_link_sent_timestamp**: ISO timestamp
- **registration_completed_timestamp**: ISO timestamp
- **routine_completion_timestamp**: ISO timestamp

### Boolean/Choice Fields
- **communication_consent**: Y/N
- **played_elsewhere_last_season**: Y/N
- **signing_on_fee_paid**: Y/N
- **mandate_authorised**: Y/N
- **subscription_activated**: Y/N

### Numeric Fields
- **preferred_payment_day**: Integer 1-31 or -1
- **payment_follow_up_count**: Integer (default 0)

## Implementation Priority

### Phase 1 (Immediate - Required for Routine 29)
1. Parent contact fields
2. Communication consent
3. Previous team information
4. U16+ player contact fields
5. Registration meta fields
6. Core payment architecture fields

### Phase 2 (Follow-up features)
1. Advanced tracking timestamps
2. Follow-up automation fields
3. Status management fields

## Database Schema Update Script Required
A script needs to be created to add these fields to the existing registrations_2526 table while preserving existing data. 