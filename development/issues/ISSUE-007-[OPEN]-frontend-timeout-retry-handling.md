# ISSUE-007: Frontend Timeout Error Handling and Retry Mechanism

**Priority**: High  
**Type**: Feature/Enhancement  
**Component**: Frontend & Backend Integration  
**Created**: 24th July 2025  
**Status**: OPEN  

## Executive Summary

The system currently experiences timeout errors when backend operations exceed CloudFront's 30-second timeout limit. When this occurs, users receive a generic error message with no automatic retry mechanism, resulting in a poor user experience. This issue proposes implementing a graceful timeout handling system with automatic retries and user-friendly messaging.

## Current Implementation

### CloudFront Configuration
**File**: `/backend/cloudfront-config.json` (lines 46-47)
```json
"OriginReadTimeout": 30,
"OriginKeepaliveTimeout": 5
```

### Frontend Error Handling
**File**: `/frontend/web/src/app/chat/page.tsx`

Current error handling (lines 556-560):
```typescript
} catch (error) {
    console.error("Failed to send message to simple backend:", error);
    const errorMessage = error instanceof Error ? error.message : "An unknown error occurred with simple backend";
    dispatch({ type: 'SET_ERROR', payload: { errorContent: errorMessage } });
}
```

Error display mechanism (lines 180-195):
```typescript
case 'SET_ERROR':
    const errorId = `error-${Date.now()}`;
    const errorMessage: Message = {
        id: errorId,
        role: 'assistant',
        content: `Error: ${action.payload.errorContent}`,
        agentName: 'System Error'
    };
    
    return {
        ...state,
        loadingMessageId: null,
        currentAssistantMessageId: null,
        messages: { ...state.messages, [errorId]: errorMessage },
        messageOrder: [...state.messageOrder, errorId],
    };
```

## Problems Identified

1. **No Timeout Detection**: The frontend doesn't distinguish between timeout errors and other errors
2. **No Retry Logic**: Failed requests due to timeouts are not automatically retried
3. **Poor User Experience**: Users see generic error messages without guidance on what to do
4. **Lost Context**: When a timeout occurs, the user's message and context are lost
5. **CloudFront Limit**: The 30-second timeout is enforced by CloudFront, which returns a 504 Gateway Timeout

## Proposed Solution

### 1. Implement Timeout Detection

Add timeout detection to the fetch request:
```typescript
// Add timeout wrapper function
const fetchWithTimeout = async (url: string, options: RequestInit, timeoutMs: number = 28000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - the server is taking longer than expected');
        }
        throw error;
    }
};
```

### 2. Add Retry Mechanism

Implement exponential backoff retry logic:
```typescript
const fetchWithRetry = async (
    url: string, 
    options: RequestInit, 
    maxRetries: number = 3,
    initialDelay: number = 1000
) => {
    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            // Set client-side timeout to 28 seconds (2 seconds before CloudFront timeout)
            const response = await fetchWithTimeout(url, options, 28000);
            
            // Check for 504 Gateway Timeout
            if (response.status === 504) {
                throw new Error('Gateway timeout - server processing took too long');
            }
            
            return response;
        } catch (error) {
            lastError = error as Error;
            
            // Only retry on timeout errors
            if (
                attempt < maxRetries && 
                (lastError.message.includes('timeout') || lastError.message.includes('504'))
            ) {
                // Show retry message to user
                dispatch({ 
                    type: 'START_ASSISTANT_MESSAGE', 
                    payload: { 
                        id: `retry-${Date.now()}`, 
                        agentName: 'System' 
                    } 
                });
                
                const retryMessage = `Apologies for the extended delay, it seems the AI servers are very busy at present. Please bear with me for a moment whilst I try again.`;
                dispatch({ 
                    type: 'UPDATE_ASSISTANT_MESSAGE', 
                    payload: { 
                        id: `retry-${Date.now()}`, 
                        content: retryMessage 
                    } 
                });
                
                // Exponential backoff
                const delay = initialDelay * Math.pow(2, attempt);
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
            }
            
            // If not a timeout or max retries reached, break
            break;
        }
    }
    
    throw lastError!;
};
```

### 3. Update Message Sending Logic

