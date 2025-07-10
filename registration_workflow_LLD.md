# UTJFC Registration Agent - 35-Step Workflow Low-Level Design

## Document Overview

This document provides a comprehensive Low-Level Design (LLD) analysis of the UTJFC Registration Agent's 35-step new player registration workflow. It details the complete business logic, routing decisions, tool integrations, validation rules, and branching paths that govern the registration process.

## Table of Contents

1. [Workflow Architecture Overview](#workflow-architecture-overview)
2. [Registration Code Routing](#registration-code-routing)
3. [35-Step Workflow Breakdown](#35-step-workflow-breakdown)
4. [Age-Based Routing Logic (Routine 22)](#age-based-routing-logic-routine-22)
5. [Business Rules Implementation](#business-rules-implementation)
6. [Tool Integration Matrix](#tool-integration-matrix)
7. [Data Flow and State Management](#data-flow-and-state-management)
8. [Error Handling and Retry Mechanisms](#error-handling-and-retry-mechanisms)
9. [Special Workflows and Edge Cases](#special-workflows-and-edge-cases)

## Workflow Architecture Overview

### Agent System Architecture

The registration system uses a sophisticated AI agent architecture built on OpenAI's GPT-4.1 model with structured outputs. The workflow is managed through:

- **Dynamic Instruction Injection**: Each routine step injects specific task instructions into the agent's system prompt
- **Structured Response Schema**: All responses follow a consistent JSON format with `agent_final_response` and `routine_number` fields
- **Tool Integration**: 14+ specialized tools for validation, payment processing, and database operations
- **Retry Logic**: Exponential backoff for AI call failures with up to 3 retry attempts
- **Session Context Management**: Persistent conversation history with structured data injection

### Registration Flow Types

1. **New Registration (200-series codes)**: Complete 35-step onboarding workflow
2. **Re-registration (100-series codes)**: Simplified flow for returning players
3. **Age-based Branching**: Different paths for U16+ vs younger players

## Registration Code Routing

### Code Format Validation

Registration codes follow the pattern: `[PREFIX]-[TEAM]-[AGE_GROUP]-[SEASON][-PLAYER_NAME]`

- **PREFIX**: `200` (new players) or `100` (returning players)
- **TEAM**: Team name (case-insensitive, e.g., "tigers", "eagles")
- **AGE_GROUP**: Format `u##` (e.g., "u10", "u16")
- **SEASON**: Must be `2526` (current season 2025-26)
- **PLAYER_NAME**: Required for 100-series codes only (`FirstName-Surname`)

### Validation Process

1. **Regex Pattern Matching**: `^(100|200)-([A-Za-z0-9_]+)-([Uu]\d+)-(2526)(?:-([A-Za-z]+)-([A-Za-z]+))?$`
2. **Team/Age Group Verification**: Cross-reference against Airtable `team_info` table
3. **Player Lookup**: For 100-series codes, verify player exists in database
4. **Structured Data Injection**: Parse code components into session context

## 35-Step Workflow Breakdown

### Phase 1: Basic Information Collection (Routines 1-11)

#### Routine 1: Parent Name Collection
- **Purpose**: Capture parent's first and last name
- **Validation**: 
  - Must contain only letters, apostrophes, hyphens, and spaces
  - Convert curly apostrophes to straight apostrophes
  - Minimum 2 words required
- **Next Step**: Routine 2 (child's name)
- **Tools Used**: None (internal validation)

#### Routine 2: Child Name Collection
- **Purpose**: Capture child's first and last name
- **Validation**: Same rules as parent name validation
- **Next Step**: Routine 3 (date of birth)
- **Business Rule**: Parent referred to by first name only from this point

#### Routine 3: Child Date of Birth
- **Purpose**: Capture and validate child's DOB
- **Validation**:
  - Accept multiple date formats (DD/MM/YYYY, MM/DD/YYYY, etc.)
  - Convert to standard DD-MM-YYYY format
  - Birth year must be 2007 or later (club rule)
  - Cannot be future date
- **Age Group Calculation**: Birth year determines age group (automatic)
- **Next Step**: Routine 4 (gender)
- **Tools Used**: `child_dob_validation`

#### Routine 4: Child Gender
- **Purpose**: Capture child's gender
- **Validation**: Normalize to 'Male', 'Female', or 'Not disclosed'
- **Accepted Variations**: 'boy/girl', 'man/woman', 'prefer not to say'
- **Next Step**: Routine 5 (medical issues)

#### Routine 5: Medical Issues Assessment
- **Purpose**: Identify any medical conditions
- **Process**:
  1. Yes/No question about medical issues
  2. If Yes: Collect details and format as comma-separated list
  3. **CRITICAL**: If serious conditions mentioned (allergies requiring EpiPen, asthma inhaler, diabetes, epilepsy, heart conditions), ask follow-up about practical information
- **Business Rule**: Keep questions simple, don't dig deep - parent remains responsible
- **Next Step**: Routine 6 (previous club history)

#### Routine 6: Previous Club History
- **Purpose**: Determine if child played for Urmston Town last season
- **Process**:
  1. Ask if played for Urmston Town in 2024-25
  2. If No: Ask if played elsewhere and capture team name
- **Business Impact**: Affects kit requirement logic later
- **Next Step**: Routine 7 (relationship)

#### Routine 7: Parent Relationship
- **Purpose**: Capture parent's relationship to child
- **Validation**: Normalize to exact values: 'Mother', 'Father', 'Guardian', 'Other'
- **Accepted Variations**: 
  - 'mum/mam/mom' → 'Mother'
  - 'dad/daddy' → 'Father'
  - 'gran/grandma/granny/grandfather/grandad' → 'Other'
- **Next Step**: Routine 8 (mobile number)

#### Routine 8: Parent Mobile Number
- **Purpose**: Capture UK mobile number for SMS payment links
- **Validation**:
  - Must start with 07
  - Exactly 11 digits
  - Remove spaces, dashes, brackets
- **Business Requirement**: MUST be mobile (not landline) for SMS functionality
- **Next Step**: Routine 9 (email)

#### Routine 9: Parent Email
- **Purpose**: Capture parent's email address
- **Validation**:
  - Must contain exactly one @ symbol
  - At least one dot after @
  - Convert to lowercase
- **Next Step**: Routine 10 (communication consent)

#### Routine 10: Communication Consent
- **Purpose**: Get consent for club communications
- **Validation**: Normalize Yes/No responses
- **Scope**: Covers general club communications throughout season
- **Next Step**: Routine 11 (parent DOB)

#### Routine 11: Parent Date of Birth
- **Purpose**: Capture parent's DOB for records
- **Validation**:
  - Accept multiple formats, convert to DD-MM-YYYY
  - Must be reasonable (not future, not before 1900)
- **Next Step**: Routine 12 (postcode)

### Phase 2: Address Collection (Routines 12-21)

#### Routine 12: Parent Postcode
- **Purpose**: Capture parent's UK postcode
- **Validation**: Clean (remove spaces, uppercase) and validate UK format
- **Next Step**: Routine 13 (house number)
- **Tools Used**: `address_validation`

#### Routine 13: Parent House Number + Address Lookup
- **Purpose**: Get house number and attempt automatic address lookup
- **Process**:
  1. Accept any format (12a, 5B, Flat 2, etc.)
  2. Use `address_lookup` tool with postcode + house number
  3. If successful: Show formatted address → Routine 15
  4. If failed: Request manual entry → Routine 14
- **Tools Used**: `address_lookup`

#### Routine 14: Manual Address Entry
- **Purpose**: Fallback for failed address lookup
- **Validation**:
  - Visual check for UK address format
  - Must include house number/name, street, area/town, UK postcode
  - Check for Manchester/Stretford/Urmston area or recognizable UK location
- **Next Step**: Routine 15 (address confirmation)

#### Routine 15: Address Confirmation
- **Purpose**: Confirm displayed address is correct
- **Process**:
  - If No/wrong: Return to Routine 14 (manual entry)
  - If Yes/correct: Proceed to Routine 16
- **Next Step**: Routine 16 (child address check)

#### Routine 16: Child Address Assessment
- **Purpose**: Determine if child lives at same address as parent
- **Critical Routing**:
  - If **Yes**: Jump to **Routine 22** (age-based routing) - **DO NOT ask question**
  - If **No**: Continue to Routine 18 (child address collection)
- **Business Rule**: Skip routines 17-21 if same address

#### Routines 18-21: Child Address Collection (Mirror of Parent Address)
- **Routine 18**: Child postcode validation
- **Routine 19**: Child house number + address lookup
- **Routine 20**: Child manual address entry (if lookup fails)
- **Routine 21**: Child address confirmation
- **End Point**: All paths lead to **Routine 22**

### Phase 3: Age-Based Routing Hub (Routine 22)

#### Routine 22: Critical Age-Based Decision Point
- **Purpose**: Determine workflow path based on child's age
- **Process**:
  1. Extract age group from conversation history system messages
  2. **If U16 or above**: Route to Routine 23 (child contact details)
  3. **If under U16**: Route to Routine 28 (data confirmation)

#### Age Group Determination Logic
```javascript
// Age group calculation from birth year
// Current season: 2025-26
// Age groups based on age at start of season (September 1, 2025)

Birth Year | Age on Sept 1, 2025 | Age Group
2007       | 18                   | U18s
2008       | 17                   | U17s  
2009       | 16                   | U16s
2010       | 15                   | U15s
2011       | 14                   | U14s
2012       | 13                   | U13s
2013       | 12                   | U12s
2014       | 11                   | U11s
2015       | 10                   | U10s
2016       | 9                    | U9s
2017       | 8                    | U8s
2018       | 7                    | U7s
```

### Phase 4A: U16+ Contact Details (Routines 23-24)

#### Routine 23: Child Mobile Number (U16+ Only)
- **Purpose**: Collect child's own mobile number (different from parent's)
- **Validation**:
  - UK mobile format (07, 11 digits)
  - Must be different from parent's number
- **Business Rule**: U16+ players need independent contact details
- **Next Step**: Routine 24

#### Routine 24: Child Email (U16+ Only)
- **Purpose**: Collect child's email address
- **Validation**:
  - Proper email format
  - Must be different from parent's email
- **Next Step**: Routine 28 (data confirmation)

### Phase 4B: Universal Data Confirmation (Routine 28)

#### Routine 28: Complete Data Review
- **Purpose**: Present all collected information for confirmation
- **Process**:
  1. Display validated data (not raw responses)
  2. If corrections needed: Stay on Routine 28, collect changes
  3. If confirmed: Proceed to payment setup
- **Data Display**: Show normalized/validated values, not original user input
- **Next Step**: Routine 29 (payment day selection)

### Phase 5: Payment Processing (Routines 29-30)

#### Routine 29: Payment Day Selection
- **Purpose**: Collect preferred monthly payment day
- **Options**:
  - Any day 1-31
  - Last day of month (recorded as -1 for GoCardless)
- **Process**:
  1. Collect valid payment day
  2. Call `create_payment_token` → Creates GoCardless billing request
  3. Call `update_reg_details_to_db` → Save all registration data
  4. **Automatic SMS Trigger**: Payment link sent via SMS
- **Tools Used**: `create_payment_token`, `update_reg_details_to_db`
- **Next Step**: Routine 30

#### Routine 30: Payment Link Confirmation + Kit Routing
- **Purpose**: Confirm SMS receipt and determine kit requirements
- **Process**:
  1. Ask if SMS payment link received
  2. If not received: Direct to email admin@urmstontownjfc.co.uk
  3. **Kit Decision Logic**:
     - Check conversation history for "played for Urmston Town last season"
     - If **No**: New player → Routine 32 (kit selection)
     - If **Yes**: Call `check_if_kit_needed` tool
       - If kit needed: Routine 32 (kit selection)
       - If kit not needed: Routine 34 (photo upload)

### Phase 6: Kit Selection (Routines 32-33)

#### Routine 32: Kit Size Selection
- **Purpose**: Choose appropriate kit size
- **Available Sizes**: 5/6, 7/8, 9/10, 11/12, 13/14, S, M, L, XL, 2XL, 3XL
- **Validation**: Accept variations (5-6, 5 to 6) and normalize
- **Recommendation Logic**: Suggest size based on age group
- **Next Step**: Routine 33 (shirt number)

#### Routine 33: Shirt Number Selection
- **Purpose**: Choose shirt number (1-25)
- **Special Rules**: Goalkeepers must choose 1 or 12
- **Process**:
  1. Validate number is 1-25
  2. Call `check_shirt_number_availability` tool
  3. If taken: Request different number
  4. If available: Call `update_kit_details_to_db`
- **Tools Used**: `check_shirt_number_availability`, `update_kit_details_to_db`
- **Next Step**: Routine 34 (photo upload)

### Phase 7: Photo Upload (Routine 34)

#### Routine 34: Passport Photo Upload
- **Purpose**: Collect passport-style photo for ID purposes
- **Validation**:
  - Supported formats: .jpg, .png, .heic, .webp
  - HEIC auto-conversion to JPEG for processing
  - Verify photo shows junior/youth
  - Passport-style requirement (not too strict)
- **Process**:
  1. Validate uploaded image
  2. Call `upload_photo_to_s3` → AWS S3 storage
  3. Call `update_photo_link_to_db` → Save S3 URL
- **Tools Used**: `upload_photo_to_s3`, `update_photo_link_to_db`
- **Next Step**: Routine 35 (completion)

### Phase 8: Registration Completion (Routine 35)

#### Routine 35: Final Confirmation
- **Purpose**: Confirm registration completion
- **Status**: "Pending payment and Direct Debit setup"
- **Final Actions**: Respond to queries, provide support information
- **Club Colors**: Use blue/yellow emojis only

## Age-Based Routing Logic (Routine 22)

### Technical Implementation

The age-based routing system uses conversation history analysis to determine the child's age group:

```python
# Routine 22 logic flow
def handle_routine_22(conversation_history):
    age_group = extract_age_group_from_history(conversation_history)
    
    if age_group in ['U16', 'U17', 'U18']:
        return {
            'next_routine': 23,
            'message': 'Since {child_name} is 16+, we need their separate contact details...'
        }
    else:
        return {
            'next_routine': 28,
            'message': 'Thank you for all the information. Let me confirm all details...'
        }
```

### Age Group Injection System

When a registration code is processed, structured data is injected into the conversation:

```text
[SYSTEM INJECTION - Registration Code Analysis]
Registration type: New Player Registration (200)
Team: Tigers
Age group: U10
Season: 2025-26
Original code: 200-tigers-u10-2526
```

This injection allows Routine 22 to extract the age group for routing decisions.

## Business Rules Implementation

### Sibling Discount Logic
- **Implementation**: Handled at payment processing level (GoCardless)
- **Detection**: Multiple registrations with same parent contact details
- **Application**: Automatic discount applied during payment setup

### Kit Requirements Matrix

| Player Type | Previous Season | Kit Required | Routing |
|-------------|----------------|--------------|---------|
| New Player | N/A | Always Yes | Routine 32 |
| Returning Player | Urmston Town | Check Database | `check_if_kit_needed` tool |
| Returning Player | Other Club | Always Yes | Routine 32 |

### Payment Business Rules
- **Signing Fee**: £45.00 one-time payment
- **Monthly Subscription**: £27.50 per month (September-May, 9 months)
- **Payment Timeline**: Must complete payment within 7 days of SMS
- **Direct Debit**: Requires UK bank account, setup via GoCardless

### Medical Information Handling
- **Collection**: Routine 5 with follow-up for serious conditions
- **Storage**: Comma-separated list format in database
- **Critical Conditions**: EpiPen locations, inhaler storage, emergency contacts
- **Responsibility**: Parent retains primary responsibility for child's medical care

## Tool Integration Matrix

### Core Validation Tools

| Tool | Routines Used | Purpose | Validation Rules |
|------|---------------|---------|------------------|
| `address_validation` | 12-21 | UK address verification | Google Places API validation |
| `address_lookup` | 13, 19 | Postcode + house number lookup | Automatic address completion |
| `child_dob_validation` | 3 | Date of birth validation | 2007+ birth year, valid date format |

### Payment Integration Tools

| Tool | Routine | Purpose | External Service |
|------|---------|---------|------------------|
| `create_payment_token` | 29 | GoCardless billing request | GoCardless API |
| `update_reg_details_to_db` | 29 | Save registration data | Airtable API |

### Kit Management Tools

| Tool | Routine | Purpose | Business Logic |
|------|---------|---------|----------------|
| `check_if_kit_needed` | 30 | Kit requirement check | Team/age group matrix |
| `check_shirt_number_availability` | 33 | Number conflict check | Team roster validation |
| `update_kit_details_to_db` | 33 | Save kit selection | Size + number storage |

### File Processing Tools

| Tool | Routine | Purpose | Capabilities |
|------|---------|---------|--------------|
| `upload_photo_to_s3` | 34 | Photo storage | HEIC conversion, AWS S3 |
| `update_photo_link_to_db` | 34 | Photo URL storage | Database reference |

## Data Flow and State Management

### Session Context Structure

```javascript
session_context = {
    registration_code: "200-tigers-u10-2526",
    routine_number: 15,
    collected_data: {
        parent: {
            first_name: "John",
            last_name: "Smith",
            // ... other fields
        },
        child: {
            first_name: "Jamie",
            last_name: "Smith",
            // ... other fields
        },
        addresses: {
            parent_address: "...",
            child_address: "..." // or same as parent
        }
    },
    injected_metadata: {
        team: "Tigers",
        age_group: "U10",
        season: "2526"
    }
}
```

### Database Schema Integration

The system writes to the `registrations_2526` Airtable table with structured fields:

- **Player Information**: Names, DOB, gender, medical info
- **Parent Information**: Contact details, relationship, address
- **Registration Metadata**: Code, type, season, status
- **Payment Information**: Billing request ID, amounts, status
- **Kit Information**: Size, shirt number, requirement status
- **Photo Information**: S3 URL, upload timestamp

## Error Handling and Retry Mechanisms

### AI Call Retry Logic

```python
def retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            response = ai_call_func(*args)
            parsed_content, routine_number = parse_structured_response(response)
            return True, response, parsed_content, routine_number
        except Exception as e:
            if attempt == max_retries:
                return False, None, f"AI call failed after {max_retries + 1} attempts", None
            wait_time = delay * (2 ** attempt)  # Exponential backoff
            time.sleep(wait_time)
```

### Validation Error Recovery

- **Invalid Input**: Stay on same routine, request clarification
- **Tool Failures**: Graceful degradation with fallback options
- **Payment Errors**: Direct to manual support channels
- **Upload Failures**: Retry mechanism with format conversion

### Business Continuity

- **Registration Persistence**: All data saved incrementally
- **Payment Decoupling**: Registration complete even if payment link fails
- **Manual Intervention**: Admin email contact for complex issues

## Special Workflows and Edge Cases

### Routine 22 Server-Side Processing

Routine 22 is unique in that it triggers server-side processing rather than waiting for user input:

1. **Age Detection**: Extract age group from conversation history
2. **Automatic Routing**: Determine next routine without user interaction
3. **Response Generation**: Create age-appropriate message
4. **Immediate Progression**: No user input required for routing decision

### Address Handling Edge Cases

1. **Different Child Address**: Full address collection workflow (Routines 18-21)
2. **Address Lookup Failures**: Fallback to manual entry
3. **Invalid Postcodes**: Re-prompt with format guidance
4. **International Addresses**: System designed for UK addresses only

### Kit Selection Edge Cases

1. **Returning Player Exceptions**: Use `check_if_kit_needed` for team-specific rules
2. **Shirt Number Conflicts**: Real-time availability checking
3. **Goalkeeper Numbers**: Special validation for positions 1 and 12
4. **Size Variations**: Flexible input parsing (5-6, 5/6, 5 to 6)

### Photo Upload Edge Cases

1. **HEIC Format**: Automatic conversion to JPEG for processing
2. **Large Files**: Async processing with status updates
3. **Invalid Photos**: Re-prompt with specific requirements
4. **Upload Failures**: Retry mechanism with error reporting

### Payment Integration Edge Cases

1. **SMS Delivery Failures**: Email fallback option provided
2. **GoCardless Errors**: Detailed error messaging and support contact
3. **Duplicate Registrations**: Handled at payment processing level
4. **Currency Formatting**: Consistent £XX.XX display format

## Conclusion

The UTJFC Registration Agent implements a sophisticated 35-step workflow that balances comprehensive data collection with user experience optimization. The age-based routing system, intelligent tool integration, and robust error handling ensure reliable registration processing across diverse scenarios while maintaining data integrity and business rule compliance.

The system's modular design allows for easy maintenance and extension, with clear separation between conversation management, validation logic, payment processing, and data storage components.