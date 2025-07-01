# UTJFC Registration Agent System - High-Level Design (HLD)

## Document Overview
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Complete technical documentation for the UTJFC registration agent system  
**Scope**: Registration agent architecture, workflow engine, tool ecosystem, and business process automation  

---

## 1. System Overview

### 1.1 Purpose
The Registration Agent System is a sophisticated AI-powered workflow engine that manages the complete football club registration process for Urmston Town Juniors FC. It provides intelligent conversation flows, automated data validation, payment processing, and comprehensive business process automation through a 35-step guided workflow.

### 1.2 Core Objectives
- **Intelligent Registration Routing**: Automatic detection and routing based on registration codes
- **35-Step Workflow Management**: Complete guided registration process with branching logic
- **Business Process Automation**: End-to-end automation from initial contact to payment setup
- **Data Validation & Normalization**: Comprehensive validation with user-friendly error handling
- **External Service Integration**: Payment, storage, communication, and address validation services
- **Agent Orchestration**: Seamless switching between generic and specialized registration agents

### 1.3 System Capabilities
- **Registration Code Detection**: Regex-based pattern matching with real-time database validation
- **Dual Agent Types**: Re-registration (100 codes) vs New registration (200 codes)
- **Age-Based Routing**: Automatic workflow branching for U16+ players requiring additional contact details
- **Payment Integration**: Complete GoCardless Direct Debit setup with SMS payment links
- **File Processing**: Photo upload, validation, and AWS S3 storage with HEIC conversion support
- **Comprehensive Validation**: 14 specialized tools for different aspects of registration data


---

## 2. Architecture Overview

### 2.1 Core Components

#### 2.1.1 Registration Agent System Structure
```
backend/registration_agent/
├── agents_reg.py                       # Agent class definition (135 lines)
├── registration_agents.py              # Agent instances (26 lines)
├── routing_validation.py               # Code detection & routing (298 lines)
├── registration_routines.py            # 35-step workflow definitions (104 lines)
├── responses_reg.py                    # Response processing engine (833 lines)
├── agent_response_schema_reg.py        # Structured response format (33 lines)
├── agent_response_schema_rereg.py      # Re-registration response format (27 lines)
└── tools/                              # Tool ecosystem
    ├── airtable/                       # Database operations
    └── registration_tools/             # 25+ specialized tools
        ├── registration_data_models.py # Data validation (436 lines)
        ├── create_payment_token.py     # GoCardless integration
        ├── upload_photo_to_s3_tool.py  # File processing
        └── [22 additional tools]
```

#### 2.1.2 Agent Architecture Pattern
```python
class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "System prompt"
    tools: list = []                    # Tool function names
    use_mcp: bool = False              # Local vs MCP execution
    mcp_server_url: str = ""           # MCP server endpoint
    
    def get_instructions_with_routine(self, routine_message: str = ""):
        # Dynamic instruction injection for workflow steps
        return self.instructions.format(routine_instructions=routine_message)
```

### 2.2 Agent Types & Specialization

#### 2.2.1 Re-Registration Agent (100 Codes)
```python
# From backend/registration_agent/registration_agents.py
re_registration_agent = Agent(
    name="UTJFC Re-registration Assistant",
    model="gpt-4.1",  # Overrides Agent class default of gpt-4o-mini
    tools=["address_validation", "address_lookup"],
    use_mcp=False
)
```

**Purpose**: Handle existing players returning for new season
**Capabilities**: Address validation, player lookup, simplified workflow
**Trigger**: Registration codes starting with "100-"

#### 2.2.2 New Registration Agent (200 Codes)
```python
# From backend/registration_agent/registration_agents.py
new_registration_agent = Agent(
    name="UTJFC New Player Registration Assistant", 
    model="gpt-4.1",  # Overrides Agent class default of gpt-4o-mini
    instructions="""[35-step workflow system prompt with dynamic routine injection]""",
    tools=[
        "address_validation", "address_lookup", "create_signup_payment_link",
        "create_payment_token", "update_reg_details_to_db", "check_shirt_number_availability", 
        "update_kit_details_to_db", "upload_photo_to_s3", "update_photo_link_to_db"
    ],
    use_mcp=False
)
```

**Purpose**: Handle complete new player registration process
**Capabilities**: Full 35-step workflow, payment setup, kit management, photo processing
**Trigger**: Registration codes starting with "200-"