Modify the `sendMessage` function to use the retry mechanism:
```typescript
const sendMessage = useCallback(async (
    content: string, 
    sessionId: string,
    agentOverride?: string | null
) => {
    // ... existing code ...
    
    try {
        // Replace direct fetch with retry-enabled fetch
        const response = await fetchWithRetry(`${apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: content,
                session_id: sessionId,
                agent_override: agentOverride,
                last_agent: lastAgent,
                routine_number: routineNumber
            }),
        });
        
        // ... rest of existing code ...
        
    } catch (error) {
        console.error("Failed to send message after retries:", error);
        
        // Provide user-friendly error message based on error type
        let userMessage = "An error occurred while processing your request.";
        
        if (error instanceof Error) {
            if (error.message.includes('timeout')) {
                userMessage = "Apologies, but it seems there is too much traffic on the AI servers. Please could you try resubmitting your last response and hopefully we can process your request this time.";
            } else if (error.message.includes('network')) {
                userMessage = "Network connection issue. Please check your internet connection and try again.";
            } else {
                userMessage = error.message;
            }
        }
        
        dispatch({ type: 'SET_ERROR', payload: { errorContent: userMessage } });
    }
}, [dispatch, scrollToMessageTop, scrollToVeryBottom]);
```

### 4. Add Loading State Management

Enhance loading states to show progress during retries:
```typescript
// Add new action types
type ChatAction =
    | { type: 'SET_RETRY_STATUS'; payload: { message: string } }
    // ... existing action types

// Update reducer
case 'SET_RETRY_STATUS':
    if (state.loadingMessageId) {
        return {
            ...state,
            messages: {
                ...state.messages,
                [state.loadingMessageId]: {
                    ...state.messages[state.loadingMessageId],
                    content: action.payload.message
                }
            }
        };
    }
    return state;
```

### 5. Timer Behavior During Retries

The frontend UI timer should continue running during retries (not restart):
```typescript
// The timer starts when the user first submits
// It continues through all retry attempts
// This gives accurate total wait time to the user
```

This means:
- Timer starts at 0:00 when user first submits
- Continues counting through all retry attempts
- Shows total elapsed time including retries
- More honest representation of actual wait time

### 6. Photo Upload Exclusion

The photo upload already has its own polling mechanism and should be excluded from retry logic:
```typescript
// In sendMessage function, check if it's a photo upload
if (uploadResponse && 'processing_id' in uploadResponse) {
    // Existing photo polling logic - DO NOT apply retry wrapper
    pollForResult();
} else {
    // Regular message - apply retry logic
    const response = await fetchWithRetry(/* ... */);
}
```

## Implementation Checklist

- [ ] Create `fetchWithTimeout` utility function with 28-second timeout
- [ ] Implement `fetchWithRetry` with exponential backoff
- [ ] Update `sendMessage` function to use retry mechanism
- [ ] Add user-friendly timeout messages as specified
- [ ] Ensure photo upload polling is not affected by retry logic
- [ ] Verify timer continues (not resets) during retries
- [ ] Test with artificially delayed backend responses
- [ ] Add retry configuration to environment variables
- [ ] Add metrics/logging for timeout occurrences
- [ ] Document the retry behavior for users

## Testing Instructions

1. **Simulate Timeout**:
   - Add artificial delay in backend endpoint: `await asyncio.sleep(35)`
   - Verify frontend detects timeout at 28 seconds
   - Confirm retry attempts are made with exponential backoff

2. **Test Retry Success**:
   - Configure backend to succeed on 2nd attempt
   - Verify user sees retry status messages
   - Confirm final response is displayed correctly

3. **Test Max Retries**:
   - Force all retries to fail
   - Verify user-friendly error message is shown
   - Confirm user can try again manually

4. **Test Different Error Types**:
   - Network errors (disconnect internet)
   - 500 server errors (should not retry)
   - 504 gateway timeouts (should retry)

## Additional Context

### CloudFront Timeout Limits
- CloudFront has a hard limit of 30 seconds for origin requests
- Cannot be increased without AWS architectural changes
- Client-side timeout should be slightly less (28 seconds) to handle gracefully

### Backend Considerations
- Long-running operations should be made asynchronous
- Consider implementing server-sent events (SSE) for long operations
- Add request ID tracking for debugging timeout issues

### Related Issues
- May relate to photo upload timeouts (similar retry logic needed)
- Consider implementing progress indicators for long operations

### References
- [AWS CloudFront Timeout Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesOriginResponseTimeout)
- [MDN Fetch API Abort Controller](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [Exponential Backoff Best Practices](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)