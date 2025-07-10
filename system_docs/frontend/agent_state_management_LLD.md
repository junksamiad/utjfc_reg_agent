# Agent State Management Low-Level Design (LLD)

## Document Overview
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Detailed technical documentation for frontend agent state persistence and management  
**Scope**: Session management, agent continuity, conversation context, and state synchronization  

---

## 1. System Architecture Overview

### 1.1 Agent State Management Architecture
```
Frontend State Management
┌─────────────────────────────────────────────────────────┐
│                  Session Storage                        │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ chat_session_id │  │   last_agent    │               │
│  │                 │  │                 │               │
│  │ routine_number  │  │ conversation_   │               │
│  │                 │  │    context      │               │
│  └─────────────────┘  └─────────────────┘               │
└─────────────────────────────────────────────────────────┘
           │                            │
           ▼                            ▼
┌─────────────────┐              ┌─────────────────┐
│   Chat State    │              │  Backend API    │
│   (useReducer)  │◄────────────▶│   Requests      │
│                 │              │                 │
└─────────────────┘              └─────────────────┘
```

### 1.2 State Persistence Layers
1. **Session Storage**: Browser-level persistence for session continuity
2. **React State**: In-memory state for real-time UI updates
3. **Backend State**: Server-side agent context and workflow position
4. **Request Payload**: State transmission with each API call

---

## 2. Session Identification & Generation

### 2.1 Session ID Generation
```typescript
// Session ID format: sess_[12-character alphanumeric]
const generateSessionId = (): string => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = 'sess_';
    
    for (let i = 0; i < 12; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    return result;
};

// Examples:
// sess_aB3dE5fG7hJ9
// sess_K2mN4pQ6rT8v
// sess_xY1zA3bC5dE7
```

### 2.2 Session ID Management
```typescript
const SESSION_STORAGE_KEY = 'chat_session_id';

// Get or create session ID
function getOrCreateSessionId(): string {
    try {
        let sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
        
        if (!sessionId || !isValidSessionId(sessionId)) {
            sessionId = generateSessionId();
            sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
            console.log('Generated new session ID:', sessionId);
        }
        
        return sessionId;
    } catch (error) {
        // Fallback for private browsing or storage issues
        console.warn('SessionStorage unavailable, using temporary session');
        return generateSessionId();
    }
}

// Validate session ID format
const isValidSessionId = (sessionId: string): boolean => {
    return /^sess_[a-zA-Z0-9]{12}$/.test(sessionId);
};

// Reset session (clear chat functionality)
const resetSession = (): string => {
    const newSessionId = generateSessionId();
    sessionStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    return newSessionId;
};
```

### 2.3 Session Lifecycle
```typescript
// Session lifecycle hooks
const useSessionManagement = () => {
    const [sessionId, setSessionId] = useState<string>('');
    
    useEffect(() => {
        // Initialize session on component mount
        const id = getOrCreateSessionId();
        setSessionId(id);
        
        // Log session start for analytics
        console.log('Session initialized:', id);
    }, []);
    
    const resetCurrentSession = useCallback(() => {
        const newId = resetSession();
        setSessionId(newId);
        
        // Clear agent state
        clearAgentState();
        
        console.log('Session reset:', newId);
        return newId;
    }, []);
    
    return { sessionId, resetCurrentSession };
};
```

---

## 3. Agent State Structure

### 3.1 Agent State Interface
```typescript
interface AgentState {
    last_agent: string | null;        // Current/last active agent name
    routine_number: number | null;    // Position in 35-step workflow
    conversation_context?: string;    // Optional conversation metadata
    agent_history?: string[];         // Optional agent transition history
}

// Agent state storage keys
const AGENT_STORAGE_KEYS = {
    LAST_AGENT: 'last_agent',
    ROUTINE_NUMBER: 'routine_number',
    CONVERSATION_CONTEXT: 'conversation_context',
    AGENT_HISTORY: 'agent_history'
} as const;
```