**Note**: Agent class default is `gpt-4o-mini` but actual registration agents override this to use `gpt-4.1`

### 2.3 Execution Modes

#### 2.3.1 Local Function Calling Mode
- **Direct Execution**: Python functions called within the backend process
- **Performance**: Fastest execution with immediate results
- **Debugging**: Full access to local debugging and logging
- **Dependencies**: All tools available as local imports

#### 2.3.2 MCP Server Mode
- **External Execution**: Tools executed via JSON-RPC protocol
- **Scalability**: Distributed tool execution across servers
- **Protocol**: JSON-RPC 2.0 over Server-Sent Events (SSE)
- **Flexibility**: Easy to add external tool providers


---

## 3. Registration Code System

### 3.1 Code Format & Structure
**Pattern**: `[PREFIX]-[TEAM]-[AGE_GROUP]-[SEASON][-PLAYER_NAME]`

**Examples**:
- `200-Lions-U10-2526` (New registration)
- `100-Tigers-U13-2526-Jack-Grealish` (Re-registration)

### 3.2 Code Components

#### 3.2.1 Prefix System
- **100**: Re-registration (existing players)
  - Requires player name in code format: `FirstName-Surname`
  - Triggers player lookup in database
  - Simplified workflow for returning players
- **200**: New registration (new players)
  - No player name required in code
  - Triggers complete 35-step registration workflow
  - Full data collection and validation

#### 3.2.2 Validation Pipeline
```python
def validate_and_route_registration(message: str) -> dict:
    # Step 1: Parse registration code format
    registration_code = parse_registration_code(message)
    
    # Step 2: Validate team and age group against Airtable
    is_valid_team = validate_team_and_age_group(team, age_group)
    
    # Step 3: For 100 codes, lookup player details
    player_details = lookup_player_details(player_name, team, age_group)
    
    # Step 4: Determine routing
    route = route_registration_request(registration_code)
```

**Validation Steps**:
1. **Regex Parsing**: Format validation and component extraction
2. **Team Validation**: Real-time lookup against Airtable `team_info` table
3. **Age Group Validation**: Ensure team supports specified age group
4. **Season Validation**: Current season (2526) only
5. **Player Lookup**: For re-registration codes (100 prefix)

### 3.3 Airtable Integration
**Team Validation Query**:
```python
# Query team_info table for validation
formula = f"AND({{short_team_name}} = '{team_normalized}', {{age_group}} = '{age_group_normalized}', {{current_season}} = '2526')"
records = table.all(formula=formula)
return len(records) > 0  # Valid if team/age group combination exists
```

### 3.4 Error Handling
- **Invalid Format**: User-friendly error messages without exposing technical details
- **Database Failures**: Graceful degradation with fallback options
- **Team Not Found**: Clear guidance to contact manager/coach
- **Player Not Found**: Specific error for re-registration attempts

### 3.5 Age Detection & Injection
```python
def inject_structured_registration_data(session_id: str, registration_code: str):
    # Parse registration code components and inject into conversation history
    structured_message = f"""[SYSTEM INJECTION - Registration Code Analysis]
    Registration type: {reg_type} ({parsed["prefix"]})
    Team: {team_name}
    Age group: {age_group}
    Season: {season}
    Original code: {registration_code}"""
    
    add_message_to_session_history(session_id, "system", structured_message)
```


---

## 4. 35-Step Workflow Engine

### 4.1 Workflow Architecture
The workflow engine manages a sophisticated 35-step registration process with intelligent branching and age-based routing.

