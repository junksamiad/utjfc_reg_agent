# Backend Low-Level Design (LLD)
## UTJFC Registration Agent Backend System

### Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Server Implementation](#core-server-implementation)
3. [API Endpoints Deep Dive](#api-endpoints-deep-dive)
4. [Agent Orchestration System](#agent-orchestration-system)
5. [Session & State Management](#session--state-management)
6. [Error Handling & Retry Mechanisms](#error-handling--retry-mechanisms)
7. [Asynchronous Processing](#asynchronous-processing)
8. [External Service Integration](#external-service-integration)
9. [Tool System Architecture](#tool-system-architecture)
10. [Database Operations](#database-operations)
11. [Webhook Processing](#webhook-processing)
12. [Security Implementation](#security-implementation)
13. [Performance Optimizations](#performance-optimizations)
14. [Testing & Development Features](#testing--development-features)
15. [Deployment Configuration](#deployment-configuration)

---

## Architecture Overview

### Technology Stack
- **Framework**: FastAPI 0.104+
- **Python Version**: 3.9+
- **ASGI Server**: Uvicorn
- **Async Support**: Python asyncio + threading
- **Validation**: Pydantic v2
- **AI Integration**: OpenAI SDK (Responses API)

### Backend Structure
```
backend/
├── server.py                    # Main application (2,121 lines)
├── registration_agent/          # Registration-specific logic
│   ├── registration_agents.py   # Agent definitions
│   ├── registration_routines.py # 35-step workflow
│   ├── responses_reg.py         # Registration chat loops
│   ├── routing_validation.py    # Code validation logic
│   └── tools/                   # Registration tools
├── urmston_town_agent/          # Generic agent system
│   ├── agents.py                # Base agent class
│   ├── responses.py             # Generic chat loop
│   ├── chat_history.py          # Session management
│   └── tools/                   # Generic tools
└── requirements.txt             # Dependencies
```

---

## Core Server Implementation

### 1. Main Server File Structure (`server.py`)

#### 1.1 Import Section (Lines 1-30)
```python
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, tempfile, asyncio, threading, time
from datetime import datetime
```

#### 1.2 Retry Mechanism Functions (Lines 33-221)
- **Generic Retry**: `retry_ai_call_with_parsing()` 
- **Re-registration Retry**: `retry_rereg_ai_call_with_parsing()`
- **Exponential Backoff**: 1s → 2s → 4s → 8s

#### 1.3 Background Processing (Lines 224-360)
- **Status Store**: Thread-safe in-memory tracking
- **Photo Processing**: Async validation and upload
- **Threading**: Daemon threads for non-blocking operations

#### 1.4 Data Models (Lines 365-369)
```python
class UserPayload(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    routine_number: Optional[int] = None
    last_agent: Optional[str] = None
```

---

## API Endpoints Deep Dive

### 1. Health & Status Endpoints

#### `GET /` (Line 460)
```python
@app.get("/")
async def root():
    return {"message": "UTJFC registration agent API"}
```

#### `GET /health` (Line 464)
- **Purpose**: Kubernetes/Docker health checks
- **Response**: `{"status": "healthy"}`

### 2. Upload Endpoints

#### `POST /upload-async` (Lines 474-520)
```python
@app.post("/upload-async")
async def upload_file_async_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    routine_number: Optional[int] = Form(None),
    last_agent: Optional[str] = Form(None)
):
    # Immediate response
    # Spawn background thread
    # Return processing status
```

**Flow**:
1. Save file temporarily
2. Start background thread
3. Return immediate response
4. Process with AI in background
5. Update status for polling

#### `GET /upload-status/{session_id}` (Lines 468-472)
- **Purpose**: Poll for async upload status
- **Response Structure**:
```json
{
    "status": "processing|complete|error",
    "response": "AI response or error message",
    "complete": boolean,
    "error": boolean
}
```

### 3. Main Chat Endpoint (`POST /chat`)

#### Implementation (Lines 538-1287)
```python
@app.post("/chat", response_model=None)
async def chat_endpoint(payload: UserPayload):
    current_session_id = payload.session_id or DEFAULT_SESSION_ID
```

#### Request Flow Logic:
1. **Routine Continuation** (Lines 551-695)
   - Check for `routine_number` in request
   - Create dynamic agent with routine instructions
   - Process with retry mechanism
   - Handle special routine 22 (age routing)

2. **Agent Continuation** (Lines 698-803)
   - Check `last_agent` parameter
   - Resume appropriate registration flow
   - Maintain conversation context

3. **Testing Mode** (Lines 806-1026)
   - "lah" cheat code implementation
   - Pre-populates 28 routines of data
   - Jumps to payment setup (routine 29)

4. **Initial Routing** (Lines 1028-1287)
   - Registration code validation
   - Agent selection (new vs re-registration)
   - Error handling for invalid codes

### 4. Session Management

#### `POST /clear` (Lines 1394-1399)
```python
@app.post("/clear")
async def clear_endpoint():
    clear_session_history()
    return {"message": "Chat history cleared"}
```

### 5. Agent Management

#### `GET /agent/status` (Lines 1401-1425)
```python
@app.get("/agent/status")
async def get_agent_status():
    return {
        "current_agent": current_agent_type,
        "mode": "mcp" if current_agent.use_mcp else "local",
        "backend": "urmston_town_conversational_backend"
    }
```

#### `POST /agent/mode` (Lines 1428-1452)
- Switch between local and MCP modes
- Updates global agent instance

---

## Agent Orchestration System

### 1. Agent Types

#### 1.1 Generic Urmston Town Agent
```python
local_agent = Agent(
    name="UTJFC Registration Assistant (Local)",
    model="gpt-4o-mini",
    instructions=INSTRUCTIONS,
    tools=["airtable_database_operation"],
    use_mcp=False
)
```

#### 1.2 Registration Agents
```python
# New registration agent (200 codes)
new_registration_agent = Agent(
    name="UTJFC New Player Registration Assistant",
    model="gpt-4o-mini",
    instructions=registration_system_prompt,
    tools=[/* 15+ specialized tools */]
)

# Re-registration agent (100 codes)
re_registration_agent = Agent(
    name="UTJFC Re-registration Assistant",
    model="gpt-4o-mini",
    instructions=re_registration_system_prompt,
    tools=["address_validation", "address_lookup"]
)
```

### 2. Dynamic Agent Creation

#### Routine-Based Agents (server.py:574-617)
```python
dynamic_agent = Agent(
    name=new_registration_agent.name,
    model=new_registration_agent.model,
    instructions=routines.get_instructions_with_routine(routine_message),
    tools=new_registration_agent.tools,
    use_mcp=new_registration_agent.use_mcp,
    mcp_server_url=new_registration_agent.mcp_server_url
)
```

### 3. Agent Routing Logic

#### Registration Code Validation (routing_validation.py)
```python
def validate_and_route_registration(user_message: str) -> dict:
    # Pattern: [PREFIX]-[TEAM]-[AGE_GROUP]-[SEASON][-PLAYER_NAME]
    # 100-Tigers-U13-2526-Jack-Grealish (re-registration)
    # 200-Lions-U10-2526 (new registration)
```

---

## Session & State Management

### 1. Implementation (chat_history.py)

#### Core Functions:
```python
# Session data structure
sessions = {}  # In-memory storage

def get_session_history(session_id: str) -> List[Dict]:
    """Retrieve conversation history"""
    
def add_message_to_session_history(session_id: str, role: str, content: str):
    """Add message to history"""
    
def set_session_context(session_id: str, context_data: dict):
    """Store registration context"""
```

### 2. Message Format
```python
{
    "role": "user|assistant|system",
    "content": "message content"
}
```

### 3. Context Persistence
- Registration data stored in session context
- Maintained across agent switches
- Used for routine continuity

---

## Error Handling & Retry Mechanisms

### 1. AI Call Retry Implementation

#### retry_ai_call_with_parsing() (server.py:33-121)
```python
def retry_ai_call_with_parsing(
    ai_call_func, *args, 
    max_retries=3, 
    delay=1.0, 
    session_id="unknown", 
    call_type="AI"
):
    for attempt in range(max_retries + 1):
        try:
            # Call AI function
            ai_response = ai_call_func(*args)
            
            # Parse response
            if hasattr(ai_response, 'output'):
                # Extract structured JSON
                text_content = ai_response.output[0].content[0].text
                structured_response = json.loads(text_content)
                
                if 'agent_final_response' in structured_response:
                    return True, ai_response, parsed_content, routine_number
                    
        except Exception as e:
            # Exponential backoff
            wait_time = delay * (2 ** attempt)
            time.sleep(wait_time)
            
    return False, None, error_message, None
```

### 2. Parse Strategies
1. **Structured JSON**: Primary parsing method
2. **Raw Text Fallback**: When JSON parsing fails
3. **Error Response**: User-friendly error messages

### 3. Logging Pattern
```python
print(f"--- Session [{session_id}] {call_type} AI call attempt {attempt + 1}/{max_retries + 1} ---")
```

---

## Asynchronous Processing

### 1. Photo Upload Background Processing

#### Thread Management (server.py:224-240)
```python
upload_status_store = {}
status_lock = threading.Lock()

def update_upload_status(session_id: str, status: dict):
    with status_lock:
        upload_status_store[session_id] = {
            **status,
            "timestamp": datetime.now().isoformat()
        }
```

#### Background Function (server.py:241-360)
```python
def process_photo_background(
    session_id: str, 
    temp_file_path: str, 
    routine_number: int, 
    last_agent: str
):
    try:
        # Update status
        update_upload_status(session_id, {
            "status": "processing",
            "response": "Processing photo with AI..."
        })
        
        # Add to session history
        add_message_to_session_history(
            session_id, "user", 
            f"[File uploaded: {temp_file_path}]"
        )
        
        # Route to AI agent
        # Process with retry mechanism
        # Update final status
    except Exception as e:
        update_upload_status(session_id, {
            "status": "error",
            "error": True,
            "response": str(e)
        })
```

### 2. Threading Implementation
```python
background_thread = threading.Thread(
    target=process_photo_background,
    args=(session_id, temp_file.name, routine_number, last_agent)
)
background_thread.daemon = True  # Won't block shutdown
background_thread.start()
```

---

## External Service Integration

### 1. OpenAI Integration
- **Via**: Agent response functions
- **Models**: gpt-4o-mini (primary)
- **Retry**: Exponential backoff on failures

### 2. Airtable Operations
- **Via**: Tool functions
- **Tables**: registrations_2526, team_info
- **Operations**: CRUD, validation queries

### 3. GoCardless Integration
- **Webhook Endpoint**: `/webhooks/gocardless`
- **Events Handled**:
  - billing_requests.fulfilled
  - subscriptions.created
  - payments.confirmed
  - mandates.active

### 4. AWS S3 Integration
- **Via**: upload_photo_to_s3 tool
- **Features**: HEIC conversion, metadata storage

### 5. Twilio SMS
- **Via**: send_sms_payment_link tool
- **Background**: Async sending to avoid delays

---

## Tool System Architecture

### 1. Tool Organization

#### Generic Tools (urmston_town_agent/tools/)
```python
tools = ["airtable_database_operation"]
```

#### Registration Tools (registration_agent/tools/registration_tools/)
```python
tools = [
    "address_validation",
    "address_lookup", 
    "create_signup_payment_link",
    "create_payment_token",
    "update_reg_details_to_db",
    "check_shirt_number_availability",
    "update_kit_details_to_db",
    "upload_photo_to_s3",
    "update_photo_link_to_db",
    "send_sms_payment_link",
    "check_if_kit_needed",
    "person_name_validation",
    "child_dob_validation",
    "postcode_validation",
    "medical_issues_validation"
]
```

### 2. Tool Execution Pattern

#### Local Mode
```python
# Direct function import and execution
from registration_agent.tools.registration_tools import (
    address_validation,
    create_payment_token
)

# Execute via agent's tool mapping
result = tool_functions[function_name](**arguments)
```

#### MCP Mode
```python
# JSON-RPC calls to external MCP server
# Server URL: http://localhost:8002/sse (dev)
# Or: https://utjfc-mcp-server.replit.app/mcp (prod)
```

---

## Database Operations

### 1. Airtable Schema (registrations_2526)

#### Core Fields
```python
{
    # Parent Information
    "parent_full_name": str,
    "parent_phone": str,
    "parent_email": str,
    "parent_dob": str,
    "parent_address": str,
    "parent_relationship": str,
    
    # Child Information
    "child_full_name": str,
    "child_dob": str,
    "child_gender": str,
    "medical_issues": str,
    "child_address": str,
    
    # Registration Details
    "team": str,
    "age_group": str,
    "season": str,
    "previous_team": str,
    
    # Payment Information
    "billing_request_id": str,
    "payment_token": str,
    "signing_on_fee_paid": str,
    "mandate_authorised": str,
    "subscription_activated": str,
    "monthly_subscription_amount": float,
    "preferred_payment_day": int,
    
    # Kit Information
    "kit_size": str,
    "shirt_number": int,
    "kit_type": str,
    
    # Photo Information
    "photo_s3_url": str,
    "photo_filename": str,
    
    # System Fields
    "registration_status": str,
    "created_date": datetime,
    "conversation_history": str
}
```

### 2. Database Operations

#### Query Patterns
```python
# Sibling detection
formula = f"AND({{parent_full_name}} = '{parent_name}', {{player_last_name}} = '{surname}')"

# Team validation
formula = f"AND({{team_name}} = '{team}', {{age_groups}} = '{age_group}')"

# Shirt number availability
formula = f"AND({{team}} = '{team}', {{age_group}} = '{age_group}', {{shirt_number}} = {number})"
```

---

## Webhook Processing

### 1. GoCardless Webhook Handler (server.py:1564-2099)

#### Webhook Authentication
```python
# Verify webhook signature
webhook_secret = os.getenv('GOCARDLESS_WEBHOOK_SECRET')
provided_signature = request.headers.get('Webhook-Signature')
# HMAC validation
```

#### Event Processing Flow
```python
for event in webhook_data.get('events', []):
    event_type = event['resource_type']
    
    if event_type == 'billing_requests':
        # Process billing request events
    elif event_type == 'subscriptions':
        # Process subscription events
    elif event_type == 'payments':
        # Process payment confirmations
    elif event_type == 'mandates':
        # Process mandate activations
```

#### Database Updates
```python
# Update registration record based on event
airtable_updates = {
    'signing_on_fee_paid': 'Y',
    'mandate_authorised': 'Y',
    'subscription_activated': 'Y',
    'registration_status': 'active'
}
```

### 2. Sibling Discount Processing
- Applied during subscription activation
- 10% discount on monthly fees
- Automatic detection via parent/surname matching

---

## Security Implementation

### 1. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Webhook Security
- HMAC signature verification
- Secret key validation
- Event authenticity checks

### 3. Environment Variables
```python
# Sensitive data in .env
OPENAI_API_KEY=sk-...
AIRTABLE_API_KEY=pat...
GOCARDLESS_TOKEN=live_...
AWS_ACCESS_KEY_ID=AKIA...
TWILIO_AUTH_TOKEN=...
```

---

## Performance Optimizations

### 1. Async Request Handling
- FastAPI async endpoints
- Non-blocking I/O operations
- Background task processing

### 2. Threading for Long Operations
- Photo uploads processed in background
- SMS sending in separate threads
- Status polling for progress tracking

### 3. Retry Mechanisms
- Prevent cascading failures
- Exponential backoff reduces API load
- Graceful degradation on errors

### 4. In-Memory Caching
- Upload status store
- Session data caching
- Agent instance reuse

---

## Testing & Development Features

### 1. "lah" Cheat Code (server.py:806-1026)
```python
if payload.user_message.strip().lower() == "lah":
    # Inject test registration code
    inject_structured_registration_data(
        session_id, 
        "200-leopards-u9-2526"
    )
    # Pre-populate 28 routines
    # Jump to payment setup
```

### 2. Test Data Population
- Complete registration data
- Valid test values for all fields
- Skips to routine 29 (payment)

### 3. Development Endpoints
- `/webhooks/gocardless/test` - Webhook testing
- Agent mode switching for debugging

---

## Deployment Configuration

### 1. Docker Support
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Production Settings
```python
# Uvicorn configuration
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
```

### 3. Environment Configuration
- Development: `.env` file
- Production: Environment variables
- Secrets management via AWS/platform

### 4. Scalability Considerations
- Stateless design (except sessions)
- Horizontal scaling ready
- External service resilience

---

## Key Implementation Patterns

### 1. Request-Response Flow
```
Request → Validation → Session Management → Agent Routing → 
AI Processing → Tool Execution → Response Parsing → 
Session Update → Client Response
```

### 2. Error Handling Strategy
```python
try:
    # Main operation
    result = process_request()
except SpecificError as e:
    # Handle known errors
    log_error(e)
    return error_response()
except Exception as e:
    # Handle unexpected errors
    log_critical(e)
    return generic_error()
finally:
    # Cleanup operations
    cleanup_resources()
```

### 3. Agent Switching Pattern
```python
# Check continuation signals
if routine_number:
    # Continue with routine
elif last_agent:
    # Continue with agent
else:
    # Check for registration code
    # Route to appropriate agent
```

---

## Conclusion

This Low-Level Design document provides a comprehensive technical view of the UTJFC Registration Agent backend implementation. The system demonstrates sophisticated patterns including:

- **Multi-agent orchestration** with seamless switching
- **Asynchronous processing** for long-running operations  
- **Robust error handling** with retry mechanisms
- **External service integration** with multiple providers
- **Scalable architecture** ready for production deployment

The implementation successfully balances complexity with maintainability, providing a solid foundation for the football club's registration system.