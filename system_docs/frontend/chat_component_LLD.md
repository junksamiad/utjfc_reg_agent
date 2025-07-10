# Chat Component Low-Level Design (LLD)

## Document Overview
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Detailed technical documentation for the chat interface components  
**Scope**: Chat UI components, state management, and user interaction patterns  

---

## 1. Component Architecture Overview

### 1.1 Component Hierarchy
```
ChatPage ("/chat/page.tsx")
├── Header Section
│   ├── Clear Chat Button
│   └── Home Button
├── ChatMessages Component
│   ├── Message List
│   ├── Avatar Display (conditional)
│   ├── Loading Timer
│   └── Copy Functionality
├── Scroll Controls
│   └── Scroll-to-Bottom Button (conditional)
└── ChatInput Component
    ├── Auto-resize Textarea
    ├── File Upload Button
    ├── Reset Button
    └── Send Button
```

### 1.2 State Management Pattern
```typescript
// Central state managed via useReducer
const [state, dispatch] = useReducer(chatReducer, initialChatState);

interface ChatState {
    messages: { [id: string]: Message };
    messageOrder: string[];
    isLoading: boolean;
    loadingMessageId: string | null;
    currentAssistantMessageId: string | null;
    processingMessages: { [id: string]: boolean };
}
```

---

## 2. ChatPage Component (/chat/page.tsx)

### 2.1 Core Responsibilities
- **State Management**: Central chat state via useReducer
- **Session Management**: Browser session persistence
- **Agent State**: Tracking conversation context
- **Layout Orchestration**: Coordinating child components
- **Scroll Management**: Auto-scroll and manual controls

### 2.2 State Structure
```typescript
interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentName?: string;
    isLoading?: boolean;
    startTime?: number;
}

type ChatAction =
    | { type: 'START_ASSISTANT_MESSAGE'; payload: { id: string; agentName?: string } }
    | { type: 'APPEND_DELTA'; payload: { id: string; delta: string } }
    | { type: 'UPDATE_AGENT_NAME'; payload: { id: string; agentName: string } }
    | { type: 'COMPLETE_ASSISTANT_MESSAGE'; payload: { id: string } }
    | { type: 'ADD_USER_MESSAGE'; payload: Message }
    | { type: 'SET_ERROR'; payload: { errorContent: string } }
    | { type: 'RESET_CHAT' }
    | { type: 'SET_PROCESSING'; payload: { id: string; processing: boolean } };
```

### 2.3 Session Management
```typescript
// Session ID generation and persistence
function getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('chat_session_id');
    if (!sessionId) {
        sessionId = generateSessionId();
        sessionStorage.setItem('chat_session_id', sessionId);
    }
    return sessionId;
}

// Agent state persistence
function storeAgentState(lastAgent: string | null, routineNumber: number | null) {
    if (lastAgent) {
        sessionStorage.setItem('last_agent', lastAgent);
    }
    if (routineNumber !== null) {
        sessionStorage.setItem('routine_number', routineNumber.toString());
    }
}
```

### 2.4 Typing Simulation System
```typescript
const simulateTyping = (
    dispatch: React.Dispatch<ChatAction>,
    messageId: string,
    fullContent: string,
    agentName?: string
) => {
    const chunks = fullContent.split('');
    let currentChunkIndex = 0;
    
    function typeNextChunk() {
        if (currentChunkIndex < chunks.length) {
            const delta = chunks[currentChunkIndex];
            dispatch({ 
                type: 'APPEND_DELTA', 
                payload: { id: messageId, delta } 
            });
            currentChunkIndex++;
            setTimeout(typeNextChunk, TYPING_SPEED_MS); // 2ms per character
        } else {
            dispatch({ 
                type: 'COMPLETE_ASSISTANT_MESSAGE', 
                payload: { id: messageId } 
            });
        }
    }
    
    typeNextChunk();
};
```

### 2.5 Layout Structure
```jsx
<div className="flex flex-col h-dvh w-screen overflow-x-hidden bg-white dark:bg-gray-900">
    {/* Header - Fixed 60px height */}
    <header className="flex-shrink-0 h-[60px] bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200/50 dark:border-gray-700/50">
        <div className="flex justify-between items-center h-full px-4">
            {/* Clear Chat Button */}
            <Button onClick={handleClearChat}>Clear Chat</Button>
            
            {/* Home Button */}
            <Button onClick={() => router.push('/')}>
                <Home className="w-5 h-5" />
            </Button>
        </div>
    </header>

    {/* Messages Area - Flexible height */}
    <div className="flex-1 overflow-y-auto -webkit-overflow-scrolling-touch" ref={messagesEndRef}>
        <ChatMessages 
            messages={orderedMessages}
            isLoading={state.isLoading}
            loadingMessageId={state.loadingMessageId}
            processingMessages={state.processingMessages}
        />
    </div>

    {/* Scroll Control - Floating */}
    {showScrollDownButton && (
        <button 
            onClick={scrollToVeryBottom}
            className="fixed bottom-24 right-4 bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg z-10"
        >
            <ChevronDown className="w-5 h-5" />
        </button>
    )}

    {/* Input Area - Fixed bottom */}
    <div className="flex-shrink-0 p-3 bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-700/50">
        <ChatInput 
            onSendMessage={handleSendMessage}
            isLoading={state.isLoading}
            sessionId={sessionId}
            dispatch={dispatch}
        />
    </div>
</div>
```

