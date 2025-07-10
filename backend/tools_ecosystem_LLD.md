# UTJFC Registration Agent Tools Ecosystem - Low Level Design

## Overview

The UTJFC Registration Agent system employs a sophisticated tool ecosystem with 14+ specialized tools organized into distinct categories. This document provides a comprehensive analysis of the tool architecture, patterns, and integrations.

## Tool Architecture

### Core Components

1. **Tool Definitions** (`*_tool.py` files)
   - OpenAI function schemas with detailed parameter specifications
   - Tool descriptions and usage instructions
   - Parameter validation and type definitions

2. **Tool Handlers** (`handle_*` functions)
   - Python functions that execute tool logic
   - Input validation and error handling
   - Return formatted JSON responses

3. **Business Logic** (core implementation files)
   - Domain-specific validation and processing
   - External service integrations
   - Data transformation and normalization

4. **Data Models** (`registration_data_models.py`)
   - Pydantic models for data validation
   - Type safety and field constraints
   - Cross-field validation rules

## Tool Categories

### 1. Validation Tools

#### **Person Name Validation**
- **Files**: `person_name_validation.py`, `person_name_validation_tool.py`
- **Purpose**: Validates full names according to UTJFC standards
- **Key Features**:
  - Minimum 2 parts (first + last name)
  - Only letters, apostrophes, hyphens allowed
  - Automatic curly apostrophe normalization
  - Whitespace cleanup
- **Schema**:
  ```python
  {
      "type": "function",
      "name": "person_name_validation",
      "parameters": {
          "full_name": {"type": "string"},
          "extract_parts": {"type": "boolean", "default": False}
      }
  }
  ```

#### **Child Date of Birth Validation**
- **Files**: `child_dob_validation.py`, `child_dob_validation_tool.py`
- **Purpose**: Validates child DOB and calculates age groups
- **Key Features**:
  - Multiple date format support (DD/MM/YYYY, MM/DD/YYYY, etc.)
  - Age range validation (2007 or later)
  - Age group calculation (u8, u9, u10, etc.)
  - Future date prevention

#### **Medical Issues Validation**
- **Files**: `medical_issues_validation.py`, `medical_issues_validation_tool.py`
- **Purpose**: Validates medical condition descriptions
- **Key Features**:
  - Y/N flag validation
  - Medical condition text normalization
  - Severity assessment for critical conditions
  - Structured medical data formatting

#### **Address Validation**
- **Files**: `address_validation.py`, `address_validation_tool.py`
- **Purpose**: Validates UK addresses and postcodes
- **Key Features**:
  - UK postcode format validation
  - Address completeness checks
  - Geographic area validation (Manchester/Trafford region)
  - Address parsing and normalization

### 2. Address Lookup Tools

#### **Address Lookup**
- **Files**: `address_lookup.py`, `address_lookup_tool.py`
- **Purpose**: Automatic address lookup using postcode + house number
- **Key Features**:
  - Royal Mail API integration
  - Postcode validation
  - House number matching
  - Formatted address return

#### **Postcode Validation**
- **Files**: `postcode_validation.py`, `postcode_validation_tool.py`
- **Purpose**: Standalone postcode validation
- **Key Features**:
  - UK postcode format validation
  - Space normalization
  - Case standardization

### 3. Payment Processing Tools

#### **GoCardless Payment Link Creation**
- **Files**: `gocardless_payment.py`, `gocardless_payment_tool.py`
- **Purpose**: Creates payment links for registration fees
- **Key Features**:
  - £45 one-off signing fee
  - £27.50 monthly subscription (Sep-May)
  - Direct Debit mandate setup
  - Prefilled customer data
- **Schema**:
  ```python
  {
      "required": ["player_full_name", "age_group", "team_name", 
                  "parent_full_name", "parent_email", "parent_address", 
                  "parent_postcode"]
  }
  ```