#### 4.1.1 Workflow Phases
```
Phase 1: Core Information Collection (Routines 1-21)
├── Routines 1-6:  Child & parent basic details
│   ├── 1: Parent name validation
│   ├── 2: Child name validation  
│   ├── 3: Child date of birth (2007+ validation)
│   ├── 4: Child gender normalization
│   ├── 5: Medical issues collection & validation
│   └── 6: Previous team information
├── Routines 7-11: Parent contact information  
│   ├── 7: Parent relationship (Mother/Father/Guardian/Other)
│   ├── 8: UK telephone validation (07.../0161...)
│   ├── 9: Email validation & lowercase formatting
│   ├── 10: Communication consent (GDPR compliance)
│   └── 11: Parent date of birth
├── Routines 12-16: Address collection & validation
│   ├── 12: Postcode collection & UK format validation
│   ├── 13: House number → address_lookup() → Google Places API
│   ├── 14: Manual address entry (fallback)
│   ├── 15: Address confirmation
│   └── 16: Child address check (same/different)
└── Routines 18-21: Child address (if different)
    ├── 18: Child postcode
    ├── 19: Child house number → address_lookup()
    ├── 20: Child manual address (fallback)
    └── 21: Child address confirmation

Phase 2: Age-Based Routing Hub (Routine 22)
├── Server-side age detection from registration code
├── U16+ → Additional contact details (Routines 23-24)
│   ├── 23: Child mobile phone (different from parent)
│   └── 24: Child email (different from parent)
└── Under 16 → Skip to validation (Routine 28)

Phase 3: Payment & Completion (Routines 28-35)
├── Routines 28-29: Information validation & payment setup
│   ├── 28: Data validation & payment explanation
│   └── 29: Payment day selection → create_payment_token
├── Routine 30:     SMS payment link confirmation
├── Routines 32-33: Kit size & shirt number selection
│   ├── 32: Kit size validation (5/6, 7/8, ..., S-3XL)
│   └── 33: Shirt number validation & availability check
├── Routine 34:     Photo upload & validation
└── Routine 35:     Registration completion
```

#### 4.1.2 Dynamic Instruction System
```python
class RegistrationRoutines:
    ROUTINES = {
        1: """Task: Your current task is to: 1) take the parent's first and last name...""",
        2: """Task: Your current task is to: 1) take the child's first and last name...""",
        # ... 35 total routine definitions with specific validation rules
    }
    
    @classmethod
    def get_routine_message(cls, routine_number: int) -> str:
        return cls.ROUTINES.get(routine_number, "")
```

**Process Flow**:
1. Frontend sends `routine_number` with user message
2. System retrieves routine-specific instructions from ROUTINES dict
3. Instructions injected into agent's system prompt via `get_instructions_with_routine()`
4. Agent responds with context-aware behavior and validation
5. Next routine number returned to frontend for progression control

### 4.2 Key Workflow Features

#### 4.2.1 Age-Based Routing (Routine 22) - Server-Side Intelligence
**Special Server-Side Logic**: 
```python
# Check for routine 22 detection - triggers server-side processing
if routine_number_from_agent == 22:
    # Extract age group from conversation history
    age_info = parse_age_from_registration_code(registration_code)
    if age_info["age_number"] >= 16:
        next_routine = 23  # Additional contact details for U16+
    else:
        next_routine = 28  # Skip to validation for under 16
    
    # Loop back with new routine instead of sending response
    return process_routine_with_agent(agent, input_messages, next_routine)
```

**Age Detection Logic**:
```python
def parse_age_from_registration_code(registration_code: str) -> dict:
    age_match = re.search(r'[Uu](\d+)', registration_code)
    age_number = int(age_match.group(1))
    
    return {
        "age_number": age_number,
        "age_group": f"U{age_number}",
        "route_type": "over_16" if age_number >= 16 else "under_16",
        "next_routine": 23 if age_number >= 16 else 28
    }
```

#### 4.2.2 Address Validation Flow - Two-Step Google Places Integration
**Smart Address Collection Process**:
```
Routine 12: Postcode Collection → UK format validation
Routine 13: House Number → address_lookup() tool call
    ├── Success → Routine 15 (show formatted address for confirmation)
    └── Failure → Routine 14 (manual entry fallback)
Routine 14: Manual Entry (Fallback) → Visual validation by agent
    └── Agent validates UK address format without API
Routine 15: Address Confirmation → User accepts/rejects
    ├── Accept → Routine 16 (child address check)
    └── Reject → Routine 14 (re-enter address)
```

**address_lookup Tool Implementation**:
```python
# Google Places API integration for postcode + house number
def handle_address_lookup(input_data):
    postcode = input_data.postcode
    house_number = input_data.house_number
    
    # Call Google Places API
    response = places_client.find_place_from_text(
        input=f"{house_number} {postcode}",
        input_type=places.PlaceSearchType.ADDRESS,
        fields=['formatted_address', 'geometry']
    )
    
    return {"formatted_address": response.candidates[0].formatted_address}
```

#### 4.2.3 Child Address Handling - Conditional Logic
**Smart Branching Logic**:
```
Routine 16: "Does child live at same address?"
├── Yes → Set routine_number = 22 (server handles age-based routing)
│   └── Server detects routine 22 → triggers age detection
└── No → Routines 18-21 (separate address collection flow)
    └── After child address complete → Routine 22
```

