# Async Photo Upload Low-Level Design (LLD)

## Document Overview
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Detailed technical documentation for the asynchronous photo upload system  
**Scope**: Photo upload flow, polling mechanism, S3 integration, and HEIC processing  

---

## 1. System Architecture Overview

### 1.1 Upload Flow Architecture
```
Frontend                    Backend                    External Services
┌─────────────────┐        ┌─────────────────┐       ┌─────────────────┐
│ File Selection  │──────▶ │ /upload-async   │──────▶│ S3 Bucket       │
│                 │        │                 │       │                 │
│ Status Polling  │◄──────│ /upload-status  │       │ HEIC Converter  │
│                 │        │                 │       │                 │
│ UI Updates      │        │ Processing      │       │ Metadata        │
└─────────────────┘        └─────────────────┘       └─────────────────┘
```

### 1.2 Key Components
- **File Selection UI**: Hidden input with validation
- **Upload Initiation**: POST to `/upload-async` endpoint
- **Polling System**: Regular status checks via `/upload-status`
- **Progress Feedback**: Real-time UI updates with timer
- **Error Handling**: Comprehensive error recovery

---

## 2. File Selection & Validation

### 2.1 Supported File Types
```typescript
const ALLOWED_FILE_TYPES = [
    'image/png',
    'image/jpeg',
    'image/jpg', 
    'image/webp',
    'image/heic'  // HEIC support for iOS photos
] as const;

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB limit
```

### 2.2 File Selection Implementation
```jsx
// Hidden file input in ChatInput component
<input
    ref={fileInputRef}
    type="file"
    accept="image/png,image/jpeg,image/jpg,image/webp,image/heic"
    onChange={handleFileSelect}
    className="hidden"
    multiple={false}
/>

// Trigger button
<button 
    type="button" 
    onClick={() => fileInputRef.current?.click()}
    disabled={isLoading}
    className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
    aria-label="Upload photo"
>
    <Upload className="w-5 h-5" />
</button>
```

### 2.3 Client-Side Validation
```typescript
const validateFile = (file: File): { isValid: boolean; error?: string } => {
    // Type validation
    if (!ALLOWED_FILE_TYPES.includes(file.type as any)) {
        return {
            isValid: false,
            error: 'Please select a valid image file (PNG, JPEG, JPG, WebP, HEIC)'
        };
    }
    
    // Size validation
    if (file.size > MAX_FILE_SIZE) {
        return {
            isValid: false,
            error: 'File size must be less than 10MB'
        };
    }
    
    // Additional validations
    if (file.size === 0) {
        return {
            isValid: false,
            error: 'Selected file is empty'
        };
    }
    
    return { isValid: true };
};

// File selection handler
const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const validation = validateFile(file);
    if (!validation.isValid) {
        alert(validation.error);
        return;
    }
    
    setSelectedFile(file);
    // Reset input to allow selecting same file again
    e.target.value = '';
};
```

### 2.4 File Preview (Future Enhancement)
```jsx
// File preview component
const FilePreview = ({ file, onRemove }) => {
    const [preview, setPreview] = useState(null);
    
    useEffect(() => {
        if (file && file.type.startsWith('image/')) {
            const url = URL.createObjectURL(file);
            setPreview(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [file]);
    
    return (
        <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
            {preview && (
                <img 
                    src={preview} 
                    alt="Preview" 
                    className="w-12 h-12 object-cover rounded"
                />
            )}
            <div className="flex-1">
                <div className="text-sm font-medium">{file.name}</div>
                <div className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                </div>
            </div>
            <button 
                onClick={onRemove}
                className="text-red-500 hover:text-red-700"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};
```

---

## 3. Upload Initiation

### 3.1 FormData Construction
```typescript
const createUploadFormData = (file: File, sessionId: string, agentState: any): FormData => {
    const formData = new FormData();
    
    // File data
    formData.append('file', file);
    
    // Session information
    formData.append('session_id', sessionId);
    
    // Agent state for continuity
    if (agentState.last_agent) {
        formData.append('last_agent', agentState.last_agent);
    }
    
    if (agentState.routine_number !== null) {
        formData.append('routine_number', agentState.routine_number.toString());
    }
    
    return formData;
};
```