#### **Payment Token Creation**
- **Files**: `create_payment_token.py`, `create_payment_token_tool.py`
- **Purpose**: Creates persistent billing request tokens
- **Key Features**:
  - Decoupled payment flow
  - Billing request ID generation
  - Payment amount calculation
  - Token storage for later use
- **Schema**:
  ```python
  {
      "required": ["player_full_name", "age_group", "team_name", 
                  "parent_full_name", "parent_first_name", 
                  "preferred_payment_day", "parent_phone"]
  }
  ```

#### **SMS Payment Link**
- **Files**: `send_sms_payment_link.py`, `send_sms_payment_link_tool_definition.py`
- **Purpose**: Sends payment links via SMS
- **Key Features**:
  - Twilio SMS integration
  - Payment link delivery
  - SMS metrics tracking
  - Delivery status monitoring

### 4. Database Operation Tools

#### **Registration Data Storage**
- **Files**: `update_reg_details_to_db_tool_ai_friendly.py`
- **Purpose**: Stores complete registration data to Airtable
- **Key Features**:
  - Pydantic validation using `RegistrationDataContract`
  - 50+ field validation
  - Session context fallback
  - Comprehensive error handling
- **Data Flow**:
  1. AI provides individual fields
  2. Pydantic validation
  3. Airtable data preparation
  4. Database write with error handling

#### **Kit Details Storage**
- **Files**: `update_kit_details_to_db_tool.py`
- **Purpose**: Updates kit information in database
- **Key Features**:
  - Kit size validation
  - Shirt number tracking
  - Team-specific kit requirements
  - Availability checking

#### **Photo Link Storage**
- **Files**: `update_photo_link_to_db_tool.py`
- **Purpose**: Stores photo URLs in database
- **Key Features**:
  - S3 URL linking
  - Record ID association
  - Photo metadata storage

#### **Airtable Database Operations**
- **Files**: `airtable_tool_definition.py`, `airtable_agent.py`
- **Purpose**: Generic database CRUD operations
- **Key Features**:
  - Natural language query processing
  - Data normalization
  - Schema compliance
  - Multi-operation support

### 5. Kit Management Tools

#### **Kit Requirement Check**
- **Files**: `check_if_kit_needed.py`, `check_if_kit_needed_tool.py`
- **Purpose**: Determines if player needs new kit
- **Key Features**:
  - Season-based kit cycling
  - Team-specific requirements
  - Previous season checking
  - Age group considerations

#### **Shirt Number Availability**
- **Files**: `check_shirt_number_availability_tool.py`
- **Purpose**: Validates shirt number availability
- **Key Features**:
  - Team-specific availability
  - Number range validation (1-25)
  - Goalkeeper number logic (1, 12)
  - Duplicate prevention

### 6. Photo Management Tools

#### **Photo Upload to S3**
- **Files**: `upload_photo_to_s3_tool.py`
- **Purpose**: Uploads player photos to AWS S3
- **Key Features**:
  - Multiple format support (.jpg, .png, .heic, .webp)
  - HEIC to JPEG conversion
  - Automatic file naming
  - Environment-aware AWS configuration
- **File Processing**:
  ```python
  # HEIC conversion example
  with Image.open(file_path) as img:
      if img.mode in ('RGBA', 'LA', 'P'):
          img = img.convert('RGB')
  ```

## Tool Registration and Invocation

### Agent Tool Configuration

Tools are registered with agents through the `tools` parameter:

```python
# Re-registration agent
re_registration_agent = Agent(
    name="UTJFC Re-registration Assistant",
    model="gpt-4.1",
    tools=["address_validation", "address_lookup"],
    use_mcp=False
)

# New registration agent
new_registration_agent = Agent(
    name="UTJFC New Player Registration Assistant", 
    model="gpt-4.1",
    tools=["address_validation", "address_lookup", "create_signup_payment_link", 
           "create_payment_token", "update_reg_details_to_db", 
           "check_shirt_number_availability", "update_kit_details_to_db", 
           "upload_photo_to_s3", "update_photo_link_to_db", "check_if_kit_needed"],
    use_mcp=False
)
```

### Tool Resolution System