**Implementation Pattern**:
```python
# Routine 16 logic in registration_routines.py
16: """Task: Your current task is to: 1) take the response about whether {child_name} lives at the same address as the parent 2) accept Yes/No response 3) if unclear response, set routine_number = 16 and ask for clarification 4) if Yes, set routine_number = 22 (DO NOT ask a question - server will handle routing) 5) if No, set routine_number = 18 and ask for {child_name}'s address."""
```

### 4.3 Validation Integration

#### 4.3.1 Silent Validation Approach
**Principle**: All validation happens behind the scenes without explicitly mentioning validation checks to parents.

**Example - Routine 1 (Parent Name)**:
```
1) Take parent's first and last name (minimum 2 parts)
2) Validate: letters, apostrophes, hyphens, spaces only
3) Convert curly apostrophes to straight apostrophes
4) If invalid: set routine_number = 1, ask for clarification (NO mention of validation)
5) If valid: set routine_number = 2, ask for child's name
```

#### 4.3.2 Embedded vs Function Validation
**Embedded Validation** (Routines 1-2, 4, 7-12, 16): Logic built into routine instructions for speed
**Function Validation** (Routines 3, 5, 13, 19, 33-34): Complex validation requiring specialized tools

**Tool Integration Examples**:
- **Routine 3**: `child_dob_validation` - Date format conversion and age rule validation
- **Routine 5**: `medical_issues_validation` - Medical information structuring and normalization
- **Routine 13/19**: `address_lookup` - Google Places API integration
- **Routine 33**: `check_shirt_number_availability` - Database uniqueness validation
- **Routine 34**: `upload_photo_to_s3` - File processing and Vision API validation

### 4.4 Response Schema Integration

#### 4.4.1 Structured Response Format
```python
class AgentResponse(BaseModel):
    agent_final_response: str = Field(
        description="User-facing response text for frontend display",
        min_length=1
    )
    
    routine_number: int = Field(
        description="Next routine step number for workflow progression control",
        ge=1
    )
```

**Usage in OpenAI Responses API**:
```python
api_params = {
    "model": agent.model,
    "instructions": agent.get_instructions_with_routine(routine_message),
    "input": input_messages,
    "text": {
        "format": {
            "type": "json_schema",
            "name": "agent_response", 
            "schema": AgentResponse.model_json_schema(),
            "strict": True
        }
    }
}
```


---

## 5. Tool Ecosystem Architecture

### 5.1 Tool Organization & Registry

#### 5.1.1 Tool Categories
```python
# Validation Tools (5 tools)
validation_tools = [
    "person_name_validation",      # Name format validation with regex & normalization
    "child_dob_validation",        # Date validation with age rules & format conversion  
    "medical_issues_validation",   # Medical information structuring & formatting
    "address_validation",          # Google Places API validation & formatting
    "address_lookup"               # Postcode to address conversion via Google Places
]

# Payment Integration Tools (3 tools)
payment_tools = [
    "create_payment_token",        # GoCardless billing request creation
    "create_signup_payment_link",  # Payment URL generation with custom amounts
    "send_sms_payment_link"        # Twilio SMS notifications with payment links
]

# Database Operations (4 tools)
database_tools = [
    "update_reg_details_to_db",    # Primary registration data save to Airtable
    "check_shirt_number_availability", # Shirt number uniqueness validation
    "update_kit_details_to_db",    # Kit selection data save
    "update_photo_link_to_db"      # Photo URL storage after S3 upload
]

# File Processing (1 tool)
file_tools = [
    "upload_photo_to_s3"           # AWS S3 photo storage with HEIC conversion
]
```

#### 5.1.2 Tool Registry Implementation
**Agent Tool Association**:
```python
def get_tools_for_openai(self):
    available_tools = {
        "address_validation": ADDRESS_VALIDATION_TOOL,
        "address_lookup": ADDRESS_LOOKUP_TOOL,
        "create_payment_token": CREATE_PAYMENT_TOKEN_TOOL,
        "create_signup_payment_link": CREATE_SIGNUP_PAYMENT_LINK_TOOL,
        "update_reg_details_to_db": UPDATE_REG_DETAILS_TO_DB_TOOL,
        "check_shirt_number_availability": CHECK_SHIRT_NUMBER_AVAILABILITY_TOOL,
        "update_kit_details_to_db": UPDATE_KIT_DETAILS_TO_DB_TOOL,
        "upload_photo_to_s3": UPLOAD_PHOTO_TO_S3_TOOL,
        "update_photo_link_to_db": UPDATE_PHOTO_LINK_TO_DB_TOOL,
        "send_sms_payment_link": SEND_SMS_PAYMENT_LINK_TOOL
    }
    
    openai_tools = []
    for tool_name in self.tools:
        if tool_name in available_tools:
            openai_tools.append(available_tools[tool_name])
    
    return openai_tools
```