### 2.6 Scroll Management
```typescript
// Scroll state management
const [isScrolledToVeryBottom, setIsScrolledToVeryBottom] = useState(true);
const [showScrollDownButton, setShowScrollDownButton] = useState(false);

// Auto-scroll logic
const scrollToVeryBottom = useCallback(() => {
    if (messagesEndRef.current) {
        messagesEndRef.current.scrollTop = messagesEndRef.current.scrollHeight;
    }
}, []);

// Scroll detection with 10px threshold
const handleScroll = useCallback(() => {
    if (messagesEndRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = messagesEndRef.current;
        const isAtBottom = scrollHeight - scrollTop - clientHeight <= 10;
        
        setIsScrolledToVeryBottom(isAtBottom);
        setShowScrollDownButton(!isAtBottom && orderedMessages.length > 0);
    }
}, [orderedMessages.length]);
```

---

## 3. ChatMessages Component

### 3.1 Core Responsibilities
- **Message Rendering**: Display user and assistant messages
- **Markdown Processing**: Rich text rendering with react-markdown
- **Loading States**: Show loading indicators and timers
- **Copy Functionality**: Enable message copying
- **Avatar Display**: Conditional UTJFC logo display

### 3.2 Component Structure
```jsx
export default function ChatMessages({ 
    messages, 
    isLoading, 
    loadingMessageId, 
    processingMessages 
}) {
    return (
        <div className="max-w-4xl mx-auto p-4 space-y-6">
            {messages.map((message) => (
                <div key={message.id} className="message-container">
                    {message.role === 'user' ? (
                        <UserMessage message={message} />
                    ) : (
                        <AssistantMessage 
                            message={message}
                            isLoading={isLoading && loadingMessageId === message.id}
                            isProcessing={processingMessages[message.id]}
                        />
                    )}
                </div>
            ))}
        </div>
    );
}
```

### 3.3 User Message Layout
```jsx
const UserMessage = ({ message }) => (
    <div className="flex justify-end">
        <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl p-3 max-w-[85%] relative group">
            <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                </ReactMarkdown>
            </div>
            
            {/* Copy button */}
            <button 
                onClick={() => copyToClipboard(message.content)}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            >
                <Copy className="w-4 h-4" />
            </button>
        </div>
    </div>
);
```

### 3.4 Assistant Message Layout
```jsx
const AssistantMessage = ({ message, isLoading, isProcessing }) => (
    <div className="flex items-start gap-2">
        {/* Avatar (conditional) */}
        {AVATAR_ON && (
            <Image
                src="/logo.svg"
                alt="UTJFC Logo"
                width={32}
                height={32}
                className="rounded-full flex-shrink-0 mt-1"
            />
        )}
        
        <div className="flex-1 min-w-0">
            {/* Agent name */}
            {message.agentName && (
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                    {message.agentName}
                </div>
            )}
            
            {/* Message content */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-3 shadow-sm border border-gray-200/50 dark:border-gray-700/50 relative group">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                    </ReactMarkdown>
                </div>
                
                {/* Loading indicator */}
                {(isLoading || isProcessing) && (
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
                        <div className="animate-pulse">●</div>
                        <LoadingTimer startTime={message.startTime} />
                    </div>
                )}
                
                {/* Copy button */}
                <button 
                    onClick={() => copyToClipboard(message.content)}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100"
                >
                    <Copy className="w-4 h-4" />
                </button>
            </div>
        </div>
    </div>
);
```

