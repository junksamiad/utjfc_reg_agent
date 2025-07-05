# Photo Upload System - Low Level Design

**Document Version**: 1.0  
**Date**: July 5, 2025  
**System**: UTJFC Registration System - Routine 34 (Photo Upload)

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Sequence Flow](#sequence-flow)
5. [Worker Thread Mechanism](#worker-thread-mechanism)
6. [Status Polling Implementation](#status-polling-implementation)
7. [Error Handling](#error-handling)
8. [Data Structures](#data-structures)
9. [Technical Specifications](#technical-specifications)

## Overview

The photo upload system (Routine 34) is the penultimate step in the UTJFC registration process. It handles asynchronous photo uploads with AI validation, S3 storage, and real-time status updates to the frontend through a polling mechanism.

### Key Features
- Asynchronous photo processing with immediate user feedback
- AI-powered photo validation using GPT-4.1 Vision
- Background thread processing to prevent blocking
- Real-time status polling for progress updates
- S3 cloud storage integration
- Database record linking

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend  │────▶│   Backend    │────▶│ Background      │
│  (Next.js)  │◀────│  (FastAPI)   │     │ Worker Thread   │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                    │                      │
       │                    │                      ├──▶ GPT-4.1 Vision API
       │                    │                      ├──▶ AWS S3
       │                    │                      └──▶ Airtable
       │                    │
       └────Polling────────▶│
         (every 2s)         │
```

## Component Details

### 1. Frontend Upload Handler (`/frontend/web/src/app/chat/page.tsx`)

**Location**: Lines 322-469

**Responsibilities**:
- File selection and upload initiation
- FormData construction with session context
- Immediate response display
- Polling mechanism trigger
- Final message display

**Key Code Section**:
```typescript
// Lines 382-458: Polling mechanism
if (data.processing === true && data.session_id) {
    console.log('🔄 Starting polling for session:', data.session_id);
    simulateTyping(dispatch, assistantMessageId, data.response, 'UTJFC Assistant');
    
    const pollForResult = async () => {
        const statusResponse = await fetch(`${config.UPLOAD_STATUS_URL}/${data.session_id}`);
        const statusData = await statusResponse.json();
        
        if (statusData.complete === true) {
            // Create new message for final result
            const finalMessageId = `assistant-final-${Date.now()}`;
            dispatch({ type: 'START_ASSISTANT_MESSAGE', payload: { id: finalMessageId } });
            simulateTyping(dispatch, finalMessageId, statusData.response, 'UTJFC Assistant');
        } else {
            setTimeout(pollForResult, 2000);
        }
    };
    
    setTimeout(pollForResult, 2000);
}
```

### 2. Backend Upload Endpoint (`/backend/server.py`)

**Async Upload Endpoint** (`/upload-async`):
- **Location**: Lines 295-344
- **Method**: POST
- **Purpose**: Receives file upload and triggers background processing

**Key Operations**:
1. Save uploaded file to temporary location
2. Generate session-specific file path
3. Return immediate response with processing flag
4. Start background thread for AI processing

**Code Structure**:
```python
@app.post("/api/upload-async")
async def upload_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    last_agent: Optional[str] = Form(None),
    routine_number: Optional[int] = Form(None)
):
    # Save file to temp location
    temp_file_path = f"/tmp/{session_id}_{file.filename}"
    
    # Start background processing
    background_thread = threading.Thread(
        target=process_photo_background,
        args=(session_id, temp_file_path, routine_number, last_agent),
        daemon=True
    )
    background_thread.start()
    
    # Return immediate response
    return JSONResponse({
        "response": "📸 Photo Received. Processing your registration...",
        "processing": True,
        "session_id": session_id
    })
```

### 3. Status Polling Endpoint (`/backend/server.py`)

**Location**: Lines 350-358
**Method**: GET
**Route**: `/api/upload-status/{session_id}`

**Implementation**:
```python
@app.get("/api/upload-status/{session_id}")
async def get_upload_status(session_id: str):
    status = get_upload_status(session_id)
    return JSONResponse(content=status)
```

## Sequence Flow

```
1. User selects photo file
   └─> Frontend creates FormData with file + session context

2. Frontend POSTs to /api/upload-async
   └─> Backend saves file to temp location
   └─> Backend returns immediate response
   └─> Backend starts background thread

3. Frontend displays "Processing..." message
   └─> Frontend starts polling /api/upload-status/{session_id}

4. Background thread processes photo
   ├─> AI agent validates photo with GPT-4.1 Vision
   ├─> Uploads validated photo to S3
   ├─> Updates database with S3 URL
   └─> Updates status store with completion

5. Frontend polling detects complete:true
   └─> Displays final success message
   └─> Stops polling
```

## Worker Thread Mechanism

### Thread Creation (`/backend/server.py`)

**Location**: Lines 49-158

**Function**: `process_photo_background()`

**Thread Characteristics**:
- **Type**: Python daemon thread
- **Lifecycle**: Runs independently, terminates with main process
- **Concurrency**: Thread-safe status updates via locks

### Processing Flow:

1. **Thread Initialization** (Lines 336-341):
```python
background_thread = threading.Thread(
    target=process_photo_background,
    args=(session_id, temp_file_path, routine_number, last_agent),
    daemon=True
)
background_thread.start()
```

2. **AI Agent Creation** (Lines 83-90):
```python
dynamic_agent = Agent(
    name=new_registration_agent.name,
    model=new_registration_agent.model,
    instructions=dynamic_instructions,
    tools=new_registration_agent.tools,
    use_mcp=new_registration_agent.use_mcp
)
```

3. **Photo Processing Chain**:
   - AI agent receives photo path and context
   - Validates photo using GPT-4.1 Vision API
   - Checks for clear face visibility
   - Uploads to S3 bucket (`utjfc-player-photos`)
   - Updates Airtable record with S3 URL
   - Returns success/failure status

### Thread Safety

**Status Store Protection** (Lines 36-47):
```python
status_lock = threading.Lock()

def set_upload_status(session_id: str, status: dict):
    with status_lock:
        upload_status_store[session_id] = {
            **status,
            'updated_at': datetime.now().isoformat()
        }

def get_upload_status(session_id: str) -> dict:
    with status_lock:
        return upload_status_store.get(session_id, {'complete': False})
```

## Status Polling Implementation

### Frontend Polling Logic

**Polling Characteristics**:
- **Interval**: 2 seconds
- **Endpoint**: GET `/api/upload-status/{session_id}`
- **Termination**: On `complete: true` or error
- **Timeout**: None (relies on backend completion)

### Status Response Structure:
```json
{
    "complete": boolean,
    "response": string,
    "last_agent": string,
    "routine_number": number,
    "error": boolean (optional),
    "message": string (progress indicator)
}
```

### Message Timer Display

**Location**: `chat-messages.tsx` Lines 124-126

Shows elapsed time for processing messages:
```typescript
{loadingMessageId === msg.id && 
 msg.content && 
 msg.content.includes("Processing") && 
 msg.startTime && (
    <LoadingTimer startTime={msg.startTime} />
)}
```

## Error Handling

### Frontend Error Scenarios:
1. **Upload Failure**: Network errors, file too large
2. **Polling Failure**: Status endpoint unreachable
3. **Timeout**: Handled by user manually (no auto-timeout)

### Backend Error Scenarios:
1. **AI Validation Failure**: Photo doesn't meet requirements
2. **S3 Upload Failure**: Network/permission issues
3. **Database Update Failure**: Record not found
4. **Thread Exceptions**: Caught and status updated

### Error Flow:
```python
try:
    # Process photo
except Exception as e:
    set_upload_status(session_id, {
        'complete': True,
        'error': True,
        'response': f'Error processing photo: {str(e)}'
    })
```

## Data Structures

### In-Memory Status Store:
```python
upload_status_store = {
    "session_id": {
        "complete": bool,
        "message": str,
        "response": str,
        "progress": str,
        "updated_at": str,
        "last_agent": str,
        "routine_number": int,
        "error": bool
    }
}
```

### Database Schema (Airtable):
```
registrations_2526 table:
- record_id: Primary key
- player_photo_url: S3 URL
- photo_uploaded_at: Timestamp
- photo_validation_status: Success/Failed
```

## Technical Specifications

### File Handling:
- **Supported Formats**: JPEG, PNG, HEIC (converted to JPG)
- **Max Size**: 10MB (configurable)
- **Temp Storage**: `/tmp/` directory
- **S3 Bucket**: `utjfc-player-photos`
- **S3 Path Format**: `photos/{year}/{month}/{player_name}_{timestamp}.jpg`

### AI Integration:
- **Model**: GPT-4.1 Vision
- **Validation Criteria**:
  - Clear face visibility
  - Single person in frame
  - Appropriate lighting
  - No obscured features

### Performance Characteristics:
- **Immediate Response**: < 100ms
- **Average Processing Time**: 5-15 seconds
- **Polling Overhead**: Minimal (simple GET requests)
- **Concurrent Uploads**: Supported via thread pool

### Security Considerations:
- Session-based access control
- Temporary file cleanup after processing
- S3 pre-signed URLs for secure access
- No direct file system exposure

## Integration Points

### With Registration Flow:
- **Previous Step**: Routine 33 (Kit selection)
- **Next Step**: Routine 35 (Final confirmation)
- **Dependencies**: Valid registration record must exist

### External Services:
1. **OpenAI API**: Photo validation
2. **AWS S3**: Photo storage
3. **Airtable API**: Database updates
4. **GoCardless**: Payment verification (indirect)

## Future Enhancements

1. **Progress Indicators**: More granular status updates
2. **Batch Processing**: Multiple photo uploads
3. **Retry Mechanism**: Automatic retry on failures
4. **Caching**: CloudFront integration for faster retrieval
5. **Monitoring**: Structured logging and metrics