### 5.2 Key Tools Deep Dive

#### 5.2.1 Payment Processing Tools

**create_payment_token** (Primary Payment Tool):
```python
# Creates GoCardless billing request with subscription setup
def handle_create_payment_token(input_data):
    # 1. Extract payment day and amounts from conversation history
    # 2. Create GoCardless billing request with one-off + subscription
    # 3. Generate billing_request_flow for user authorization
    # 4. Return billing_request_id and payment configuration
    # 5. Integration with routine 29 for payment setup
```

**Implementation Details**:
- **One-off Payment**: £55 registration fee
- **Monthly Subscription**: £12/month starting after first payment
- **Payment Day**: User-selected (1st-28th of month)
- **Currency**: GBP with GoCardless mandate creation
- **Error Handling**: Comprehensive GoCardless API error mapping

**send_sms_payment_link** (Notification Tool):
```python
# Sends SMS payment link via Twilio with background processing
def ai_send_sms_payment_link(input_data):
    # 1. Format UK phone number for Twilio (+44 prefix)
    # 2. Generate payment link URL with billing_request_id
    # 3. Send SMS via Twilio API with custom message template
    # 4. Log delivery status and metrics to SQLite database
    # 5. Return confirmation with delivery status
```

**SMS Template**:
```
UTJFC Registration: Complete your payment setup here: https://pay.gocardless.com/billing_requests/{billing_request_id}
This will set up your £55 registration fee and £12/month subscription.
```

#### 5.2.2 File Processing Tools

**upload_photo_to_s3** (Advanced File Processing):
```python
# Comprehensive photo processing with HEIC support and validation
def upload_photo_to_s3(input_data):
    # 1. File validation (format, size, content)
    # 2. HEIC to JPEG conversion if needed (pillow-heif library)
    # 3. Generate structured S3 filename with timestamp
    # 4. Upload to S3 bucket with public-read access
    # 5. OpenAI Vision API content validation
    # 6. Return public URL for database storage
```

**Advanced Features**:
- **Format Support**: PNG, JPEG, WebP, HEIC (with conversion)
- **Size Validation**: 10MB maximum with detailed error messages
- **Content Validation**: OpenAI Vision API to verify it's a person
- **HEIC Conversion**: Automatic conversion for iOS photos
- **Structured Naming**: `{team_name}_{player_name}_{timestamp}.jpg`
- **S3 Configuration**: Public access with CloudFront CDN support

**Content Validation Implementation**:
```python
# OpenAI Vision API integration for photo validation
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Is this a photo of a person? Respond with only 'yes' or 'no'."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
        ]
    }]
)
```

#### 5.2.3 Database Integration Tools

**update_reg_details_to_db** (Primary Database Tool):
```python
# Comprehensive registration data save to Airtable with validation
def update_reg_details_to_db_ai_friendly(input_data):
    # 1. Parse entire conversation history for all collected data
    # 2. Extract and validate against RegistrationDataContract model
    # 3. Handle special cases (child address, U16+ contacts)
    # 4. Save to Airtable registrations_2526 table
    # 5. Include conversation history as JSON for audit trail
    # 6. Add payment details and timestamps
```

**RegistrationDataContract Integration**:
```python
class RegistrationDataContract(BaseModel):
    # Child Information (Required)
    child_first_name: str = Field(..., min_length=1)
    child_last_name: str = Field(..., min_length=1)
    child_date_of_birth: date = Field(...)
    child_gender: str = Field(...)
    
    # Parent Information (Required)
    parent_first_name: str = Field(..., min_length=1)
    parent_last_name: str = Field(..., min_length=1)
    parent_relationship: str = Field(...)
    parent_phone_number: str = Field(...)
    parent_email: EmailStr = Field(...)
    
    # Conditional Fields (Age-dependent)
    child_phone_number: Optional[str] = Field(None)  # U16+ only
    child_email: Optional[EmailStr] = Field(None)    # U16+ only
    
    # Computed Fields
    full_registration_code: str = Field(...)
    conversation_history: str = Field(...)
    billing_request_id: Optional[str] = Field(None)
```

