# Backend Debugging & Testing Low-Level Design (LLD)
## UTJFC Development Tools & Testing Infrastructure

### Table of Contents
1. [Testing Cheat Codes](#testing-cheat-codes)
2. [Session Management Debugging](#session-management-debugging)
3. [Status Monitoring Tools](#status-monitoring-tools)
4. [Production Debugging](#production-debugging)
5. [Development Workflow](#development-workflow)

---

## Testing Cheat Codes

### Overview
The backend implements two production-ready cheat codes for rapid testing of complex registration workflows without requiring full user interaction.

### "lah" Cheat Code (`server.py:806-907`)

#### Purpose
Jumps directly to routine 29 (payment setup) with complete conversation history pre-populated for a fictional player "Seb Martinez".

#### Implementation
```python
# Check for testing cheat code 'lah' (Last Agent Handler)
if payload.user_message.strip().lower() == "lah":
    print(f"--- Session [{current_session_id}] Testing cheat code 'lah' detected - jumping directly to routine 29 (payment setup) with full registration completed ---")
```

#### Pre-populated Test Data
- **Player**: Seb Martinez, 8 years old
- **Team**: Lions U9
- **Parent**: Sarah Martinez
- **Contact**: 07123456789, sarah.martinez@email.com
- **Address**: 123 Test Road, Manchester, M1 1AA
- **Complete Registration**: All routines 1-28 completed

#### Usage
1. Start any chat session
2. Type: `lah`
3. System jumps to routine 29 with full registration context
4. Test payment flow immediately

### "SDH" Cheat Code (`server.py:910-1118`)

#### Purpose  
Jumps directly to routine 34 (photo upload) with complete registration and payment setup pre-populated.

#### Implementation
```python
# Check for extended testing cheat code 'sdh' (Skip to Photo Upload)
if payload.user_message.strip().lower() == "sdh":
    print(f"--- Session [{current_session_id}] Extended testing cheat code 'sdh' detected - jumping directly to routine 34 (photo upload) with full registration completed ---")
```

#### Pre-populated Context
- **Complete Registration**: All routines 1-33 completed
- **Database Record**: Creates actual Airtable record with test data
- **Payment Setup**: Mock payment setup completed
- **Conversation History**: 33 message pairs simulating full registration

#### Advanced Features
```python
# Execute actual tool calls for realistic testing
tool_calls = [
    {
        "id": "call_123",
        "type": "function", 
        "function": {
            "name": "update_reg_details_to_db",
            "arguments": json.dumps({
                "player_first_name": "Seb",
                "player_last_name": "Martinez",
                # ... complete registration data
            })
        }
    }
]
```

#### Usage
1. Start any chat session  
2. Type: `sdh`
3. System creates real database record and jumps to photo upload
4. Test complete photo upload workflow with actual S3 integration

---

## Session Management Debugging

### Chat History Architecture

#### Centralized History Management
```python
# All agents use the same chat history system
from urmston_town_agent.chat_history import (
    get_session_history, 
    add_message_to_session_history,
    clear_session_history
)
```

#### Memory Management (`chat_history.py:7,37`)
```python
MAX_HISTORY_LENGTH = 40  # Total messages (20 turns)

# Automatic cleanup of old messages
while len(history) > MAX_HISTORY_LENGTH * 2:
    history.pop(0)  # Remove oldest message
```

#### Session History Format
```python
# Standard message format
{
    "role": "user|assistant|system",
    "content": "message content",
    "timestamp": "ISO format"
}

# Tool call logging format
{
    "role": "assistant", 
    "content": "🔧 Tool Call: function_name - result_summary"
}
```

### Database Storage Integration

#### Photo Upload Context Storage
During routine 34 (photo upload), the complete conversation history is stored in the database:

```python
# Conversation history saved to Airtable
update_data = {
    "conversation_history": json.dumps(session_history, indent=2)
}
```

#### Session ID Management
```python
# Environment variable for tool access
os.environ['CURRENT_SESSION_ID'] = session_id

# Default session handling
DEFAULT_SESSION_ID = "default_session_id"
```

---

## Status Monitoring Tools

### Upload Status Tracking (`server.py:225-239`)

#### Thread-Safe Status Store
```python
upload_status_store = {}
status_lock = threading.Lock()

def set_upload_status(session_id: str, status: dict):
    """Thread-safe status update"""
    with status_lock:
        upload_status_store[session_id] = status

def get_upload_status(session_id: str) -> dict:
    """Thread-safe status retrieval"""
    with status_lock:
        return upload_status_store.get(session_id, {
            'complete': False, 
            'message': 'Not found'
        })
```

#### Status Progression Tracking
```python
# Processing stages
{
    'complete': False,
    'message': 'Starting photo processing...',
    'step': 'initialization'
}

{
    'complete': False, 
    'message': 'AI agent processing photo...',
    'step': 'ai_processing'
}

{
    'complete': True,
    'message': 'Photo uploaded successfully',
    'step': 'completed',
    'routine_number': 35
}
```

### Real-time Status Endpoint (`server.py:468-472`)

#### Polling Interface
```python
@app.get("/upload-status/{session_id}")
async def get_upload_processing_status(session_id: str):
    """Get the current status of photo upload processing"""
    status = get_upload_status(session_id)
    return status
```

#### Frontend Integration
- **Polling Interval**: 2-3 second intervals
- **Status Display**: Real-time progress updates
- **Error Handling**: Comprehensive error state management

---

## Production Debugging

### Logging Patterns

#### Session-Based Logging
```python
print(f"--- Session [{session_id}] Action description ---")
print(f"--- Background session [{session_id}] Processing step ---")
print(f"✅ Session [{session_id}] Success message ---")
print(f"❌ Session [{session_id}] Error message ---")
```

#### Tool Execution Logging
```python
print(f"🔧 Tool Call: {tool_name}")
print(f"📋 Tool Args: {tool_args}")
print(f"✅ Tool Result: {result_summary}")
print(f"❌ Tool Error: {error_details}")
```

### Health Check Integration

#### Application Health Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "UTJFC Registration Backend is running"
    }
```

#### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1
```

### Error Tracking

#### AI Processing Errors
```python
# Retry mechanism with detailed logging
for attempt in range(max_retries + 1):
    print(f"--- Session [{session_id}] AI call attempt {attempt + 1}/{max_retries + 1} ---")
    try:
        ai_response = ai_call_func(*args)
        return True, ai_response, parsed_content, routine_number
    except Exception as e:
        print(f"--- Session [{session_id}] AI call failed: {e} ---")
```

#### External Service Monitoring
```python
# Service-specific error handling
try:
    s3_client.upload_file(file_path, bucket, filename)
    print("✅ S3 upload successful")
except Exception as e:
    print(f"❌ S3 upload failed: {e}")
    return {"success": False, "error": str(e)}
```

---

## Development Workflow

### Local Testing Sequence

#### 1. Basic Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Cheat Code Testing
```bash
# Test routine 29 (payment setup)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "lah", "session_id": "test_session"}'

# Test routine 34 (photo upload)  
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "sdh", "session_id": "test_session"}'
```

#### 3. Photo Upload Testing
```bash
# Test async photo upload
curl -X POST http://localhost:8000/upload-async \
  -F "file=@test_photo.jpg" \
  -F "session_id=test_session"

# Monitor upload status
curl http://localhost:8000/upload-status/test_session
```

### Session Management Commands

#### Session History Operations
```python
# Get session history
from urmston_town_agent.chat_history import get_session_history
history = get_session_history("session_id")

# Clear session for testing
from urmston_town_agent.chat_history import clear_session_history
clear_session_history("session_id")

# Add test messages
from urmston_town_agent.chat_history import add_message_to_session_history
add_message_to_session_history("session_id", "user", "test message")
```

### Environment Testing

#### Local Development
```python
# Environment detection
is_production = (
    os.environ.get('AWS_EXECUTION_ENV') is not None or
    os.path.exists('/opt/elasticbeanstalk')
)

if not is_production:
    print("🏠 Local environment - using development settings")
```

#### Production Verification
```bash
# Verify production environment variables
eb printenv

# Check application logs
eb logs --all

# Monitor health status
eb health --refresh
```

---

## Troubleshooting Common Issues

### Session State Problems

#### Symptoms
- Lost conversation context
- Routine number resets
- Tool call failures

#### Diagnosis
```python
# Check session history length
history = get_session_history(session_id)
print(f"Session history length: {len(history)}")

# Verify session ID consistency
print(f"Current session ID: {os.environ.get('CURRENT_SESSION_ID')}")
```

### Photo Upload Issues

#### Symptoms
- Status polling timeouts
- Background processing failures
- S3 upload errors

#### Diagnosis
```python
# Check upload status store
status = get_upload_status(session_id)
print(f"Upload status: {status}")

# Verify file path in session history
for message in session_history:
    if message.get('content', '').startswith('UPLOADED_FILE_PATH:'):
        print(f"Found file path: {message['content']}")
```

### AI Processing Failures

#### Symptoms
- Retry mechanism exhaustion
- JSON parsing errors
- Routine number extraction failures

#### Diagnosis
```python
# Check AI response structure
print(f"AI response type: {type(ai_response)}")
print(f"Response output length: {len(ai_response.output) if hasattr(ai_response, 'output') else 'No output'}")

# Verify JSON structure
try:
    parsed = json.loads(ai_response.output[0].content[0].text)
    print(f"Parsed keys: {parsed.keys()}")
except Exception as e:
    print(f"JSON parse error: {e}")
```

---

## Conclusion

The UTJFC backend includes comprehensive debugging and testing infrastructure that supports both development and production operations. The cheat code system enables rapid testing of complex workflows, while the session management and status monitoring tools provide detailed visibility into system operations.

The debugging tools are designed to be production-safe and provide the necessary information for troubleshooting issues while maintaining system security and performance.