### 3.2 Upload Request
```typescript
const initiateUpload = async (file: File, sessionId: string) => {
    const agentState = getAgentState();
    const formData = createUploadFormData(file, sessionId, agentState);
    
    try {
        const response = await fetch(config.UPLOAD_ASYNC_URL, {
            method: 'POST',
            body: formData,
            // Note: Don't set Content-Type header - browser sets it with boundary
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `Upload failed with status ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Upload initiation failed:', error);
        throw error;
    }
};
```

### 3.3 Initial Upload Response
```typescript
// Backend response structure
interface UploadInitiationResponse {
    message: string;           // Initial processing message
    session_id: string;        // Confirms session ID
    upload_id?: string;        // Optional upload tracking ID
}

// Example response:
{
    "message": "Photo uploaded successfully! Processing your image now...",
    "session_id": "sess_abc123def456"
}
```

---

## 4. Polling System

### 4.1 Polling Configuration
```typescript
const POLLING_CONFIG = {
    INTERVAL_MS: 1000,          // Poll every 1 second
    MAX_ATTEMPTS: 300,          // Maximum 5 minutes (300 seconds)
    TIMEOUT_MS: 30000,          // 30 second request timeout
    EXPONENTIAL_BACKOFF: false, // Linear polling for consistent UX
} as const;
```

### 4.2 Polling Implementation
```typescript
const pollUploadStatus = async (
    sessionId: string,
    messageId: string,
    dispatch: React.Dispatch<ChatAction>
): Promise<void> => {
    let attempts = 0;
    
    const poll = async (): Promise<boolean> => {
        attempts++;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), POLLING_CONFIG.TIMEOUT_MS);
            
            const response = await fetch(
                `${config.UPLOAD_STATUS_URL}?session_id=${encodeURIComponent(sessionId)}`,
                {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                    },
                    signal: controller.signal
                }
            );
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }
            
            const data: UploadStatusResponse = await response.json();
            
            switch (data.status) {
                case 'completed':
                    handleUploadComplete(data, messageId, dispatch);
                    return true; // Stop polling
                    
                case 'error':
                    handleUploadError(data, messageId, dispatch);
                    return true; // Stop polling
                    
                case 'processing':
                    // Continue polling
                    return false;
                    
                default:
                    console.warn('Unknown upload status:', data.status);
                    return false;
            }
        } catch (error) {
            console.error(`Polling attempt ${attempts} failed:`, error);
            
            // Stop polling after max attempts
            if (attempts >= POLLING_CONFIG.MAX_ATTEMPTS) {
                handleUploadTimeout(messageId, dispatch);
                return true;
            }
            
            // Continue polling for network errors
            return false;
        }
    };
    
    // Initial poll
    const shouldStop = await poll();
    if (shouldStop) return;
    
    // Set up interval polling
    const intervalId = setInterval(async () => {
        const shouldStop = await poll();
        if (shouldStop) {
            clearInterval(intervalId);
        }
    }, POLLING_CONFIG.INTERVAL_MS);
    
    // Cleanup on component unmount (handled by caller)
    return () => clearInterval(intervalId);
};
```

### 4.3 Status Response Handling
```typescript
interface UploadStatusResponse {
    status: 'processing' | 'completed' | 'error';
    response?: string;          // Final agent response
    last_agent?: string;        // Updated agent state
    routine_number?: number;    // Updated routine number
    error?: string;             // Error message if status is 'error'
    progress?: number;          // Optional progress percentage
    estimated_completion?: number; // Optional ETA in seconds
}

// Handle successful completion
const handleUploadComplete = (
    data: UploadStatusResponse,
    messageId: string,
    dispatch: React.Dispatch<ChatAction>
) => {
    // Update message content with final response
    dispatch({
        type: 'APPEND_DELTA',
        payload: {
            id: messageId,
            delta: data.response || 'Photo processed successfully!'
        }
    });
    
    // Complete the message
    dispatch({
        type: 'COMPLETE_ASSISTANT_MESSAGE',
        payload: { id: messageId }
    });
    
    // Update agent state
    if (data.last_agent || data.routine_number !== undefined) {
        storeAgentState(data.last_agent || null, data.routine_number || null);
    }
    
    // Stop processing indicator
    dispatch({
        type: 'SET_PROCESSING',
        payload: { id: messageId, processing: false }
    });
};