### 3.5 Loading Timer Component
```jsx
const LoadingTimer = ({ startTime }) => {
    const [elapsedTime, setElapsedTime] = useState(0);
    
    useEffect(() => {
        if (!startTime) return;
        
        const interval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            setElapsedTime(elapsed);
        }, 100); // Update every 100ms for smooth timer
        
        return () => clearInterval(interval);
    }, [startTime]);
    
    const formatTime = (ms) => {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const tenths = Math.floor((ms % 1000) / 100);
        
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${tenths}`;
    };
    
    return <span>{formatTime(elapsedTime)}</span>;
};
```

### 3.6 Copy Functionality
```typescript
const copyToClipboard = async (text: string) => {
    try {
        await navigator.clipboard.writeText(text);
        // Could add toast notification here
    } catch (err) {
        console.error('Failed to copy text: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
};
```

---

## 4. ChatInput Component

### 4.1 Core Responsibilities
- **Text Input**: Auto-resizing textarea for user messages
- **File Upload**: Photo upload with validation
- **Send Control**: Message submission and loading states
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Mobile Optimization**: iOS focus handling

### 4.2 Component Structure
```jsx
export default function ChatInput({ onSendMessage, isLoading, sessionId, dispatch }) {
    const [input, setInput] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const textareaRef = useRef(null);
    const fileInputRef = useRef(null);
    
    return (
        <form onSubmit={handleSubmit} className="chat-input-form">
            {/* Main input container */}
            <div className="flex flex-col w-full max-w-full mx-auto gap-2 p-3 border border-gray-300/50 dark:border-gray-600/50 rounded-2xl bg-white/80 dark:bg-gray-800/80 shadow-lg backdrop-blur-md">
                
                {/* Textarea row */}
                <TextareaAutosize
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    placeholder="Type your message..."
                    className="textarea-styles"
                    minRows={1}
                    maxRows={10}
                />
                
                {/* Controls row */}
                <div className="flex justify-between items-center h-8">
                    <div className="flex items-center gap-1">
                        {/* File upload button */}
                        <button type="button" onClick={() => fileInputRef.current?.click()}>
                            <Upload className="w-5 h-5" />
                        </button>
                        
                        {/* Reset button */}
                        <button type="button" onClick={handleReset}>
                            <RotateCcw className="w-5 h-5" />
                        </button>
                        
                        {/* File indicator */}
                        {selectedFile && (
                            <span className="text-sm text-green-600">
                                {selectedFile.name}
                            </span>
                        )}
                    </div>
                    
                    {/* Send button */}
                    <button 
                        type="submit" 
                        disabled={isLoading || (!input.trim() && !selectedFile)}
                        className="send-button-styles"
                    >
                        {isLoading ? (
                            <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>
            
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp,image/heic"
                onChange={handleFileSelect}
                className="hidden"
            />
        </form>
    );
}
```

### 4.3 Auto-resize Textarea
```typescript
// TextareaAutosize configuration
<TextareaAutosize
    ref={textareaRef}
    value={input}
    onChange={(e) => setInput(e.target.value)}
    className="w-full resize-none overflow-y-auto max-h-60 bg-transparent border-0 outline-none placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-gray-100"
    placeholder="Type your message..."
    minRows={1}
    maxRows={10}
    style={{
        fontSize: '16px', // Prevents iOS zoom
        lineHeight: '1.5'
    }}
/>
```

### 4.4 File Upload System
```typescript
// File validation
const validateFile = (file: File): boolean => {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid image file (PNG, JPEG, JPG, WebP, HEIC)');
        return false;
    }
    
    if (file.size > maxSize) {
        alert('File size must be less than 10MB');
        return false;
    }
    
    return true;
};

// File selection handler
const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
        setSelectedFile(file);
    }
    e.target.value = ''; // Reset input
};
```

### 4.5 Keyboard Shortcuts
```typescript
const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!isLoading && (input.trim() || selectedFile)) {
            handleSubmit(e as any);
        }
    }
    // Shift+Enter creates new line (default behavior)
};
```

### 4.6 iOS Focus Handling
```typescript
// Detect iOS devices
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

// Focus handler to prevent viewport jumping
const handleFocus = useCallback(() => {
    if (isIOS) {
        // Prevent document scrolling on iOS
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
        document.body.style.top = `-${window.scrollY}px`;
    }
}, []);

// Blur handler to restore normal scrolling
const handleBlur = useCallback(() => {
    if (isIOS) {
        const scrollY = document.body.style.top;
        document.body.style.position = '';
        document.body.style.width = '';
        document.body.style.top = '';
        window.scrollTo(0, parseInt(scrollY || '0') * -1);
    }
}, []);

// Auto-focus management
useEffect(() => {
    if (!isLoading && textareaRef.current) {
        textareaRef.current.focus();
    }
}, [isLoading]);
```

### 4.7 Message Submission
```typescript
const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLoading) return;
    if (!input.trim() && !selectedFile) return;
    
    const currentInput = input.trim();
    const currentFile = selectedFile;
    
    // Clear input immediately for better UX
    setInput('');
    setSelectedFile(null);
    
    try {
        if (currentFile) {
            await handleFileUpload(currentFile);
        } else {
            await onSendMessage(currentInput);
        }
    } catch (error) {
        // Restore input on error
        setInput(currentInput);
        setSelectedFile(currentFile);
    }
};
```

---

## 5. Performance Optimizations

### 5.1 Component Memoization
```typescript
// Memoized message ordering
const orderedMessages = useMemo(() => 
    state.messageOrder.map(id => state.messages[id]).filter(Boolean)
, [state.messageOrder, state.messages]);