### 3.2 Agent Types & Routing
```typescript
// Known agent types in the system
enum AgentType {
    RE_REGISTRATION = 're_registration_agent',
    NEW_REGISTRATION = 'new_registration_agent',
    GENERAL_INQUIRY = 'general_inquiry_agent',
    PAYMENT_PROCESSING = 'payment_agent',
    PHOTO_PROCESSING = 'photo_agent'
}

// Registration code detection patterns
const REGISTRATION_CODE_PATTERNS = {
    RE_REGISTRATION: /^1[0-9]{2}$/,     // 100-199 series
    NEW_REGISTRATION: /^2[0-9]{2}$/,    // 200-299 series
    GENERAL: /^[3-9][0-9]{2}$/          // 300+ series
} as const;

// Agent routing logic
const determineAgent = (userInput: string): AgentType | null => {
    const codeMatch = userInput.match(/\b([1-9][0-9]{2})\b/);
    
    if (codeMatch) {
        const code = codeMatch[1];
        
        if (REGISTRATION_CODE_PATTERNS.RE_REGISTRATION.test(code)) {
            return AgentType.RE_REGISTRATION;
        }
        
        if (REGISTRATION_CODE_PATTERNS.NEW_REGISTRATION.test(code)) {
            return AgentType.NEW_REGISTRATION;
        }
    }
    
    return null; // Let backend determine appropriate agent
};
```

### 3.3 Routine Number Management
```typescript
// 35-step registration workflow positions
const WORKFLOW_STAGES = {
    INITIAL_CONTACT: 1,
    CODE_VALIDATION: 2,
    PERSONAL_DETAILS: 3,
    PARENT_DETAILS: 4,
    ADDRESS_DETAILS: 5,
    EMERGENCY_CONTACT: 6,
    MEDICAL_INFORMATION: 7,
    PHOTO_UPLOAD: 8,
    TEAM_ASSIGNMENT: 9,
    KIT_REQUIREMENTS: 10,
    PAYMENT_SETUP: 11,
    DIRECT_DEBIT: 12,
    SMS_VERIFICATION: 13,
    FINAL_CONFIRMATION: 14,
    COMPLETION: 15
    // ... continues to 35
} as const;

// Workflow progress calculation
const calculateProgress = (routineNumber: number | null): number => {
    if (!routineNumber) return 0;
    return Math.min(Math.round((routineNumber / 35) * 100), 100);
};

// Stage name mapping
const getStageDescription = (routineNumber: number | null): string => {
    if (!routineNumber) return 'Starting registration';
    
    const stageMap: { [key: number]: string } = {
        1: 'Initial contact',
        2: 'Code validation',
        3: 'Personal details',
        4: 'Parent details',
        5: 'Address information',
        6: 'Emergency contact',
        7: 'Medical information',
        8: 'Photo upload',
        9: 'Team assignment',
        10: 'Kit requirements',
        11: 'Payment setup',
        12: 'Direct debit setup',
        13: 'SMS verification',
        14: 'Final confirmation',
        15: 'Registration complete'
        // Simplified mapping - full version has 35 stages
    };
    
    return stageMap[routineNumber] || `Step ${routineNumber} of 35`;
};
```

---

## 4. State Persistence Implementation