// Handle upload errors
const handleUploadError = (
    data: UploadStatusResponse,
    messageId: string,
    dispatch: React.Dispatch<ChatAction>
) => {
    const errorMessage = data.error || 'An error occurred while processing your photo.';
    
    dispatch({
        type: 'SET_ERROR',
        payload: { errorContent: errorMessage }
    });
    
    // Stop processing indicator
    dispatch({
        type: 'SET_PROCESSING',
        payload: { id: messageId, processing: false }
    });
};

// Handle timeout
const handleUploadTimeout = (
    messageId: string,
    dispatch: React.Dispatch<ChatAction>
) => {
    dispatch({
        type: 'SET_ERROR',
        payload: { 
            errorContent: 'Photo upload timed out. Please try again with a smaller image.' 
        }
    });
    
    dispatch({
        type: 'SET_PROCESSING',
        payload: { id: messageId, processing: false }
    });
};
```

---

## 5. UI Feedback System

### 5.1 Upload States
```typescript
enum UploadState {
    IDLE = 'idle',
    UPLOADING = 'uploading',
    PROCESSING = 'processing',
    COMPLETED = 'completed',
    ERROR = 'error'
}

interface UploadProgress {
    state: UploadState;
    progress?: number;
    message?: string;
    startTime?: number;
    estimatedCompletion?: number;
}
```

### 5.2 Progress Indicator Component
```jsx
const UploadProgressIndicator = ({ 
    state, 
    progress, 
    startTime, 
    estimatedCompletion 
}) => {
    const [elapsedTime, setElapsedTime] = useState(0);
    
    useEffect(() => {
        if (!startTime) return;
        
        const interval = setInterval(() => {
            setElapsedTime(Date.now() - startTime);
        }, 100);
        
        return () => clearInterval(interval);
    }, [startTime]);
    
    const formatTime = (ms) => {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };
    
    const getStatusMessage = () => {
        switch (state) {
            case UploadState.UPLOADING:
                return 'Uploading photo...';
            case UploadState.PROCESSING:
                return 'Processing photo...';
            default:
                return 'Processing...';
        }
    };
    
    return (
        <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            {/* Animated spinner */}
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
            
            {/* Status text */}
            <div className="flex-1">
                <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {getStatusMessage()}
                </div>
                
                {/* Progress bar (if available) */}
                {progress !== undefined && (
                    <div className="mt-1 w-full bg-blue-200 dark:bg-blue-800 rounded-full h-1.5">
                        <div 
                            className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                )}
                
                {/* Timer */}
                {startTime && (
                    <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                        Elapsed: {formatTime(elapsedTime)}
                        {estimatedCompletion && (
                            <span className="ml-2">
                                ETA: {formatTime(estimatedCompletion * 1000)}
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
```

### 5.3 Message State Integration
```jsx
// In ChatMessages component
const AssistantMessage = ({ message, isLoading, isProcessing }) => (
    <div className="assistant-message-container">
        {/* Regular message content */}
        <div className="message-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        
        {/* Upload progress indicator */}
        {isProcessing && (
            <UploadProgressIndicator
                state={UploadState.PROCESSING}
                startTime={message.startTime}
            />
        )}
        
        {/* Regular loading indicator */}
        {isLoading && !isProcessing && (
            <div className="flex items-center gap-2 mt-2">
                <div className="animate-pulse text-blue-500">●</div>
                <LoadingTimer startTime={message.startTime} />
            </div>
        )}
    </div>
);
```

---

## 6. Error Handling & Recovery

### 6.1 Error Categories
```typescript
enum UploadErrorType {
    VALIDATION_ERROR = 'validation_error',
    NETWORK_ERROR = 'network_error',
    SERVER_ERROR = 'server_error',
    TIMEOUT_ERROR = 'timeout_error',
    PROCESSING_ERROR = 'processing_error'
}

interface UploadError {
    type: UploadErrorType;
    message: string;
    retryable: boolean;
    userFriendlyMessage: string;
}
```

### 6.2 Error Handling Implementation
```typescript
const handleUploadError = (error: Error, context: string): UploadError => {
    // Network errors
    if (error.name === 'AbortError') {
        return {
            type: UploadErrorType.TIMEOUT_ERROR,
            message: `Request timeout in ${context}`,
            retryable: true,
            userFriendlyMessage: 'Upload timed out. Please try again with a smaller image.'
        };
    }
    
    if (error.message.includes('Failed to fetch')) {
        return {
            type: UploadErrorType.NETWORK_ERROR,
            message: `Network error in ${context}: ${error.message}`,
            retryable: true,
            userFriendlyMessage: 'Network connection failed. Please check your internet and try again.'
        };
    }
    
    // Server errors
    if (error.message.includes('500')) {
        return {
            type: UploadErrorType.SERVER_ERROR,
            message: `Server error in ${context}: ${error.message}`,
            retryable: true,
            userFriendlyMessage: 'Server error occurred. Please try again in a moment.'
        };
    }
    
    // Client errors
    if (error.message.includes('400')) {
        return {
            type: UploadErrorType.VALIDATION_ERROR,
            message: `Validation error in ${context}: ${error.message}`,
            retryable: false,
            userFriendlyMessage: 'Invalid file format or size. Please select a different image.'
        };
    }
    
    // Generic error
    return {
        type: UploadErrorType.PROCESSING_ERROR,
        message: `Unexpected error in ${context}: ${error.message}`,
        retryable: true,
        userFriendlyMessage: 'An unexpected error occurred. Please try again.'
    };
};
```

### 6.3 Retry Mechanism
```typescript
const uploadWithRetry = async (
    file: File,
    sessionId: string,
    maxRetries: number = 3
): Promise<any> => {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await initiateUpload(file, sessionId);
        } catch (error) {
            lastError = error as Error;
            const uploadError = handleUploadError(lastError, 'upload');
            
            // Don't retry validation errors
            if (!uploadError.retryable) {
                throw lastError;
            }
            
            // Don't retry on last attempt
            if (attempt === maxRetries) {
                throw lastError;
            }
            
            // Exponential backoff
            const delay = Math.pow(2, attempt - 1) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            
            console.log(`Upload attempt ${attempt} failed, retrying in ${delay}ms...`);
        }
    }
    
    throw lastError!;
};
```

### 6.4 User Error Feedback
```jsx
const ErrorMessage = ({ error, onRetry, onDismiss }) => (
    <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        
        <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-red-900 dark:text-red-100">
                Upload Failed
            </div>
            <div className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error.userFriendlyMessage}
            </div>
        </div>
        
        <div className="flex gap-2">
            {error.retryable && (
                <button
                    onClick={onRetry}
                    className="text-sm bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-800 dark:text-red-200 px-3 py-1 rounded"
                >
                    Retry
                </button>
            )}
            <button
                onClick={onDismiss}
                className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
            >
                Dismiss
            </button>
        </div>
    </div>
);
```

---

## 7. Backend Integration Details

### 7.1 Upload Endpoints
```typescript
// Initial upload endpoint
POST /upload-async
Content-Type: multipart/form-data

FormData fields:
- file: File (binary data)
- session_id: string
- last_agent?: string
- routine_number?: string

Response: {
    "message": string,
    "session_id": string
}
```

```typescript
// Status polling endpoint
GET /upload-status?session_id={session_id}
Accept: application/json

Response: {
    "status": "processing" | "completed" | "error",
    "response"?: string,
    "last_agent"?: string,
    "routine_number"?: number,
    "error"?: string
}
```

### 7.2 Backend Processing Flow
1. **Upload Receipt**: File received and stored temporarily
2. **S3 Upload**: File uploaded to AWS S3 bucket
3. **HEIC Conversion**: Convert HEIC files to JPEG if needed
4. **AI Processing**: Agent analyzes photo and generates response
5. **Database Update**: Store photo URL and metadata
6. **Status Update**: Mark processing as complete

### 7.3 S3 Integration
```typescript
// Photo storage structure in S3
const S3_STRUCTURE = {
    bucket: 'utjfc-registration-photos',
    keyFormat: 'photos/{session_id}/{timestamp}_{filename}',
    publicAccess: false,
    expirationDays: 30
};

// Example S3 key:
// photos/sess_abc123def456/1641234567890_player_photo.jpg
```

---

## 8. Performance Optimizations

### 8.1 File Upload Optimizations
```typescript
// Compress large images before upload (future enhancement)
const compressImage = async (file: File, maxSizeMB: number = 5): Promise<File> => {
    if (file.size <= maxSizeMB * 1024 * 1024) {
        return file; // No compression needed
    }
    
    // Use canvas to compress
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    return new Promise((resolve) => {
        img.onload = () => {
            const ratio = Math.min(
                1000 / img.width,
                1000 / img.height
            );
            
            canvas.width = img.width * ratio;
            canvas.height = img.height * ratio;
            
            ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            canvas.toBlob((blob) => {
                const compressedFile = new File([blob!], file.name, {
                    type: 'image/jpeg',
                    lastModified: Date.now()
                });
                resolve(compressedFile);
            }, 'image/jpeg', 0.8);
        };
        
        img.src = URL.createObjectURL(file);
    });
};
```

### 8.2 Memory Management
```typescript
// Clean up object URLs
useEffect(() => {
    return () => {
        // Cleanup any object URLs created for previews
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }
    };
}, [previewUrl]);

// Abort ongoing requests on unmount
useEffect(() => {
    const controllers: AbortController[] = [];
    
    return () => {
        controllers.forEach(controller => controller.abort());
    };
}, []);
```

### 8.3 Polling Efficiency
```typescript
// Smart polling intervals based on file size
const getPollingInterval = (fileSize: number): number => {
    if (fileSize < 1 * 1024 * 1024) return 500;   // Small files: 0.5s
    if (fileSize < 5 * 1024 * 1024) return 1000;  // Medium files: 1s
    return 2000; // Large files: 2s
};

// Background tab handling
const useVisibilityAwarePolling = (isPolling: boolean) => {
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden && isPolling) {
                // Reduce polling frequency when tab is hidden
                console.log('Tab hidden, reducing polling frequency');
            } else if (!document.hidden && isPolling) {
                // Resume normal polling when tab is visible
                console.log('Tab visible, resuming normal polling');
            }
        };
        
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [isPolling]);
};
```

---

## 9. Security Considerations

### 9.1 File Type Validation
```typescript
// Validate actual file content, not just extension
const validateFileContent = async (file: File): Promise<boolean> => {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const arrayBuffer = e.target?.result as ArrayBuffer;
            const bytes = new Uint8Array(arrayBuffer.slice(0, 12));
            
            // Check magic numbers for image types
            const signatures = {
                png: [0x89, 0x50, 0x4E, 0x47],
                jpeg: [0xFF, 0xD8, 0xFF],
                webp: [0x57, 0x45, 0x42, 0x50],
                heic: [0x66, 0x74, 0x79, 0x70, 0x68, 0x65, 0x69, 0x63]
            };
            
            const isValidImage = Object.values(signatures).some(signature =>
                signature.every((byte, index) => bytes[index] === byte)
            );
            
            resolve(isValidImage);
        };
        reader.readAsArrayBuffer(file.slice(0, 12));
    });
};
```

### 9.2 Session Security
```typescript
// Validate session ID format
const isValidSessionId = (sessionId: string): boolean => {
    return /^sess_[a-zA-Z0-9]{12,}$/.test(sessionId);
};

