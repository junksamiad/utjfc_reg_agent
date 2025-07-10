# External Integrations Low-Level Design (LLD)

## Overview

This document provides comprehensive technical analysis of all external service integrations in the UTJFC Registration Backend. The system integrates with 6 major external services to provide a complete football club registration solution.

## Table of Contents

1. [Airtable Database Integration](#1-airtable-database-integration)
2. [GoCardless Payment Processing](#2-gocardless-payment-processing)
3. [Twilio SMS Services](#3-twilio-sms-services)
4. [AWS S3 Photo Storage](#4-aws-s3-photo-storage)
5. [Google Places API Address Validation](#5-google-places-api-address-validation)
6. [OpenAI AI Services](#6-openai-ai-services)
7. [MCP Server Integration](#7-mcp-server-integration)
8. [Environment Configuration](#8-environment-configuration)
9. [Error Handling Patterns](#9-error-handling-patterns)
10. [Monitoring & Health Checks](#10-monitoring--health-checks)

---

## 1. Airtable Database Integration

### Configuration & Authentication

**Location**: `backend/registration_agent/tools/airtable/`

**Configuration Pattern**:
```python
# airtable_setup.py
AIRTABLE_BASE_ID = "appBLxf3qmGIBc6ue"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
```

**Authentication Method**: 
- Personal Access Token (PAT) via environment variable
- Uses `pyairtable==2.3.3` SDK
- Base ID hardcoded for security (prevents accidental database access)

### API Patterns

**Client Initialization**:
```python
def get_airtable_client():
    if not AIRTABLE_API_KEY:
        raise ValueError("AIRTABLE_API_KEY environment variable is required")
    return Api(AIRTABLE_API_KEY)
```

**Table Access Pattern**:
```python
def get_table(season: str):
    client = get_airtable_client()
    table_config = TABLES_CONFIG[season]
    return client.table(AIRTABLE_BASE_ID, table_config["table_id"])
```

### Data Flow Architecture

**AI Agent Integration**:
1. **Natural Language Processing**: Uses OpenAI Responses API with code interpreter
2. **Data Validation**: Validates against schema before operations
3. **Operation Planning**: Generates validated operation plans
4. **Execution**: Executes operations via pyairtable SDK

**Supported Operations**:
- `table.all()` - Retrieve all records with optional formula filtering
- `table.first()` - Get first matching record
- `table.get(record_id)` - Retrieve by record ID
- `table.search()` - Search by field values
- `table.create()` - Create new records
- `table.update()` - Update existing records
- `table.delete()` - Delete records
- `table.count()` - Count records with optional filtering

### Schema Management

**Season-Based Configuration**:
```python
TABLES_CONFIG = {
    "2526": {
        "table_name": "registrations_2526",
        "table_id": "tbl1D7hdjVcyHbT8a",
        "season": "2025-26"
    }
}
```

**Data Normalization Rules**:
- Age groups: "u10s" → "u10" (lowercase u)
- Team names: "tigers" → "Tigers" (proper case)
- Medical issues: "yes/no" → "Y/N"
- Names: Proper case + space normalization

### Error Handling

**Standardized Response Format**:
```python
def format_airtable_error(error):
    return {
        "status": "error",
        "message": f"Airtable API error: {str(error)}",
        "data": None
    }
```

**Retry Logic**: No automatic retries at integration level (handled by parent system)

---

## 2. GoCardless Payment Processing

### Configuration & Authentication

**Location**: `backend/registration_agent/tools/registration_tools/gocardless_payment.py`

**Authentication**:
```python
GOCARDLESS_API_KEY = os.getenv("GOCARDLESS_API_KEY")
headers = {
    "Authorization": f"Bearer {gocardless_api_key}",
    "Content-Type": "application/json",
    "GoCardless-Version": "2015-07-06"
}
```

**Environment Support**:
- Sandbox: For testing
- Live: For production payments
- Environment configured via `GOCARDLESS_ENVIRONMENT`

### Payment Flow Architecture

**Two-Stage Payment Setup**:

1. **Billing Request Creation**:
```python
def create_billing_request(player_full_name, team, age_group, signing_fee_amount=4500, monthly_amount=2750)
```
- Creates one-off payment (signing fee: £45.00)
- Sets up mandate for monthly subscription (£27.50)
- Returns billing request ID

2. **Flow Creation for Authorization**:
```python
def create_billing_request_flow(billing_request_id, parent_email, parent_first_name, ...)
```
- Generates payment authorization URL
- Pre-fills customer data
- Returns authorization URL for SMS delivery

### Subscription Management

**Smart Start Date Logic**:
```python
def activate_subscription(mandate_id, registration_record)
```

**Business Rules**:
- **3-day advance notice**: GoCardless requirement compliance
- **Interim subscriptions**: For late-month registrations
- **Season policy**: No payments until September 2025 for early registrations
- **Smart fairness logic**: Avoids unfair partial month charges

**Sibling Discount Implementation**:
```python
# 10% discount for multiple children from same parent
if len(existing_siblings) > 0:
    monthly_amount = monthly_amount * 0.9
    print(f"🎉 SIBLING DISCOUNT APPLIED")
```

### Webhook Integration

**Webhook Endpoint**: `/webhooks/gocardless`

**Event Processing**:
```python
async def process_gocardless_event(event: dict):
    event_id = event.get('id')
    resource_type = event.get('resource_type')
    action = event.get('action')
```

**Supported Events**:
- `payments.confirmed`: Payment completion
- `mandate_active`: Mandate authorization complete
- `billing_request_fulfilled`: Full process completion

**Security**:
- HMAC signature verification (configurable)
- Development mode fallback
- Request logging for debugging

### Error Handling

**Comprehensive Error Responses**:
```python
{
    "success": False,
    "message": "User-friendly error message",
    "billing_request_id": "",
    "billing_request_data": {},
    "player_full_name": player_full_name,
    "team": team,
    "age_group": age_group
}
```

**Request Exception Handling**:
- Network timeouts (30s timeout)
- API rate limiting
- Validation errors
- Authentication failures

---

## 3. Twilio SMS Services

### Configuration & Authentication

**Location**: `backend/registration_agent/tools/registration_tools/send_sms_payment_link_tool.py`

**Authentication**:
```python
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(account_sid, auth_token)
```

### Phone Number Processing

**UK Number Formatting**:
```python
def format_uk_phone_for_twilio(phone: str) -> str:
    # Converts: 07123456789 -> +447123456789
    # Handles: +44 7123 456789, 447123456789, etc.
```

**Validation**:
```python
def validate_uk_mobile(phone: str) -> bool:
    uk_mobile_pattern = r'^\+447[0-9]{9}$'
    return bool(re.match(uk_mobile_pattern, formatted))
```

### Message Composition

**Template Structure**:
```python
sms_message = (
    f"Hi {parent_name}, it's the registration assistant from Urmston Town Juniors FC! "
    f"{child_name}'s registration is almost complete. "
    f"Please complete your payment and setup monthly subscription to secure your place: "
    f"{payment_link}"
)
```

**Payment Link Generation**:
```python
# Hard-coded production CloudFront URL for reliability
payment_base_url = 'https://d1ahgtos8kkd8y.cloudfront.net/api'
payment_link = f"{payment_base_url}/reg_setup/{billing_request_id}"
```

### Delivery Tracking

**Metrics Collection**:
```python
sms_metrics = {
    'sms_sent_at': current_time,
    'sms_delivery_status': 'sent',
    'sms_delivery_error': '',
    'twilio_message_sid': message.sid,
    'formatted_phone': formatted_phone,
    'child_name': child_name,
    'parent_name': parent_name
}
```

**Queue-Based Logging**:
- Non-blocking metrics collection
- Background database updates
- SQLite queue for reliability

### Error Handling

**Twilio-Specific Errors**:
```python
except TwilioException as e:
    error_msg = f"Twilio error: {str(e)}"
    # Queue error metrics for background processing
```

**Fallback Strategies**:
- Invalid number format detection
- Service unavailability handling
- Rate limiting compliance

---

## 4. AWS S3 Photo Storage

### Configuration & Authentication

**Location**: `backend/registration_agent/tools/registration_tools/upload_photo_to_s3_tool.py`

**Environment Detection**:
```python
is_production = (
    os.environ.get('AWS_EXECUTION_ENV') is not None or
    os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is not None or
    os.environ.get('AWS_INSTANCE_ID') is not None or
    os.path.exists('/opt/elasticbeanstalk') or
    os.environ.get('EB_IS_COMMAND_LEADER') is not None
)
```

**Authentication Strategy**:
- **Local Development**: AWS Profile (`footballclub`)
- **Production**: IAM Role (EC2/Elastic Beanstalk)
- **Automatic Detection**: Prevents ProfileNotFound errors

### File Processing Pipeline

**HEIC Conversion**:
```python
def _convert_heic_to_jpeg(file_path: str) -> str:
    with Image.open(file_path) as img:
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(jpeg_path, 'JPEG', quality=90, optimize=True)
```

**Requirements**:
- `pillow==10.1.0`: Core image processing
- `pillow-heif==0.17.0`: HEIC format support
- Graceful degradation if HEIC support unavailable

### Upload Strategy

**Filename Generation**:
```python
clean_name = "".join(c for c in player_full_name if c.isalnum()).lower()
clean_team = "".join(c for c in team if c.isalnum()).lower()
clean_age_group = "".join(c for c in age_group if c.isalnum()).lower()
filename = f"{clean_name}_{clean_team}_{clean_age_group}{file_extension}"
```

**Metadata Attachment**:
```python
ExtraArgs={
    'ContentType': _get_content_type(file_extension),
    'Metadata': {
        'record_id': validated_data.record_id,
        'player_name': validated_data.player_full_name,
        'team': validated_data.team,
        'age_group': validated_data.age_group,
        'upload_timestamp': datetime.now().isoformat(),
        'original_extension': original_extension
    }
}
```

### Session History Integration

**File Path Extraction**:
```python
# Look for UPLOADED_FILE_PATH message in session history
for message in reversed(session_history):
    if (message.get('role') == 'system' and 
        message.get('content', '').startswith('UPLOADED_FILE_PATH:')):
        file_path = message['content'].replace('UPLOADED_FILE_PATH:', '').strip()
        break
```

### Cleanup Strategy

**Automatic File Removal**:
```python
files_to_clean = [file_path]
if original_extension == '.heic' and '_converted.jpg' in file_path:
    original_heic = file_path.replace('_converted.jpg', '.heic')
    if os.path.exists(original_heic):
        files_to_clean.append(original_heic)
```

### Error Handling

**Validation Layers**:
1. **File Existence**: Check file exists before processing
2. **Format Support**: Validate HEIC conversion capability
3. **Upload Validation**: Verify S3 upload success
4. **Cleanup Safety**: Handle cleanup failures gracefully

---

## 5. Google Places API Address Validation

### Configuration & Authentication

**Location**: `backend/registration_agent/tools/registration_tools/address_lookup.py`

**Authentication**:
```python
google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": google_api_key,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.addressComponents"
}
```

### API Integration Pattern

**Places API v1 Text Search**:
```python
url = "https://places.googleapis.com/v1/places:searchText"
payload = {
    "textQuery": search_query,
    "regionCode": "GB",  # UK region constraint
    "languageCode": "en"
}
```

### Address Construction Logic

**Two-Stage Process**:
1. **Postcode Lookup**: Get street/area information
2. **Address Construction**: Combine with house number

```python
def construct_full_address(house_number: str, postcode_address: str, postcode: str):
    parts = [part.strip() for part in postcode_address.split(',')]
    if len(parts) >= 2:
        street_name = parts[0]
        area_parts = parts[1:]
        full_address = f"{house_number} {street_name}, " + ", ".join(area_parts)
```

### Validation & Confidence Scoring

**UK Address Validation**:
```python
uk_indicators = ["UK", "UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES", 
                "LONDON", "MANCHESTER", "BIRMINGHAM", ...]
if not any(keyword in formatted_address.upper() for keyword in uk_indicators):
    return confidence_level = "Low"
```

**Confidence Levels**:
- **High**: Single clear match
- **Medium**: Multiple possible matches
- **Low**: Ambiguous or non-UK address

### Component Extraction

**Structured Data Extraction**:
```python
def extract_address_components_v2(place_data: Dict):
    components = {
        "street_number": "",
        "street_name": "",
        "locality": "",
        "postal_code": "",
        "administrative_area": "",
        "country": ""
    }
```

### Error Handling

**Graceful Degradation**:
- Service unavailability → Generic error message
- Invalid postcode → User-friendly validation message
- Rate limiting → Temporary unavailability message

---

## 6. OpenAI AI Services

### Configuration & Authentication

**Authentication**:
```python
from openai import OpenAI
client = OpenAI()  # Uses OPENAI_API_KEY environment variable
```

### Model Configuration

**Responses API Usage**:
```python
response = client.responses.create(
    model="gpt-4.1",
    instructions=system_instructions,
    input=f"Parse and validate data for: {query}",
    tools=self.tools
)
```

### AI Retry Logic

**Exponential Backoff Pattern**:
```python
def retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0):
    for attempt in range(max_retries + 1):
        try:
            ai_full_response_object = ai_call_func(*args)
            # Parse and validate response
            if parsing_successful:
                return True, ai_response, parsed_content, routine_number
        except Exception as parse_error:
            if attempt == max_retries:
                return False, ai_response, error_message, None
            time.sleep(delay * (2 ** attempt))  # Exponential backoff
```

### Code Interpreter Integration

**Tool Configuration**:
```python
self.tools = [
    {
        "type": "code_interpreter",
        "container": {"type": "auto"}
    }
]
```

### Response Parsing

**Multi-Strategy Extraction**:
1. **Structured JSON**: Primary parsing method
2. **Pattern Matching**: Regex-based fallback
3. **Balanced Braces**: Complex dictionary extraction
4. **Manual Field Extraction**: Last resort parsing

---

## 7. MCP Server Integration

### Architecture Overview

**Location**: `mcp_server/server.py`

**Purpose**: External integrations server using Model Context Protocol
- Deployed on Replit: `https://utjfc-mcp-server.replit.app/mcp`
- Provides isolated environment for external service calls
- Enables OpenAI Responses API integration

### Protocol Implementation

**JSON-RPC 2.0 Support**:
```python
async def handle_jsonrpc_request(request_data: dict) -> dict:
    jsonrpc = request_data.get("jsonrpc", "2.0")
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
```

**Supported Methods**:
- `initialize`: Protocol handshake
- `tools/list`: Available tools enumeration
- `tools/call`: Tool execution

### Tool Definition

**Airtable Database Tool**:
```python
AIRTABLE_TOOL = {
    "name": "airtable_database_operation",
    "description": "Execute CRUD operations on UTJFC registration database",
    "inputSchema": {
        "type": "object",
        "properties": {
            "season": {"type": "string", "enum": ["2526", "2425"]},
            "query": {"type": "string"}
        },
        "required": ["season", "query"]
    }
}
```

### Authentication & Security

**Optional Token-Based Auth**:
```python
def check_auth(request: Request) -> bool:
    if not MCP_AUTH_TOKEN:
        return True  # No auth configured
    
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == MCP_AUTH_TOKEN
```

**CORS Configuration**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.openai.com", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

---

## 8. Environment Configuration

### Configuration Template

**Location**: `backend/env.production.template`

**Required Environment Variables**:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MCP Server Configuration
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
USE_MCP=true

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=appBLxf3qmGIBc6ue

# GoCardless Payment Configuration
GOCARDLESS_ACCESS_TOKEN=your_gocardless_access_token_here
GOCARDLESS_ENVIRONMENT=sandbox  # or 'live'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=eu-north-1
S3_BUCKET_NAME=utjfc-player-photos

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Server Configuration
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production

# Security Configuration
SESSION_SECRET_KEY=your_random_secret_key_here
CORS_ORIGINS=["https://urmstontownjfc.co.uk"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=JSON
```

### Secrets Management Strategy

**Development vs Production**:
- **Development**: `.env` file (git-ignored)
- **Production**: Environment variables via AWS Elastic Beanstalk
- **Template**: `env.production.template` for reference

**Security Considerations**:
- No secrets in version control
- Environment-specific configurations
- Fallback defaults where appropriate

---

## 9. Error Handling Patterns

### Standardized Error Response Format

**Common Pattern Across All Integrations**:
```python
{
    "success": False,
    "message": "User-friendly error message",
    "error_code": "SPECIFIC_ERROR_TYPE",
    "data": null,
    "debug_info": {
        "exception_type": "RequestException",
        "service": "airtable",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

### Service-Specific Error Handling

**Airtable Errors**:
- Rate limiting: Exponential backoff
- Authentication failures: Clear credential messaging
- Schema validation: Detailed field-level errors

**GoCardless Errors**:
- Payment failures: User-friendly payment messaging
- Webhook validation: Security error logging
- Mandate issues: Clear authorization guidance

**Twilio Errors**:
- Invalid numbers: Format validation guidance
- Service outages: Fallback notification strategies
- Rate limiting: Queue-based retry mechanisms

**AWS S3 Errors**:
- Upload failures: Storage quota and permission issues
- Authentication: IAM role vs profile detection
- File processing: HEIC conversion fallbacks

**Google Places Errors**:
- API quota: Service unavailability messaging
- Invalid addresses: Validation guidance
- Rate limiting: Request throttling

### Retry Strategies

**AI Call Retries**:
```python
# Exponential backoff with jitter
delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
time.sleep(delay)
```

**Network Request Retries**:
```python
# Fixed timeout with service-specific handling
timeout = 30  # seconds for most services
timeout = 10  # seconds for address lookup (user-facing)
```

### Logging & Monitoring

**Structured Logging Pattern**:
```python
print(f"--- Session [{session_id}] {service_name} error: {error_message} ---")
print(f"   Request details: {request_summary}")
print(f"   Response status: {response_status}")
print(f"   Retry attempt: {attempt}/{max_retries}")
```

---

## 10. Monitoring & Health Checks

### CloudWatch Integration

**Location**: `monitoring/setup-monitoring.sh`

**Configured Alarms**:
- **CPU Utilization**: >80% for 2 periods
- **Environment Health**: <15 (Green=25, Yellow=15, Red=10)
- **5xx Error Rate**: >5 errors per 5 minutes

**SNS Notification Setup**:
```bash
TOPIC_ARN=$(aws sns create-topic --name "utjfc-backend-alerts")
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint admin@domain.com
```

### Health Check Endpoints

**Service Health**: `/health`
```python
@app.get("/health")
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'airtable': check_airtable_health(),
            'gocardless': check_gocardless_health(),
            'twilio': check_twilio_health(),
            's3': check_s3_health(),
            'google_places': check_google_places_health()
        }
    }
```

**Webhook Health**: `/webhooks/gocardless/test`
```python
@app.get("/webhooks/gocardless/test")
async def test_webhook_endpoint():
    return {"status": "Webhook endpoint is accessible", "timestamp": "2025-01-27"}
```

### Performance Monitoring

**Instance Configuration**:
- **Current**: t3.small (2GB RAM) - insufficient for AI photo processing
- **Recommended**: t3.medium (4GB RAM) minimum
- **Auto-scaling**: CPU-based (70% upper, 20% lower threshold)
- **Redundancy**: Minimum 2 instances recommended

**Resource Monitoring**:
- Memory usage during photo processing
- AI response times and retry rates
- Database connection pooling
- External service response times

### Reliability Patterns

**Circuit Breaker Pattern**: Not implemented (future enhancement)

**Graceful Degradation**:
- Address lookup failure → Manual entry fallback
- Photo upload failure → Registration continues without photo
- SMS delivery failure → Email fallback (future enhancement)
- Payment service outage → Manual payment link generation

**Data Consistency**:
- Airtable as source of truth
- Eventual consistency for metrics
- Idempotent operations where possible
- Webhook replay capability for payment events

---

## Dependencies Summary

### Core External Service Libraries

```
# Database and External Services
pyairtable==2.3.3           # Airtable integration
gocardless-pro==3.1.0        # Payment processing
boto3==1.35.90               # AWS S3 integration  
twilio==8.5.0                # SMS services
openai==1.81.0               # AI services

# Image Processing
pillow==10.1.0               # Core image processing
pillow-heif==0.17.0          # HEIC format support

# HTTP and API
httpx==0.28.1                # HTTP client
requests                     # HTTP requests (via dependencies)

# Validation and Utilities
email-validator==2.1.0       # Email validation
pydantic==2.11.4             # Data validation
python-dotenv==1.1.0         # Environment management
```

### Security Dependencies

```
# Security and Authentication
python-jose[cryptography]==3.3.0    # JWT handling
passlib[bcrypt]==1.7.4               # Password hashing
```

---

## Integration Test Coverage

### Manual Test Scripts

**Location**: `backend/test_*.py`

**Available Tests**:
- `test_photo_upload.py`: Comprehensive photo upload testing
- `test_backend_mcp_flow.py`: MCP server integration testing
- `cleanup_test_photos.py`: S3 photo cleanup utilities
- `test_address_flow.py`: Address validation testing
- `test_gocardless.py`: Payment flow testing
- `test_sms_tool.py`: SMS delivery testing

### Automated Testing Strategy

**Integration Test Patterns**:
- Service mocking for development
- Sandbox environments for external services
- End-to-end flow validation
- Error condition simulation

**Test Environment Configuration**:
```bash
# Use sandbox/test endpoints
GOCARDLESS_ENVIRONMENT=sandbox
AWS_PROFILE=footballclub-test
TWILIO_PHONE_NUMBER=+15005550006  # Twilio test number
```

---

## Future Enhancements

### Planned Improvements

1. **Circuit Breaker Pattern**: Implement for external service resilience
2. **Caching Layer**: Redis for frequently accessed data
3. **Rate Limiting**: Implement request throttling
4. **Webhook Replay**: Robust event processing with replay capability
5. **Service Mesh**: Consider Istio for production microservices
6. **Observability**: OpenTelemetry integration for distributed tracing

### Scalability Considerations

1. **Connection Pooling**: Database connection management
2. **Async Processing**: Queue-based background job processing
3. **Load Balancing**: Multi-instance deployment strategy
4. **CDN Integration**: Static asset delivery optimization
5. **Database Sharding**: Multi-season data partitioning

---

*This document represents the current state of external integrations as of January 2025. Regular updates are recommended as services evolve and new integrations are added.*