// Memoized callbacks
const handleSendMessage = useCallback(async (input: string) => {
    // Implementation
}, [dispatch, sessionId]);

const scrollToVeryBottom = useCallback(() => {
    if (messagesEndRef.current) {
        messagesEndRef.current.scrollTop = messagesEndRef.current.scrollHeight;
    }
}, []);
```

### 5.2 Efficient Re-renders
```typescript
// Reducer pattern minimizes re-renders
const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
    switch (action.type) {
        case 'APPEND_DELTA':
            return {
                ...state,
                messages: {
                    ...state.messages,
                    [action.payload.id]: {
                        ...state.messages[action.payload.id],
                        content: state.messages[action.payload.id].content + action.payload.delta
                    }
                }
            };
        // Other cases...
    }
};
```

### 5.3 Scroll Performance
```typescript
// Throttled scroll handler
const throttledHandleScroll = useCallback(
    throttle(handleScroll, 100),
    [handleScroll]
);

// Intersection Observer for better performance
useEffect(() => {
    const observer = new IntersectionObserver(
        ([entry]) => {
            setIsScrolledToVeryBottom(entry.isIntersecting);
        },
        { threshold: 1.0 }
    );
    
    if (messagesEndRef.current) {
        observer.observe(messagesEndRef.current);
    }
    
    return () => observer.disconnect();
}, []);
```

---

## 6. Accessibility Features

### 6.1 ARIA Labels
```jsx
// Screen reader support
<button 
    type="submit"
    disabled={isLoading}
    aria-label={isLoading ? "Sending message..." : "Send message"}
    aria-describedby="send-button-help"
>
    {/* Button content */}
</button>

<div id="send-button-help" className="sr-only">
    Press Enter to send message, Shift+Enter for new line
</div>
```

### 6.2 Keyboard Navigation
```typescript
// Focus management
const focusableElements = [
    textareaRef.current,
    fileInputRef.current,
    sendButtonRef.current
];

// Tab navigation support
const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Tab') {
        // Custom tab order if needed
    }
};
```

### 6.3 Screen Reader Support
```jsx
// Live region for dynamic content
<div aria-live="polite" aria-atomic="true" className="sr-only">
    {isLoading && "Assistant is typing..."}
    {state.currentAssistantMessageId && "New message received"}
</div>

// Message roles for screen readers
<div role="log" aria-label="Chat conversation">
    {messages.map(message => (
        <div key={message.id} role="article" aria-label={`${message.role} message`}>
            {message.content}
        </div>
    ))}
</div>
```

---

## 7. Error Handling

### 7.1 Component Error Boundaries
```jsx
// Error boundary wrapper (future enhancement)
class ChatErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    
    static getDerivedStateFromError(error) {
        return { hasError: true };
    }
    
    componentDidCatch(error, errorInfo) {
        console.error('Chat component error:', error, errorInfo);
    }
    
    render() {
        if (this.state.hasError) {
            return <ChatErrorFallback onRetry={this.handleRetry} />;
        }
        
        return this.props.children;
    }
}
```

### 7.2 Input Validation
```typescript
// Real-time input validation
const validateInput = (input: string): string | null => {
    if (input.length > 5000) {
        return "Message too long (maximum 5000 characters)";
    }
    return null;
};

// File validation with user feedback
const validateFile = (file: File): string | null => {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic'];
    
    if (!allowedTypes.includes(file.type)) {
        return "Please select a valid image file (PNG, JPEG, JPG, WebP, HEIC)";
    }
    
    if (file.size > 10 * 1024 * 1024) {
        return "File size must be less than 10MB";
    }
    
    return null;
};
```

---

## Conclusion

The chat component system provides a robust, accessible, and performant conversational interface optimized for the UTJFC registration process. The architecture supports complex state management, real-time interactions, and comprehensive mobile optimization while maintaining clean separation of concerns and excellent user experience.

**Key Strengths**:
- Clean component separation with clear responsibilities
- Efficient state management via useReducer pattern
- Comprehensive mobile optimizations
- Real-time typing simulation and feedback
- Robust error handling and validation
- Accessibility support throughout

**Architecture Quality**: High - well-structured with good performance characteristics  
**Maintainability**: Excellent - clear code organization and documentation  
**User Experience**: Outstanding - smooth, responsive, and intuitive interface