**check_shirt_number_availability** (Validation Tool):
```python
# Real-time shirt number availability checking
def check_shirt_number_availability_ai_friendly(input_data):
    # 1. Query Airtable for existing registrations with same number
    # 2. Check against team_name and age_group for uniqueness
    # 3. Return availability status with alternative suggestions
    # 4. Handle edge cases (preferred numbers, conflicts)
```

### 5.3 Data Models & Validation

#### 5.3.1 Core Data Model
**RegistrationDataContract** (436 lines in `registration_data_models.py`):
- **40+ Validated Fields**: Comprehensive registration data structure
- **Strict Typing**: Pydantic models with field validators
- **Conditional Logic**: Different requirements based on age group
- **Data Normalization**: Automatic formatting and cleanup
- **Error Handling**: User-friendly validation error messages

**Key Validation Patterns**:
```python
# Phone number validation with regex
@field_validator('parent_phone_number')
@classmethod
def validate_parent_phone(cls, v):
    if not re.match(r'^(07\d{9}|0161\d{7})$', v):
        raise ValueError('Must be valid UK mobile (07...) or Manchester (0161...)')
    return v

# Address validation with Google Places integration  
@field_validator('parent_address')
@classmethod  
def validate_address(cls, v):
    if not v or len(v.strip()) < 10:
        raise ValueError('Address must be at least 10 characters')
    return v.strip()
```

#### 5.3.2 Tool Schema Generation
**Pydantic to OpenAI Schema Conversion**:
```python
# tools/registration_tools/pydantic_to_openai_schema.py
def convert_pydantic_to_openai_schema(model_class):
    schema = model_class.model_json_schema()
    
    openai_schema = {
        "type": "function",
        "function": {
            "name": model_class.__name__.lower(),
            "description": model_class.__doc__ or f"Execute {model_class.__name__}",
            "parameters": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", [])
            }
        }
    }
    
    return openai_schema
```

### 5.4 External Service Integration

#### 5.4.1 GoCardless Payment System
**Configuration**:
- **Environment**: Hardcoded to `'live'` (production)
- **Webhooks**: Payment status updates and mandate confirmations  
- **Currency**: GBP only with UK bank account mandates
- **Payment Flow**: Billing request → Customer authorization → Mandate creation

**Integration Architecture**:
```python
# GoCardless client initialization (from create_payment_token.py)
client = gocardless_pro.Client(
    access_token=gocardless_api_key,
    environment='live'  # Hardcoded to live environment
)

# Billing request creation
billing_request = gocardless_client.billing_requests.create(
    params={
        "mandate_request": {"currency": "GBP"},
        "payment_request": {"amount": 5500, "currency": "GBP"},  # £55.00
        "metadata": {"club": "UTJFC", "season": "2526"}
    }
)
```

#### 5.4.2 AWS S3 Storage System
**Photo Storage Configuration**:
- **Bucket**: `utjfc-player-photos` (or environment-specific)
- **Access**: Public-read for photo display
- **File Structure**: `{team_name}/{player_name}_{timestamp}.jpg`
- **CDN**: CloudFront distribution for global delivery

#### 5.4.3 Twilio SMS System
**SMS Configuration**:
- **Service**: Twilio SMS API with UK number support
- **Templates**: Payment links, reminders, confirmations
- **Delivery Tracking**: Status updates stored in SQLite
- **Error Handling**: Retry logic and fallback options

#### 5.4.4 Airtable Database System
**Table Structure**:
- **registrations_2526**: Main registration data
- **team_info**: Team and age group validation
- **payment_tracking**: GoCardless integration data
- **sms_delivery**: Communication audit trail


---

## 6. Session Management & State Persistence

### 6.1 Cross-Agent Session Management
**Implementation**: `urmston_town_agent/chat_history.py` manages persistent conversation state across agent transitions.

#### 6.1.1 Session Storage
```python
# In-memory session storage with conversation history
sessions = {}

def add_message_to_session_history(session_id: str, role: str, content: str):
    if session_id not in sessions:
        sessions[session_id] = []
    
    sessions[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

def get_session_history(session_id: str) -> list:
    return sessions.get(session_id, [])
```