### 4.1 SessionStorage Operations
```typescript
// Store agent state in sessionStorage
const storeAgentState = (
    lastAgent: string | null, 
    routineNumber: number | null,
    context?: string
): void => {
    try {
        if (lastAgent !== null) {
            sessionStorage.setItem(AGENT_STORAGE_KEYS.LAST_AGENT, lastAgent);
        }
        
        if (routineNumber !== null) {
            sessionStorage.setItem(
                AGENT_STORAGE_KEYS.ROUTINE_NUMBER, 
                routineNumber.toString()
            );
        }
        
        if (context) {
            sessionStorage.setItem(AGENT_STORAGE_KEYS.CONVERSATION_CONTEXT, context);
        }
        
        // Update timestamp for session tracking
        sessionStorage.setItem('agent_state_updated', Date.now().toString());
        
    } catch (error) {
        console.warn('Failed to store agent state:', error);
    }
};

// Retrieve agent state from sessionStorage
const getAgentState = (): AgentState => {
    try {
        const lastAgent = sessionStorage.getItem(AGENT_STORAGE_KEYS.LAST_AGENT);
        const routineNumberStr = sessionStorage.getItem(AGENT_STORAGE_KEYS.ROUTINE_NUMBER);
        const context = sessionStorage.getItem(AGENT_STORAGE_KEYS.CONVERSATION_CONTEXT);
        
        return {
            last_agent: lastAgent,
            routine_number: routineNumberStr ? parseInt(routineNumberStr, 10) : null,
            conversation_context: context || undefined
        };
    } catch (error) {
        console.warn('Failed to retrieve agent state:', error);
        return { last_agent: null, routine_number: null };
    }
};

// Clear agent state (chat reset)
const clearAgentState = (): void => {
    try {
        Object.values(AGENT_STORAGE_KEYS).forEach(key => {
            sessionStorage.removeItem(key);
        });
        sessionStorage.removeItem('agent_state_updated');
        
        console.log('Agent state cleared');
    } catch (error) {
        console.warn('Failed to clear agent state:', error);
    }
};
```

### 4.2 Agent State Hook
```typescript
// Custom hook for agent state management
const useAgentState = () => {
    const [agentState, setAgentState] = useState<AgentState>(() => getAgentState());
    
    // Update local state when storage changes
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key && Object.values(AGENT_STORAGE_KEYS).includes(e.key as any)) {
                setAgentState(getAgentState());
            }
        };
        
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);
    
    // Update agent state
    const updateAgentState = useCallback((
        lastAgent: string | null,
        routineNumber: number | null,
        context?: string
    ) => {
        storeAgentState(lastAgent, routineNumber, context);
        setAgentState(getAgentState());
    }, []);
    
    // Clear agent state
    const clearState = useCallback(() => {
        clearAgentState();
        setAgentState({ last_agent: null, routine_number: null });
    }, []);
    
    return {
        agentState,
        updateAgentState,
        clearState,
        progress: calculateProgress(agentState.routine_number),
        stageDescription: getStageDescription(agentState.routine_number)
    };
};
```

---

## 5. Request Payload Integration

### 5.1 Payload Construction
```typescript
// Build request payload with agent state
const buildRequestPayload = (
    userMessage: string,
    sessionId: string,
    agentState: AgentState,
    additionalData?: Record<string, any>
): ChatRequestPayload => {
    const payload: ChatRequestPayload = {
        user_message: userMessage,
        session_id: sessionId,
        timestamp: new Date().toISOString()
    };
    
    // Add agent state if available
    if (agentState.last_agent) {
        payload.last_agent = agentState.last_agent;
    }
    
    if (agentState.routine_number !== null) {
        payload.routine_number = agentState.routine_number;
    }
    
    if (agentState.conversation_context) {
        payload.conversation_context = agentState.conversation_context;
    }
    
    // Add any additional data
    if (additionalData) {
        Object.assign(payload, additionalData);
    }
    
    return payload;
};

// Chat request payload interface
interface ChatRequestPayload {
    user_message: string;
    session_id: string;
    timestamp: string;
    last_agent?: string;
    routine_number?: number;
    conversation_context?: string;
    [key: string]: any; // Allow additional fields
}
```

### 5.2 Response Handling
```typescript
// Handle backend response and update agent state
const handleAgentResponse = (
    response: ChatResponse,
    updateAgentState: (agent: string | null, routine: number | null) => void
): void => {
    // Extract agent state from response
    const { last_agent, routine_number, conversation_context } = response;
    
    // Update local agent state
    if (last_agent !== undefined || routine_number !== undefined) {
        updateAgentState(
            last_agent || null,
            routine_number || null,
            conversation_context
        );
        
        console.log('Agent state updated:', {
            agent: last_agent,
            routine: routine_number,
            context: conversation_context
        });
    }
};

// Chat response interface
interface ChatResponse {
    response: string;
    last_agent?: string;
    routine_number?: number;
    conversation_context?: string;
    agent_name?: string;
    metadata?: Record<string, any>;
}
```

---

## 6. File Upload State Management