The `Agent` class provides two methods for tool resolution:

1. **`get_tools_for_openai()`**: Returns OpenAI-compatible tool definitions
2. **`get_tool_functions()`**: Returns Python function handlers

```python
def get_tools_for_openai(self):
    available_tools = {
        "person_name_validation": PERSON_NAME_VALIDATION_TOOL,
        "child_dob_validation": CHILD_DOB_VALIDATION_TOOL,
        "medical_issues_validation": MEDICAL_ISSUES_VALIDATION_TOOL,
        # ... more tools
    }
    
    openai_tools = []
    for tool_name in self.tools:
        if tool_name in available_tools:
            openai_tools.append(available_tools[tool_name])
    
    return openai_tools
```

### Tool Invocation Flow

1. **AI Agent**: Calls tool with parameters
2. **Tool Handler**: Validates input and processes request
3. **Business Logic**: Executes core functionality
4. **Response**: Returns structured JSON response

Example invocation:
```python
# Tool call from AI
{
    "type": "function",
    "name": "person_name_validation",
    "parameters": {
        "full_name": "John O'Connor",
        "extract_parts": true
    }
}

# Handler processes and returns
{
    "valid": true,
    "message": "Valid name with 2 parts",
    "parts": ["John", "O'Connor"],
    "normalized_name": "John O'Connor",
    "first_name": "John",
    "last_name": "O'Connor"
}
```

## Error Handling Patterns

### 1. Validation Errors
```python
try:
    validated_data = RegistrationDataContract(**kwargs)
except ValidationError as e:
    return {
        "success": False,
        "message": f"Validation failed: {str(e)}",
        "errors": e.errors()
    }
```

### 2. External Service Errors
```python
try:
    api_response = external_service.call()
except ImportError:
    return fallback_response()
except Exception as e:
    return {
        "success": False,
        "message": f"Service error: {str(e)}"
    }
```

### 3. Data Processing Errors
```python
try:
    processed_data = process_input(data)
except ValueError as e:
    return {
        "valid": False,
        "message": f"Invalid data: {str(e)}",
        "usage_note": "Please provide corrected data"
    }
```

## External Service Integrations

### 1. **Airtable** (Database)
- **Purpose**: Primary data storage
- **Integration**: PyAirtable API
- **Tables**: `registrations_2526`
- **Operations**: CRUD with validation

### 2. **GoCardless** (Payments)
- **Purpose**: Direct Debit and one-off payments
- **Integration**: GoCardless API
- **Features**: Billing requests, payment flows, mandate setup

### 3. **Twilio** (SMS)
- **Purpose**: SMS notifications and payment links
- **Integration**: Twilio API
- **Features**: Message delivery, status tracking

### 4. **AWS S3** (Photo Storage)
- **Purpose**: Player photo storage
- **Integration**: Boto3
- **Features**: File upload, HEIC conversion, URL generation

### 5. **Address Lookup Services**
- **Purpose**: UK address validation
- **Integration**: Royal Mail API
- **Features**: Postcode lookup, address formatting

## Data Models and Schemas

### Registration Data Contract

The `RegistrationDataContract` is the core data model with 50+ fields:

```python
class RegistrationDataContract(BaseModel):
    # Player Information
    player_first_name: str = Field(..., min_length=1, max_length=50)
    player_last_name: str = Field(..., min_length=1, max_length=50)
    player_dob: str = Field(..., pattern=r'^\d{2}-\d{2}-\d{4}$')
    player_gender: Literal["Male", "Female", "Not Disclosed"]
    
    # Medical Information
    player_has_any_medical_issues: Literal["Y", "N"]
    description_of_player_medical_issues: Optional[str]
    
    # Parent Information
    parent_first_name: str = Field(..., min_length=1, max_length=50)
    parent_last_name: str = Field(..., min_length=1, max_length=50)
    parent_email: str
    parent_telephone: str
    
    # Payment Information
    billing_request_id: str = Field(..., min_length=10, max_length=50)
    preferred_payment_day: int = Field(..., ge=-1, le=31)
    
    # Validation Methods
    @field_validator('parent_telephone', 'player_telephone')
    def validate_phone_format(cls, v):
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^07\d{9}$', cleaned):
            raise ValueError('Phone number must be UK mobile')
        return cleaned
```