#### 6.1.2 Agent Transition Management
**Process Flow**:
1. **Generic Agent → Registration Agent**: Session transfers with full conversation history
2. **State Injection**: Registration code data injected as system message
3. **Routine Continuity**: Workflow state maintained across agent switches
4. **Context Preservation**: All collected data available to specialized agents

**Transition Implementation**:
```python
# Transfer session from generic to registration agent
def transfer_to_registration_agent(session_id: str, registration_code: str):
    # 1. Get existing conversation history
    conversation_history = get_session_history(session_id)
    
    # 2. Inject structured registration data
    inject_structured_registration_data(session_id, registration_code)
    
    # 3. Route to appropriate agent (100 vs 200 codes)
    agent = get_agent_for_registration_type(registration_code)
    
    # 4. Continue with specialized agent
    return process_with_agent(agent, conversation_history)
```

### 6.2 Conversation State Management

#### 6.2.1 Routine State Tracking
**Frontend State Management**:
```javascript
// React state for routine progression
const [currentRoutine, setCurrentRoutine] = useState(1);
const [registrationCode, setRegistrationCode] = useState(null);
const [conversationHistory, setConversationHistory] = useState([]);

// Backend routine response handling
function handleRoutineResponse(response) {
    setCurrentRoutine(response.routine_number);
    setConversationHistory(prev => [...prev, response.agent_final_response]);
}
```

#### 6.2.2 Data Persistence Strategy
**Multi-Layer Persistence**:
1. **Session Memory**: Active conversation in memory during registration
2. **Progress Checkpoints**: Key data points saved at routine milestones
3. **Database Storage**: Complete registration data saved at routine 29
4. **Audit Trail**: Full conversation history stored with registration

### 6.3 Error Recovery & Resilience

#### 6.3.1 Tool Failure Handling
**Graceful Degradation**:
```python
# Address lookup fallback example
def handle_address_lookup_with_fallback(input_data):
    try:
        # Primary: Google Places API
        return google_places_lookup(input_data)
    except Exception as e:
        logger.warning(f"Google Places API failed: {e}")
        
        # Fallback: Manual address entry
        return {
            "success": False,
            "fallback_required": True,
            "message": "Please enter your full address manually"
        }
```

#### 6.3.2 Session Recovery
**Automatic Session Recovery**:
- **Browser Refresh**: Session state maintained in browser storage
- **Connection Loss**: Automatic reconnection with session restoration
- **Agent Failures**: Graceful fallback to previous routine state
- **Data Loss Prevention**: Progressive data save at key checkpoints

---

## 7. Performance & Scalability

### 7.1 Performance Characteristics
**Actual Implementation**:
- **Tool Execution**: Synchronous execution within agent responses
- **Database Operations**: Direct Airtable API calls via pyairtable
- **File Processing**: Synchronous S3 upload with HEIC conversion
- **Payment Integration**: Direct GoCardless API calls

### 7.2 Concurrent User Support
**Session Management**:
- **Session Isolation**: In-memory session storage per conversation
- **Tool Execution**: Sequential tool calls within each session
- **State Persistence**: Conversation history maintained in memory

### 7.3 Monitoring & Logging
**Basic Logging**:
- **Console Output**: Print statements for debugging and status
- **Error Handling**: Try/catch blocks with error messages
- **SMS Metrics**: SQLite database for SMS delivery tracking (`sms_metrics_queue.db`)

---

## 8. Security & Data Protection

### 8.1 Data Security Measures
**Privacy Protection**:
- **GDPR Compliance**: Explicit consent collection in routine 10
- **Data Minimization**: Only collect necessary registration information
- **Secure Storage**: Encrypted data transmission and storage
- **Access Controls**: Restricted database access with API keys

### 8.2 Payment Security
**PCI Compliance**:
- **No Card Storage**: GoCardless handles all payment data
- **Secure Redirects**: Payment processing on GoCardless platform
- **Mandate Protection**: Bank account details never stored locally
- **Audit Trails**: Complete payment process logging

### 8.3 File Upload Security
**Photo Processing Security** (as implemented):
- **File Type Validation**: PNG, JPEG, WebP, HEIC formats supported
- **Size Limits**: 10MB maximum file size validation
- **Content Validation**: OpenAI Vision API to verify it's a person
- **S3 Storage**: Public-read access for photo display

---

## 9. Integration Architecture