### 6.1 Upload Request State
```typescript
// File upload with agent state
const buildUploadFormData = (
    file: File,
    sessionId: string,
    agentState: AgentState
): FormData => {
    const formData = new FormData();
    
    // File data
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    // Agent state
    if (agentState.last_agent) {
        formData.append('last_agent', agentState.last_agent);
    }
    
    if (agentState.routine_number !== null) {
        formData.append('routine_number', agentState.routine_number.toString());
    }
    
    if (agentState.conversation_context) {
        formData.append('conversation_context', agentState.conversation_context);
    }
    
    return formData;
};
```

### 6.2 Upload Status Polling
```typescript
// Upload status with agent state updates
const pollUploadStatus = async (
    sessionId: string,
    updateAgentState: (agent: string | null, routine: number | null) => void
): Promise<UploadStatusResponse> => {
    const response = await fetch(
        `${config.UPLOAD_STATUS_URL}?session_id=${encodeURIComponent(sessionId)}`
    );
    
    const data: UploadStatusResponse = await response.json();
    
    // Update agent state from upload response
    if (data.status === 'completed' && (data.last_agent || data.routine_number)) {
        updateAgentState(data.last_agent || null, data.routine_number || null);
    }
    
    return data;
};
```

---

## 7. State Synchronization

### 7.1 Cross-Tab Synchronization
```typescript
// Handle storage events for cross-tab synchronization
const useCrossTabSync = () => {
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === SESSION_STORAGE_KEY && e.newValue !== e.oldValue) {
                console.log('Session ID changed in another tab');
                // Could reload page or sync state
            }
            
            if (Object.values(AGENT_STORAGE_KEYS).includes(e.key as any)) {
                console.log('Agent state changed in another tab');
                // Update local state
                const newState = getAgentState();
                setAgentState(newState);
            }
        };
        
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);
};
```

### 7.2 State Validation & Recovery
```typescript
// Validate and recover corrupted state
const validateAndRecoverState = (): AgentState => {
    const state = getAgentState();
    
    // Validate routine number range
    if (state.routine_number && (state.routine_number < 1 || state.routine_number > 35)) {
        console.warn('Invalid routine number detected, resetting:', state.routine_number);
        storeAgentState(state.last_agent, null);
        return { ...state, routine_number: null };
    }
    
    // Validate agent name format
    if (state.last_agent && !Object.values(AgentType).includes(state.last_agent as AgentType)) {
        console.warn('Unknown agent type detected:', state.last_agent);
        // Could map to known agent or clear
    }
    
    return state;
};

// Periodic state health check
const useStateHealthCheck = () => {
    useEffect(() => {
        const interval = setInterval(() => {
            validateAndRecoverState();
        }, 30000); // Check every 30 seconds
        
        return () => clearInterval(interval);
    }, []);
};
```

---

## 8. State Debugging & Monitoring

### 8.1 Debug Utilities
```typescript
// Debug agent state
const debugAgentState = (): void => {
    const state = getAgentState();
    const sessionId = sessionStorage.getItem(SESSION_STORAGE_KEY);
    
    console.group('🤖 Agent State Debug');
    console.log('Session ID:', sessionId);
    console.log('Last Agent:', state.last_agent);
    console.log('Routine Number:', state.routine_number);
    console.log('Progress:', calculateProgress(state.routine_number) + '%');
    console.log('Stage:', getStageDescription(state.routine_number));
    console.log('Context:', state.conversation_context);
    console.log('Storage Available:', isStorageAvailable());
    console.groupEnd();
};

// Check storage availability
const isStorageAvailable = (): boolean => {
    try {
        const test = '__storage_test__';
        sessionStorage.setItem(test, test);
        sessionStorage.removeItem(test);
        return true;
    } catch {
        return false;
    }
};

// Export state for debugging
const exportStateForDebugging = (): string => {
    const state = {
        sessionId: sessionStorage.getItem(SESSION_STORAGE_KEY),
        agentState: getAgentState(),
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        storageAvailable: isStorageAvailable()
    };
    
    return JSON.stringify(state, null, 2);
};
```

