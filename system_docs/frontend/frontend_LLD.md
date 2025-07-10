# Frontend Low Level Design (LLD)
## UTJFC Chat Application

### Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Application Entry Point & Routing](#application-entry-point--routing)
3. [Chat Page Core Functionality](#chat-page-core-functionality)
4. [Component Analysis](#component-analysis)
5. [State Management](#state-management)
6. [Styling & Theme System](#styling--theme-system)
7. [Mobile Device Optimization](#mobile-device-optimization)
8. [API Integration](#api-integration)
9. [Performance Considerations](#performance-considerations)
10. [Known Issues & Potential Solutions](#known-issues--potential-solutions)

---

## Architecture Overview

### Technology Stack
- **Framework**: Next.js 15+ with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS with custom CSS variables
- **UI Components**: Custom React components
- **Icons**: Lucide React
- **Fonts**: Geist Sans & Geist Mono (Google Fonts)

### Project Structure
```
src/
├── app/
│   ├── chat/
│   │   ├── _components/
│   │   │   ├── chat-input.tsx
│   │   │   ├── chat-messages.tsx
│   │   └── page.tsx
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── config/
│   └── environment.ts
└── lib/
    └── utils.ts
```

---

## Application Entry Point & Routing

### CloudFront Redirect Mechanism
Users access the chat through a multi-step redirect process:

1. **Initial Request**: `urmstontownjfc.co.uk/chat`
2. **Hostinger Redirect**: JavaScript in website header detects `/chat` path
3. **CloudFront Redirect**: Browser redirected to `https://d1ahgtos8kkd8y.cloudfront.net/chat/index.html`
4. **Next.js Routing**: App Router serves the chat page

```javascript
// Hostinger Header Script
if (window.location.pathname === '/chat' || window.location.pathname === '/chat/') {
    window.location.replace('https://d1ahgtos8kkd8y.cloudfront.net/chat/index.html');
}
```

### Root Layout Configuration
The `layout.tsx` establishes critical mobile viewport settings:

```typescript
<meta
  name="viewport"
  content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
/>
```

**Key Properties:**
- `user-scalable=no`: Prevents zoom (can cause mobile input issues)
- `viewport-fit=cover`: Supports iPhone notch/safe areas
- `maximum-scale=1.0`: Locks zoom level

---

## Chat Page Core Functionality

### Main Page Component (`chat/page.tsx`)

#### Component Architecture
The chat page uses a sophisticated state management pattern with `useReducer` for complex state transitions:

```typescript
interface ChatState {
    messages: { [id: string]: Message };
    messageOrder: string[];
    isLoading: boolean;
    loadingMessageId: string | null;
    currentAssistantMessageId: string | null;
}
```

#### Key Features Implementation

**1. Session Management**
```typescript
function getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('chat_session_id');
    if (!sessionId) {
        sessionId = generateSessionId();
        sessionStorage.setItem('chat_session_id', sessionId);
    }
    return sessionId;
}
```

**2. Agent State Persistence**
The application maintains conversation context across browser sessions:
- `last_agent`: Tracks which AI agent is handling the conversation
- `routine_number`: Maintains workflow state for complex interactions

**3. Typing Animation System**
```typescript
const simulateTyping = (dispatch, messageId, fullContent, agentName) => {
    const chunks = fullContent.split('');
    let currentChunkIndex = 0;
    
    function typeNextChunk() {
        if (currentChunkIndex < chunks.length) {
            const delta = chunks[currentChunkIndex];
            dispatch({ type: 'APPEND_DELTA', payload: { id: messageId, delta } });
            currentChunkIndex++;
            setTimeout(typeNextChunk, TYPING_SPEED_MS);
        }
    }
};
```

#### Layout Structure
```jsx
<div className="flex flex-col h-dvh w-screen overflow-x-hidden">
    {/* Header - Fixed height 60px */}
    <header className="flex-shrink-0 h-[60px]">
        {/* Clear Chat & Home buttons */}
    </header>
    
    {/* Message Area - Flexible height */}
    <div className="flex-1 overflow-y-auto">
        <ChatMessages />
    </div>
    
    {/* Scroll Button - Floating */}
    {showScrollDownButton && <button className="fixed bottom-24" />}
    
    {/* Input Area - Fixed bottom */}
    <div className="flex-shrink-0 p-3 bg-gray-50/80 backdrop-blur-md">
        <ChatInput />
    </div>
</div>
```

---

## Component Analysis

### ChatInput Component

#### Core Functionality
- **Auto-resize textarea** using `react-textarea-autosize`
- **File upload handling** with validation (10MB max, specific image types)
- **Keyboard shortcuts** (Enter to send, Shift+Enter for new line)
- **Loading state management** with disabled states

#### Mobile Optimizations
```typescript
// Touch-friendly button sizing
className="p-2 touch-manipulation"

// Auto-focus management
useEffect(() => {
    if (!isLoading) {
        textareaRef.current?.focus();
    }
}, [isLoading]);
```

#### Layout Implementation
```jsx
<form className="flex flex-col w-full max-w-full mx-auto gap-2 p-3 sm:p-4 
                 border border-gray-300/50 dark:border-gray-600/50 
                 rounded-2xl sm:rounded-3xl bg-white/80 dark:bg-gray-800/80 
                 shadow-lg backdrop-blur-md">
    
    {/* Textarea Row */}
    <TextareaAutosize className="w-full resize-none overflow-y-auto max-h-60" />
    
    {/* Button Row */}
    <div className="flex justify-between items-center h-8">
        <div className="flex items-center gap-1">
            {/* File Upload & Reset buttons */}
        </div>
        {/* Send button */}
    </div>
</form>
```

### ChatMessages Component

#### Message Rendering System
- **Markdown support** with `react-markdown` and `remark-gfm`
- **Avatar display** (toggleable via `AVATAR_ON` flag)
- **Copy functionality** for each message
- **Loading timer** showing response time

#### Message Layout Patterns
```jsx
// User messages - Right aligned
<div className="flex justify-end">
    <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl p-3 max-w-[85%]">

// Assistant messages - Left aligned with avatar
<div className="flex items-start gap-2">
    {AVATAR_ON && <Image src="/logo.svg" />}
    <div className="rounded-lg p-3">
```

---

## State Management

### Reducer Pattern Implementation
The chat uses a sophisticated reducer pattern handling 7 action types:

1. **ADD_USER_MESSAGE**: Adds user input to message list
2. **START_ASSISTANT_MESSAGE**: Creates loading message placeholder
3. **APPEND_DELTA**: Streams content character by character
4. **UPDATE_AGENT_NAME**: Updates which AI agent is responding
5. **COMPLETE_ASSISTANT_MESSAGE**: Finalizes message and stops loading
6. **SET_ERROR**: Handles API errors gracefully
7. **RESET_CHAT**: Clears all state and session data

### Performance Optimizations
```typescript
// Memoized message ordering
const orderedMessages = useMemo(() => 
    messageOrder.map(id => messages[id]).filter(Boolean)
, [messageOrder, messages]);

// Callback memoization
const handleSendMessage = useCallback(async (currentInput: string) => {
    // Implementation
}, [dispatch, scrollToVeryBottom]);
```

---

## Styling & Theme System

### CSS Architecture
1. **TailwindCSS** for utility-first styling
2. **CSS Custom Properties** for theme variables
3. **Global CSS** for mobile-specific optimizations

### Theme Implementation
```css
:root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* ... other properties */
}

.dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark theme overrides */
}
```

### Responsive Design Strategy
- **Mobile-first approach** with `sm:` breakpoints
- **Container sizing**: `max-w-4xl` on desktop, full width on mobile
- **Spacing system**: Responsive padding (`p-3 sm:p-4`)

---

## Mobile Device Optimization

### Viewport Configuration Issues
**Current Setup:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
```

**Potential Issues:**
- `user-scalable=no` can cause iOS input focus problems
- `maximum-scale=1.0` prevents accessibility zoom
- May conflict with iOS Safari's dynamic viewport behavior

### CSS Mobile Optimizations

#### Scroll Prevention
```css
html, body {
    overflow-x: hidden;
    overflow-y: hidden;
    height: 100%;
    overscroll-behavior-x: none;
}
```

#### Touch Targets
```css
@media (max-width: 640px) {
    button, [role="button"] {
        min-height: 44px;
        min-width: 44px;
    }
}
```

#### Safe Area Support
```css
.safe-area-bottom {
    padding-bottom: calc(env(safe-area-inset-bottom, 0) + 2.5rem);
}

.safe-area-top {
    padding-top: env(safe-area-inset-top, 0);
}
```

#### iOS Scrolling Enhancement
```css
.overflow-y-auto {
    -webkit-overflow-scrolling: touch;
}
```

### Dynamic Viewport Handling
The app uses `h-dvh` (dynamic viewport height) instead of `h-screen` to handle mobile browser UI changes:

```jsx
<div className="flex flex-col h-dvh w-screen overflow-x-hidden">
```

---

## API Integration

### Environment Configuration
```typescript
const config = {
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:8000'
    : 'https://d1ahgtos8kkd8y.cloudfront.net/api',
  
  get UPLOAD_URL() {
    return `${this.API_BASE_URL}/upload`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};
```

### Request Handling
Both chat and file upload include agent state management:

```typescript
const requestPayload = { 
    user_message: currentInput, 
    session_id: sessionId 
};

// Add agent state if available
if (agentState.last_agent) {
    requestPayload.last_agent = agentState.last_agent;
}
if (agentState.routine_number !== null) {
    requestPayload.routine_number = agentState.routine_number;
}
```

---

## Performance Considerations

### Optimization Strategies
1. **Component Memoization**: Key callbacks and computed values
2. **Efficient Re-renders**: Reducer pattern minimizes unnecessary updates
3. **Lazy Loading**: Messages rendered on-demand
4. **Smooth Scrolling**: Intersection observer for scroll management

### Memory Management
- Session storage for persistence
- Message cleanup on reset
- Proper event listener cleanup

---

## Known Issues & Potential Solutions

### Mobile Rendering Issue Analysis

**Problem**: Page renders correctly initially but breaks after input interaction, showing scrollbars.

**Likely Causes:**

1. **Viewport Meta Tag Conflicts**
   ```html
   <!-- Current (problematic) -->
   <meta name="viewport" content="user-scalable=no, maximum-scale=1.0" />
   
   <!-- Recommended -->
   <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
   ```

2. **iOS Safari Input Focus Behavior**
   - iOS Safari zooms on input focus by default
   - `user-scalable=no` can cause layout thrashing
   - Dynamic viewport changes during keyboard appearance

3. **CloudFront Redirect Timing**
   - Multiple redirects may interfere with initial viewport calculation
   - JavaScript redirect happens after initial page load

### Recommended Solutions

#### 1. Viewport Meta Tag Fix
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

#### 2. iOS Input Focus Handling
```css
/* Prevent zoom on input focus for font-size >= 16px */
input, textarea {
    font-size: 16px;
}

/* Alternative: CSS-only zoom prevention */
@media screen and (-webkit-min-device-pixel-ratio: 0) {
    select, textarea, input[type="text"] {
        font-size: 16px;
    }
}
```

#### 3. Enhanced Layout Stability
```jsx
// Add layout shift prevention
<div className="flex flex-col h-dvh w-screen overflow-x-hidden">
    {/* Add min-height to prevent collapse */}
    <div className="flex-1 overflow-y-auto min-h-0">
```

#### 4. Input Focus Management
```typescript
// Delay focus to ensure viewport stability
useEffect(() => {
    const timer = setTimeout(() => {
        if (!isLoading && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, 100);
    return () => clearTimeout(timer);
}, [isLoading]);
```

#### 5. Scroll Management Enhancement
```typescript
// Prevent scroll during input focus
const handleInputFocus = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
    }
}, []);

const handleInputBlur = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        document.body.style.position = '';
        document.body.style.width = '';
    }
}, []);
```

### Testing Recommendations
1. Test on actual iOS devices (iPhone Safari)
2. Test the redirect flow specifically
3. Monitor layout shifts with Chrome DevTools
4. Test with different iOS versions
5. Verify keyboard appearance/disappearance behavior

---

This LLD provides a comprehensive analysis of your frontend chat application. The mobile rendering issue is likely related to the viewport meta tag configuration combined with iOS Safari's input focus behavior. The recommended solutions should resolve the scrollbar appearance and layout stability issues. 