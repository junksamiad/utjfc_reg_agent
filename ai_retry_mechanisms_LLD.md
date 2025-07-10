# AI Retry Mechanisms - Low-Level Design Document

## Overview

The UTJFC Registration Agent system implements sophisticated retry mechanisms to handle AI API failures and response parsing errors. This document provides a comprehensive analysis of the retry functions, exponential backoff implementation, parsing strategies, and error handling patterns.

## Table of Contents

1. [Retry Functions Architecture](#retry-functions-architecture)
2. [Exponential Backoff Implementation](#exponential-backoff-implementation)
3. [Parsing Strategies](#parsing-strategies)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Registration vs Re-registration Logic](#registration-vs-re-registration-logic)
6. [Performance Implications](#performance-implications)
7. [System Integration](#system-integration)
8. [Configuration and Optimization](#configuration-and-optimization)

## Retry Functions Architecture

### Core Retry Functions

The system implements two specialized retry functions located in `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/server.py`:

#### 1. `retry_ai_call_with_parsing()`

```python
def retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0, session_id="unknown", call_type="AI"):
    """
    Retry an AI function call with exponential backoff when parsing fails.
    
    Args:
        ai_call_func: The AI function to call (e.g., chat_loop_new_registration_1)
        *args: Arguments to pass to the AI function
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        session_id: Session ID for logging
        call_type: Type of AI call for logging (e.g., "registration", "photo upload")
    
    Returns:
        tuple: (success, ai_response_object, parsed_content, routine_number)
    """
```

**Use Cases:**
- New player registrations (200-series codes)
- Photo upload processing (routine 34)
- Universal agent interactions
- Registration continuation flows

#### 2. `retry_rereg_ai_call_with_parsing()`

```python
def retry_rereg_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0, session_id="unknown"):
    """
    Retry a re-registration AI function call with exponential backoff when parsing fails.
    Re-registration uses a different response structure (output_text instead of output[0].content[0].text).
    
    Args:
        ai_call_func: The AI function to call (e.g., chat_loop_renew_registration_1)
        *args: Arguments to pass to the AI function
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        session_id: Session ID for logging
    
    Returns:
        tuple: (success, ai_response_object, parsed_content)
    """
```

**Use Cases:**
- Existing player re-registrations (100-series codes)
- Simplified workflow without routine progression

## Exponential Backoff Implementation

### Algorithm Details

Both retry functions implement exponential backoff with the following formula:

```python
wait_time = delay * (2 ** attempt)
```

**Backoff Sequence:**
- Attempt 1: No delay (immediate)
- Attempt 2: 1.0 seconds (delay * 2^0)
- Attempt 3: 2.0 seconds (delay * 2^1)
- Attempt 4: 4.0 seconds (delay * 2^2)

### Implementation Code

```python
# Wait before retrying (exponential backoff)
wait_time = delay * (2 ** attempt)
print(f"--- Session [{session_id}] Retrying in {wait_time} seconds... ---")
time.sleep(wait_time)
```

### Configuration Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_retries` | 3 | Maximum retry attempts (total attempts = max_retries + 1) |
| `delay` | 1.0 | Initial delay multiplier in seconds |
| `session_id` | "unknown" | Session tracking for logging |

## Parsing Strategies

### Primary Parsing Strategy (New Registration)

The new registration agent uses a hierarchical parsing approach:

1. **Structured JSON Response Parsing:**
   ```python
   if hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
       text_content = ai_full_response_object.output[0].content[0].text
       structured_response = json.loads(text_content)
       if isinstance(structured_response, dict):
           if 'agent_final_response' in structured_response:
               parsed_content = structured_response['agent_final_response']
               if 'routine_number' in structured_response:
                   routine_number = structured_response['routine_number']
   ```

2. **Raw Text Fallback:**
   ```python
   except json.JSONDecodeError as e:
       parsed_content = ai_full_response_object.output[0].content[0].text
       return True, ai_full_response_object, parsed_content, routine_number
   ```

### Secondary Parsing Strategy (Re-registration)

Re-registration uses a different response structure with multiple fallback levels:

1. **Primary: output_text Parsing**
   ```python
   if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
       structured_response = json.loads(ai_full_response_object.output_text)
       if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
           parsed_content = structured_response['agent_final_response']
   ```

2. **Secondary: Raw output_text Fallback**
   ```python
   except json.JSONDecodeError as e:
       parsed_content = ai_full_response_object.output_text
       return True, ai_full_response_object, parsed_content
   ```

3. **Tertiary: Detailed Parsing Fallback**
   ```python
   elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
       # Same parsing as new registration
   ```

### Response Schema Validation

The system uses Pydantic schemas for structured validation:

**New Registration Schema (`AgentResponse`):**
```python
class AgentResponse(BaseModel):
    agent_final_response: str = Field(min_length=1)
    routine_number: int = Field(ge=1)
    
    class Config:
        extra = "forbid"
```

**Re-registration Schema (`ReRegistrationAgentResponse`):**
```python
class ReRegistrationAgentResponse(BaseModel):
    agent_final_response: str = Field(min_length=1)
    
    class Config:
        extra = "forbid"
```

## Error Handling Patterns

### Error Classification

The system handles three categories of errors:

1. **AI Call Errors**: Network, API, or service failures
2. **Parsing Errors**: JSON decode errors, missing fields, malformed responses
3. **Validation Errors**: Schema validation failures, missing required fields

### Error Handling Flow

```python
for attempt in range(max_retries + 1):
    try:
        # AI function call
        ai_full_response_object = ai_call_func(*args)
        
        try:
            # Parsing logic
            # ... parsing code ...
            return True, ai_full_response_object, parsed_content, routine_number
            
        except Exception as parse_error:
            # Parse error handling
            if attempt == max_retries:
                return False, ai_full_response_object, parsed_content, routine_number
            # Exponential backoff
            
    except Exception as ai_error:
        # AI call error handling
        if attempt == max_retries:
            return False, None, f"Error: {call_type} AI call failed after {max_retries + 1} attempts", None
        # Exponential backoff
```

### Logging Strategy

Comprehensive logging at each retry attempt:

```python
print(f"--- Session [{session_id}] {call_type} AI call attempt {attempt + 1}/{max_retries + 1} ---")
print(f"--- Session [{session_id}] Parse error on attempt {attempt + 1}: {parse_error} ---")
print(f"--- Session [{session_id}] Retrying in {wait_time} seconds... ---")
```

## Registration vs Re-registration Logic

### Key Differences

| Aspect | New Registration | Re-registration |
|--------|------------------|----------------|
| **Response Structure** | `output[0].content[0].text` | `output_text` (primary) |
| **Schema** | `AgentResponse` | `ReRegistrationAgentResponse` |
| **Routine System** | ✅ (35-step workflow) | ❌ (simple flow) |
| **Return Values** | 4-tuple with routine_number | 3-tuple without routine_number |
| **Complexity** | High (multiple parsing layers) | Medium (dual fallback) |

### Functional Differences

**New Registration Parsing:**
```python
# Returns: (success, ai_response_object, parsed_content, routine_number)
success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
    chat_loop_new_registration_1, 
    dynamic_agent, 
    session_history, 
    current_session_id,
    max_retries=3,
    session_id=current_session_id,
    call_type="Registration"
)
```

**Re-registration Parsing:**
```python
# Returns: (success, ai_response_object, parsed_content)
success, ai_full_response_object, assistant_content_to_send = retry_rereg_ai_call_with_parsing(
    chat_loop_renew_registration_1, 
    re_registration_agent, 
    session_history,
    max_retries=3,
    session_id=current_session_id
)
```

## Performance Implications

### Latency Analysis

**Best Case Scenario:**
- Single successful call: ~2-5 seconds (OpenAI API response time)
- No retry overhead

**Worst Case Scenario:**
- 4 failed attempts: ~2-5 seconds per attempt + backoff delays
- Total backoff time: 0 + 1 + 2 + 4 = 7 seconds
- Total worst case: ~4 * 5 + 7 = 27 seconds

### Memory Usage

**Response Object Storage:**
- Each retry attempt stores the full AI response object
- Average response size: ~1-5KB per attempt
- Maximum memory overhead: ~20KB per retry cycle

**Session History Impact:**
- Failed attempts do not add to session history
- Only successful responses are stored
- Prevents session history pollution

### Throughput Considerations

**Concurrent Session Handling:**
- Each session operates independently
- No shared state between retry mechanisms
- Thread-safe operation through session isolation

**Resource Optimization:**
- Early return on successful parsing
- Minimal computational overhead for JSON parsing
- Efficient memory cleanup on completion

## System Integration

### Integration Points

The retry mechanisms integrate with multiple system components:

1. **Chat Endpoints** (`/chat`, `/chat/continue`, `/chat/rereg`)
2. **Photo Upload Processing** (`/upload_photo`)
3. **Background Processing** (async photo validation)
4. **Universal Agent** (fallback conversations)

### Call Flow Integration

```python
# Example integration in chat endpoint
try:
    success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
        chat_loop_new_registration_1, 
        dynamic_agent, 
        session_history, 
        current_session_id,
        max_retries=3,
        session_id=current_session_id,
        call_type="Registration"
    )
    
    if success:
        # Process successful response
        if routine_number_from_agent:
            # Update routine progression
            pass
    else:
        # Handle failure case
        pass
        
except Exception as e:
    # Additional error handling
    pass
```

### Session Management Integration

The retry mechanisms integrate with session management:

```python
# Session ID propagation
os.environ['CURRENT_SESSION_ID'] = session_id

# Session history management
add_message_to_session_history(current_session_id, "user", payload.user_message)
session_history = get_session_history(current_session_id)
```

## Configuration and Optimization

### Current Configuration

All retry functions currently use consistent configuration:

```python
max_retries=3      # Total of 4 attempts
delay=1.0          # 1 second initial delay
```

### Optimization Strategies

#### 1. Adaptive Retry Configuration

**Context-aware retry limits:**
```python
def get_retry_config(call_type: str, routine_number: int = None) -> dict:
    """Get optimized retry configuration based on call context"""
    configs = {
        "photo_upload": {"max_retries": 5, "delay": 2.0},  # Higher tolerance for photo processing
        "routine_34": {"max_retries": 5, "delay": 2.0},    # Critical photo validation step
        "payment": {"max_retries": 2, "delay": 0.5},       # Fast fail for payment operations
        "default": {"max_retries": 3, "delay": 1.0}
    }
    return configs.get(call_type, configs["default"])
```

#### 2. Circuit Breaker Pattern

**Prevent cascading failures:**
```python
class AIServiceCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def should_attempt_call(self) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
```

#### 3. Response Caching

**Cache successful responses for identical inputs:**
```python
import hashlib
from functools import lru_cache

def cache_key(messages: list, agent_config: dict) -> str:
    """Generate cache key for identical AI requests"""
    content = json.dumps(messages, sort_keys=True) + json.dumps(agent_config, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

@lru_cache(maxsize=100)
def cached_ai_call(cache_key: str, ai_call_func, *args):
    """Cache AI responses for identical requests"""
    return ai_call_func(*args)
```

#### 4. Async Retry Implementation

**Non-blocking retry operations:**
```python
import asyncio

async def async_retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0, session_id="unknown"):
    """Async version of retry mechanism"""
    for attempt in range(max_retries + 1):
        try:
            # Use async AI call
            ai_full_response_object = await ai_call_func(*args)
            
            # Parsing logic (same as sync version)
            # ...
            
        except Exception as ai_error:
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
            else:
                # Final failure
                return False, None, f"Error: AI call failed after {max_retries + 1} attempts", None
```

### Performance Monitoring

**Metrics to track:**
- Success rate by call type
- Average retry count per session
- Response time distribution
- Error classification frequency

**Implementation:**
```python
class RetryMetrics:
    def __init__(self):
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "retry_counts": [],
            "error_types": {},
            "response_times": []
        }
    
    def record_call(self, success: bool, attempts: int, error_type: str = None, response_time: float = None):
        self.metrics["total_calls"] += 1
        if success:
            self.metrics["successful_calls"] += 1
        self.metrics["retry_counts"].append(attempts)
        if error_type:
            self.metrics["error_types"][error_type] = self.metrics["error_types"].get(error_type, 0) + 1
        if response_time:
            self.metrics["response_times"].append(response_time)
```

## Conclusion

The AI retry mechanisms in the UTJFC Registration Agent system provide robust error handling with:

- **Exponential backoff** to prevent API rate limiting
- **Dual parsing strategies** for different response formats
- **Comprehensive error classification** and logging
- **Session-aware retry logic** for better debugging
- **Configurable retry parameters** for different use cases

The system successfully handles the complexity of managing both simple re-registration flows and complex 35-step new registration workflows while maintaining high reliability and performance.

### Future Enhancements

1. **Adaptive Configuration**: Context-aware retry parameters
2. **Circuit Breaker Pattern**: Prevent cascading failures
3. **Response Caching**: Improve performance for repeated requests
4. **Async Implementation**: Non-blocking retry operations
5. **Enhanced Monitoring**: Detailed metrics and alerting

This retry mechanism is a critical component ensuring the system's resilience and providing a smooth user experience even when facing intermittent AI service issues.