### Tool Parameter Schemas

Each tool defines its parameters using OpenAI function schema format:

```python
PERSON_NAME_VALIDATION_TOOL = {
    "type": "function",
    "name": "person_name_validation",
    "description": "Validate a full person name...",
    "parameters": {
        "type": "object",
        "properties": {
            "full_name": {
                "type": "string",
                "description": "The full name to validate"
            },
            "extract_parts": {
                "type": "boolean",
                "description": "Whether to extract first and last name parts",
                "default": False
            }
        },
        "required": ["full_name"]
    }
}
```

## Tool Orchestration in Registration Flow

### 35-Step Registration Process

The tools are orchestrated through a 35-step workflow defined in `registration_routines.py`:

1. **Steps 1-2**: Name validation using `person_name_validation`
2. **Step 3**: DOB validation using `child_dob_validation`  
3. **Step 5**: Medical validation using `medical_issues_validation`
4. **Steps 12-15**: Address validation using `address_validation`, `address_lookup`
5. **Step 29**: Payment token creation using `create_payment_token`
6. **Step 29**: Database write using `update_reg_details_to_db`
7. **Step 30**: Kit requirement check using `check_if_kit_needed`
8. **Step 33**: Shirt number check using `check_shirt_number_availability`
9. **Step 34**: Photo upload using `upload_photo_to_s3`

### Tool Chaining Examples

```python
# Example: Address collection flow
1. collect_postcode() → postcode_validation
2. collect_house_number() → address_lookup  
3. confirm_address() → address_validation
4. store_address() → update_reg_details_to_db

# Example: Payment flow
1. collect_payment_day() → create_payment_token
2. store_registration() → update_reg_details_to_db
3. send_payment_link() → send_sms_payment_link
```

## Performance and Reliability

### Retry Mechanisms

The system includes retry logic for AI calls with exponential backoff:

```python
def retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            ai_response = ai_call_func(*args)
            return parse_response(ai_response)
        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay * (2 ** attempt))
            else:
                return error_response(e)
```

### Caching and Optimization

- **Session Context**: Maintains conversation state
- **Tool Response Caching**: Avoids duplicate validations
- **Database Connection Pooling**: Efficient Airtable operations
- **S3 Optimization**: Async photo uploads

## Security Considerations

### Input Validation
- Pydantic model validation for all inputs
- SQL injection prevention through parameterized queries
- File upload restrictions and scanning
- Phone number and email format validation

### Data Protection
- PII handling in accordance with GDPR
- Secure S3 bucket configurations
- Encrypted communication with external services
- Access control for sensitive operations

### API Security
- Environment-based configuration
- API key rotation support
- Rate limiting on external service calls
- Error message sanitization

## Future Enhancements

### Planned Tool Additions
1. **Email Validation Tool**: Enhanced email verification
2. **Photo Recognition Tool**: Automated photo validation
3. **Duplicate Detection Tool**: Prevent duplicate registrations
4. **Audit Trail Tool**: Track registration changes
5. **Notification Tools**: Multi-channel communication

### Architecture Improvements
1. **MCP Integration**: Model Context Protocol support
2. **Tool Versioning**: Backward compatibility
3. **Async Tool Execution**: Improved performance
4. **Tool Metrics**: Usage analytics and monitoring
5. **Dynamic Tool Loading**: Runtime tool registration

## Conclusion

The UTJFC Registration Agent tool ecosystem represents a sophisticated, well-architected system with clear separation of concerns, robust error handling, and comprehensive external service integrations. The 14+ tools work together to provide a complete registration solution that handles everything from data validation to payment processing and photo management.

The system's strength lies in its modular design, comprehensive validation, and seamless integration with external services, making it a robust foundation for grassroots football club registration management.