### 9.1 External Service Dependencies
**Critical Dependencies** (based on actual implementation):
- **OpenAI API**: GPT models for conversation and Vision API for photo validation
- **GoCardless**: Payment processing (hardcoded to 'live' environment)
- **Airtable**: Database for registrations and team validation
- **Google Places API**: Address validation and lookup
- **AWS S3**: Photo storage and processing
- **Twilio**: SMS notifications for payment links

**API Keys Required**:
- `OPENAI_API_KEY`
- `GOCARDLESS_API_KEY` 
- `AIRTABLE_API_KEY`
- `GOOGLE_PLACES_API_KEY`
- AWS credentials (via AWS profile)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### 9.2 API Integration Patterns
**Error Handling Strategy** (as implemented):
- **Try/Catch Blocks**: Basic error handling in all tool functions
- **Graceful Degradation**: Address lookup falls back to manual entry
- **User-Friendly Messages**: Technical errors converted to readable messages
- **Tool-Level Validation**: Input validation before API calls

---

## 10. Development & Deployment

### 10.1 Environment Configuration
**Actual Configuration** (based on `backend/registration_agent/env.example`):
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=appBLxf3qmGIBc6ue

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8002/mcp
USE_MCP=true

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Payment Link Configuration
PAYMENT_BASE_URL=https://your-ngrok-url.ngrok.io

# Server Configuration
PORT=8001
HOST=0.0.0.0
```

**Note**: GoCardless environment is hardcoded to `'live'` in `create_payment_token.py` (line 172)

### 10.2 Testing Strategy
**Actual Testing Files** (based on codebase):
- **Tool Testing**: Individual test files like `test_sms_tool.py`, `test_twilio_simple.py`
- **GoCardless Testing**: `debug_gocardless.py`, `test_gocardless.py`
- **Address Flow Testing**: `test_address_flow.py`, `test_child_address_handling.py`
- **Comprehensive Testing**: `comprehensive_test.py` for registration tools
- **MCP Integration Testing**: Multiple test files in `mcp_test_files/`

### 10.3 Deployment Architecture
**Current Deployment** (based on server configuration):
- **FastAPI Server**: `backend/server.py` with port configuration from env
- **Development Setup**: Uses ngrok for payment URLs
- **MCP Server**: Separate server on port 8002
- **Frontend**: Next.js development server
- **Configuration**: Environment variables from `.env` files

---

## 11. Future Enhancements

### 11.1 Planned Features
**Short-term Roadmap**:
- **Photo Gallery**: Team photo collections
- **Kit Customization**: Advanced kit options
- **Payment Reminders**: Automated SMS reminders
- **Multi-language Support**: Welsh and other languages

### 11.2 Scalability Improvements
**Long-term Architecture**:
- **Microservices**: Tool-specific service decomposition
- **Event-Driven Architecture**: Asynchronous processing
- **Caching Layer**: Redis for session and data caching
- **CDN Integration**: Global content delivery

---

## 12. Conclusion

The UTJFC Registration Agent System represents a sophisticated implementation of conversational AI for business process automation. Key achievements include:

### 12.1 Technical Achievements
- **Intelligent Workflow Management**: 35-step process with dynamic branching
- **Dual Agent Architecture**: Specialized agents for different registration types
- **Comprehensive Tool Ecosystem**: 14 specialized tools for complete automation
- **Robust Error Handling**: Graceful degradation and recovery mechanisms
- **External Service Integration**: Payment, storage, communication, and validation services

### 12.2 Business Value
- **Complete Automation**: End-to-end registration without human intervention
- **User Experience**: Conversational interface with intelligent validation
- **Data Quality**: Comprehensive validation and normalization
- **Payment Integration**: Seamless Direct Debit setup with SMS notifications
- **Operational Efficiency**: Reduced manual processing and error rates

### 12.3 Architecture Benefits
- **Modularity**: Clear separation between agents, tools, and workflows
- **Extensibility**: Easy addition of new tools and workflow steps
- **Reliability**: Comprehensive error handling and fallback mechanisms
- **Maintainability**: Well-structured codebase with clear documentation
- **Scalability**: Design supports concurrent users and future growth

The system successfully demonstrates how conversational AI can be applied to complex business processes, providing both technical sophistication and practical business value for football club registration management.

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Total Lines**: 1,200+  
**File Location**: `system_docs/registration_system_HLD.md`