### 8.2 State Change Logging
```typescript
// Log state changes for debugging
const useStateLogger = () => {
    const [previousState, setPreviousState] = useState<AgentState | null>(null);
    
    useEffect(() => {
        const currentState = getAgentState();
        
        if (previousState && JSON.stringify(previousState) !== JSON.stringify(currentState)) {
            console.log('🔄 Agent State Changed:', {
                from: previousState,
                to: currentState,
                timestamp: new Date().toISOString()
            });
        }
        
        setPreviousState(currentState);
    });
};
```

---

## 9. Error Handling & Edge Cases

### 9.1 Storage Failure Handling
```typescript
// Graceful degradation when storage fails
const useStorageGracefulDegradation = () => {
    const [memoryState, setMemoryState] = useState<AgentState>({ 
        last_agent: null, 
        routine_number: null 
    });
    
    const [storageAvailable, setStorageAvailable] = useState(true);
    
    useEffect(() => {
        setStorageAvailable(isStorageAvailable());
    }, []);
    
    const getState = (): AgentState => {
        if (storageAvailable) {
            return getAgentState();
        }
        return memoryState;
    };
    
    const setState = (lastAgent: string | null, routineNumber: number | null): void => {
        if (storageAvailable) {
            storeAgentState(lastAgent, routineNumber);
        } else {
            setMemoryState({ last_agent: lastAgent, routine_number: routineNumber });
        }
    };
    
    return { getState, setState, storageAvailable };
};
```

### 9.2 Concurrent Request Handling
```typescript
// Handle multiple simultaneous requests
const useRequestDeduplication = () => {
    const pendingRequests = useRef<Map<string, Promise<any>>>(new Map());
    
    const makeRequest = async (
        key: string,
        requestFn: () => Promise<any>
    ): Promise<any> => {
        // Check if request is already pending
        if (pendingRequests.current.has(key)) {
            return pendingRequests.current.get(key);
        }
        
        // Create new request
        const request = requestFn().finally(() => {
            pendingRequests.current.delete(key);
        });
        
        pendingRequests.current.set(key, request);
        return request;
    };
    
    return { makeRequest };
};
```

---

## 10. Performance Optimizations

### 10.1 State Update Batching
```typescript
// Batch state updates to reduce storage writes
const useBatchedStateUpdates = () => {
    const pendingUpdates = useRef<Partial<AgentState>>({});
    const timeoutRef = useRef<NodeJS.Timeout>();
    
    const batchUpdate = (updates: Partial<AgentState>) => {
        // Merge with pending updates
        Object.assign(pendingUpdates.current, updates);
        
        // Clear existing timeout
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        
        // Set new timeout to flush updates
        timeoutRef.current = setTimeout(() => {
            const { last_agent, routine_number, conversation_context } = pendingUpdates.current;
            
            storeAgentState(
                last_agent !== undefined ? last_agent : null,
                routine_number !== undefined ? routine_number : null,
                conversation_context
            );
            
            // Clear pending updates
            pendingUpdates.current = {};
        }, 100); // 100ms debounce
    };
    
    return { batchUpdate };
};
```

### 10.2 Memory Management
```typescript
// Clean up unused state references
const useStateCleanup = () => {
    useEffect(() => {
        return () => {
            // Cleanup on unmount - could implement LRU cache here
            console.log('Cleaning up agent state references');
        };
    }, []);
};
```

---

## Conclusion

The agent state management system provides robust, persistent conversation context across the entire UTJFC registration flow. The architecture ensures seamless handoffs between different AI agents while maintaining user progress through the 35-step workflow.

**Key Strengths**:
- Persistent session management across browser sessions
- Robust error handling and graceful degradation
- Cross-tab synchronization capabilities
- Comprehensive debugging and monitoring tools
- Performance optimizations for frequent state updates
- Secure state validation and recovery mechanisms

**Architecture Quality**: Excellent - comprehensive state management with proper error handling  
**Reliability**: High - graceful degradation and recovery mechanisms  
**Performance**: Optimized - efficient storage operations and batched updates  
**Developer Experience**: Strong - extensive debugging tools and clear interfaces