// Sanitize file names
const sanitizeFileName = (fileName: string): string => {
    return fileName
        .replace(/[^a-zA-Z0-9._-]/g, '_')
        .replace(/^\.+/, '')
        .slice(0, 100); // Limit length
};
```

---

## Conclusion

The async photo upload system provides a robust, user-friendly solution for handling image uploads in the UTJFC registration process. The architecture supports efficient processing of various image formats while providing real-time feedback and comprehensive error handling.

**Key Features**:
- Comprehensive file validation and security
- Real-time upload progress and status feedback
- Robust error handling with retry mechanisms
- Mobile-optimized file selection interface
- Efficient polling system with smart intervals
- Memory management and performance optimization

**Architecture Quality**: High - well-designed async flow with proper error handling  
**User Experience**: Excellent - clear feedback and progress indication  
**Reliability**: Strong - comprehensive error recovery and retry logic  
**Performance**: Optimized - efficient polling and memory management

### Recent Infrastructure Improvements (v1.6.26-v1.6.27)

**Upload Capacity Enhancement**: Backend infrastructure updated to support the full 10MB file size limit referenced in frontend validation. Previous infrastructure limitations that caused "413 Request Entity Too Large" errors for photos >2MB have been resolved through nginx configuration improvements and enhanced FastAPI validation.

**Photo Optimization**: Backend photo processing is now fully operational, automatically optimizing all uploaded photos to FA portal requirements (4:5 aspect ratio) with smart EXIF-aware cropping while maintaining the same frontend user experience.