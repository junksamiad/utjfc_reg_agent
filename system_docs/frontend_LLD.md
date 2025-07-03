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
  content="width=device-width, initial-scale=1.0, viewport-fit=cover"
/>
```

**Key Properties (Updated for Mobile Compatibility):**
- `viewport-fit=cover`: Supports iPhone notch/safe areas
- **Removed `user-scalable=no`**: Was causing iOS layout thrashing on input focus
- **Removed `maximum-scale=1.0`**: Was conflicting with iOS Safari's dynamic viewport behavior

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
<div className="flex flex-col h-[calc(100dvh-0px)] bg-white dark:bg-gray-900">
    {/* Header - Sticky positioned */}
    <header className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 h-[60px] sm:px-6 border-b border-gray-200 dark:border-gray-700">
        {/* Clear Chat & Home buttons */}
    </header>
    
    {/* Message Area - Flexible height with bottom padding for auto-scroll */}
    <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto py-2 sm:py-4 bg-gray-50 dark:bg-gray-850 scroll-smooth min-h-0"
        onScroll={handleScroll}
    >
        <div className="mx-auto w-full max-w-4xl px-3 sm:px-4 pb-32 sm:pb-48 md:pb-64">
            <ChatMessages messages={orderedMessages} loadingMessageId={loadingMessageId} />
        </div>
    </div>
    
    {/* Scroll Button - Floating with responsive positioning */}
    {showScrollDownButton && (
        <button
            onClick={scrollToVeryBottom}
            className="fixed bottom-24 sm:bottom-32 left-1/2 -translate-x-1/2 z-20 p-2 sm:p-3 bg-gray-700 dark:bg-gray-200 text-white dark:text-black rounded-full shadow-lg hover:bg-gray-800 dark:hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-600 dark:focus:ring-gray-400 transition-opacity duration-300 touch-manipulation"
            aria-label="Scroll to bottom"
        >
            <ChevronDown size={20} />
        </button>
    )}

    {/* Input Area - Sticky bottom with backdrop blur */}
    <div className="sticky bottom-0 z-10 p-3 sm:p-4 bg-gray-50/80 dark:bg-gray-850/80 backdrop-blur-md border-t border-gray-200 dark:border-gray-700 safe-area-bottom">
        <div className="w-full max-w-4xl mx-auto">
            <ChatInput
                onSendMessage={handleSendMessage}
                onFileUpload={handleFileUpload}
                onReset={handleReset}
                isLoading={isLoading}
            />
        </div>
    </div>
</div>
```

## Auto-Scroll Functionality - RESTORED ✅

### Issue Resolution Summary

**Problem**: After mobile rendering fixes were implemented, the auto-scroll functionality stopped working. When users submitted messages, new content would appear behind/below the input area instead of auto-scrolling to show the conversation.

**Root Cause**: Layout structure changes during mobile optimization removed key elements needed for proper auto-scroll behavior.

### ✅ IMPLEMENTED AUTO-SCROLL SOLUTION (Deployed & Working)

**Date**: July 3, 2025  
**CloudFront Invalidation ID**: IELS2G8L1QQQ86R1RMCFT6IMJV

#### 1. Bottom Padding for Message Container ✅
**File**: `frontend/web/src/app/chat/page.tsx`
```jsx
<!-- BEFORE (problematic) -->
<div className="w-full max-w-4xl mx-auto px-4 py-4">
    <ChatMessages />
</div>

<!-- AFTER (fixed) -->
<div className="mx-auto w-full max-w-4xl px-3 sm:px-4 pb-32 sm:pb-48 md:pb-64">
    <ChatMessages messages={orderedMessages} loadingMessageId={loadingMessageId} />
</div>
```

**Key Change**: Added responsive bottom padding (`pb-32 sm:pb-48 md:pb-64`) to ensure new messages don't get hidden behind the input area when auto-scrolling to bottom.

#### 2. Sticky Positioning Restoration ✅
```jsx
<!-- BEFORE -->
<div className="flex-shrink-0 p-3 sm:p-4 bg-gray-50/80 dark:bg-gray-850/80 backdrop-blur-md border-t border-gray-200 dark:border-gray-700 safe-area-bottom">

<!-- AFTER -->
<div className="sticky bottom-0 z-10 p-3 sm:p-4 bg-gray-50/80 dark:bg-gray-850/80 backdrop-blur-md border-t border-gray-200 dark:border-gray-700 safe-area-bottom">
```

**Key Change**: Restored `sticky bottom-0 z-10` positioning for proper input area behavior.

#### 3. Smooth Scrolling Enhancement ✅
```jsx
<!-- BEFORE -->
<div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-850 min-h-0">

<!-- AFTER -->
<div className="flex-1 overflow-y-auto py-2 sm:py-4 bg-gray-50 dark:bg-gray-850 scroll-smooth min-h-0" onScroll={handleScroll}>
```

**Key Changes**:
- Added `scroll-smooth` class for better UX
- Added `onScroll={handleScroll}` directly to scrollable div
- Restored responsive padding (`py-2 sm:py-4`)

#### 4. Header Sticky Positioning ✅
```jsx
<!-- BEFORE -->
<header className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 h-[60px] sm:px-6 border-b border-gray-200 dark:border-gray-700 safe-area-top">

<!-- AFTER -->
<header className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 h-[60px] sm:px-6 border-b border-gray-200 dark:border-gray-700">
```

**Key Change**: Made header sticky (`sticky top-0 z-10`) for consistent positioning.

#### 5. Container Height Adjustment ✅
```jsx
<!-- BEFORE -->
<div className="flex flex-col h-dvh w-screen overflow-x-hidden bg-white dark:bg-gray-900">

<!-- AFTER -->
<div className="flex flex-col h-[calc(100dvh-0px)] bg-white dark:bg-gray-900">
```

**Key Change**: Updated to `h-[calc(100dvh-0px)]` to match working layout structure.

### 📱 Auto-Scroll Results - Fully Working ✅

**Tested on Desktop & Mobile:**
- ✅ Auto-scroll to bottom when user submits message
- ✅ New messages appear in visible area (not behind input)
- ✅ Smooth scrolling animation during auto-scroll
- ✅ Scroll button works correctly for manual navigation
- ✅ All mobile rendering optimizations preserved

### 💡 Key Technical Details

**Auto-Scroll Trigger Logic:**
```typescript
const handleSendMessage = useCallback(async (currentInput: string) => {
    // ... message creation logic
    
    // Scroll to bottom to show the new conversation
    setTimeout(() => {
        scrollToVeryBottom();
    }, 0);
    
    // ... API call logic
}, [dispatch, scrollToVeryBottom]);
```

**Bottom Padding Strategy:**
- `pb-32` (128px) on mobile - accounts for input area height
- `pb-48` (192px) on small screens - additional buffer 
- `pb-64` (256px) on medium+ screens - comfortable desktop spacing

This ensures when `scrollToVeryBottom()` is called, there's sufficient padding so the last message is fully visible above the input area.

### 🔄 Preserved Mobile Optimizations

All previous mobile fixes remain intact:
- ✅ Viewport meta tag without user-scalable restrictions
- ✅ iOS zoom prevention with 16px font sizes
- ✅ Input focus/blur handlers for iOS stability
- ✅ Layout stability with min-h-0 flex containers
- ✅ Touch-friendly button sizing and spacing

The auto-scroll functionality is now **completely restored** while maintaining all mobile compatibility improvements.

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

### Viewport Configuration - Fixed ✅
**Updated Setup (FIXED):**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

**Issues Resolved:**
- ✅ Removed `user-scalable=no` which was causing iOS input focus problems
- ✅ Removed `maximum-scale=1.0` which was preventing accessibility zoom
- ✅ Eliminated conflicts with iOS Safari's dynamic viewport behavior

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

## Mobile Rendering Issue - RESOLVED ✅

### Issue Resolution Summary

**Problem**: Page rendered correctly initially but broke after input interaction, showing scrollbars on iOS devices (iPhone Safari and Chrome).

**Root Causes Identified:**
1. **Viewport Meta Tag Conflicts** - `user-scalable=no` and `maximum-scale=1.0` causing iOS layout thrashing
2. **iOS Input Focus Behavior** - Font sizes < 16px triggering automatic zoom
3. **Layout Instability** - Flex containers collapsing during viewport changes

### ✅ IMPLEMENTED SOLUTIONS (Deployed & Working)

#### 1. Viewport Meta Tag Fix ✅
**File**: `frontend/web/src/app/layout.tsx`
```html
<!-- BEFORE (problematic) -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />

<!-- AFTER (fixed) -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

#### 2. iOS Zoom Prevention ✅
**File**: `frontend/web/src/app/globals.css`
```css
/* Prevent iOS zoom on input focus by ensuring font-size >= 16px */
input, textarea {
    font-size: 16px;
}

/* Additional iOS-specific input handling */
@media screen and (-webkit-min-device-pixel-ratio: 0) {
    select, textarea, input[type="text"] {
        font-size: 16px;
    }
}

/* Enhanced mobile input handling */
@media (max-width: 768px) {
    /* Prevent layout shifts on focus */
    textarea, input {
        transform: translateZ(0);
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
    }
    
    /* Improve touch scrolling performance */
    * {
        -webkit-overflow-scrolling: touch;
    }
}
```

#### 3. Layout Stability Enhancement ✅
**File**: `frontend/web/src/app/chat/page.tsx`
```jsx
<!-- BEFORE -->
<div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-850">

<!-- AFTER -->
<div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-850 min-h-0">
```

#### 4. Input Focus Management ✅
**File**: `frontend/web/src/app/chat/_components/chat-input.tsx`

**Delayed Focus for Viewport Stability:**
```typescript
useEffect(() => {
    // Delay focus to ensure viewport stability on mobile
    const timer = setTimeout(() => {
        textareaRef.current?.focus();
    }, 100);
    return () => clearTimeout(timer);
}, []);
```

**iOS-Specific Focus/Blur Handlers:**
```typescript
// iOS-specific input focus/blur handlers to prevent layout issues
const handleInputFocus = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
        document.body.style.top = `-${window.scrollY}px`;
    }
}, []);

const handleInputBlur = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        const scrollY = document.body.style.top;
        document.body.style.position = '';
        document.body.style.width = '';
        document.body.style.top = '';
        if (scrollY) {
            window.scrollTo(0, parseInt(scrollY || '0', 10) * -1);
        }
    }
}, []);
```

**Explicit Font Size Override:**
```jsx
<TextareaAutosize
    // ... other props
    style={{ fontSize: '16px' }}
    onFocus={handleInputFocus}
    onBlur={handleInputBlur}
/>
```

### 📱 Results - Fully Working ✅

**Tested on iPhone (Safari & Chrome):**
- ✅ No scrollbars appearing after input interaction
- ✅ Stable layout during keyboard appearance/disappearance  
- ✅ No unwanted zoom on input focus
- ✅ Smooth scrolling throughout the app
- ✅ Proper viewport handling during CloudFront redirects

### 🚀 Deployment Details

**Date**: July 3, 2025  
**CloudFront Invalidation ID**: I3Y5ES9HF70YF3IKX5U9TJ4BPM  
**Files Modified**: 
- `layout.tsx` - Viewport meta tag
- `globals.css` - Mobile CSS optimizations  
- `page.tsx` - Layout stability
- `chat-input.tsx` - Input focus management

### 💡 Key Learnings for Future

1. **16px Font Rule**: Always ensure inputs have minimum 16px font size to prevent iOS zoom
2. **Viewport Meta Tag**: Avoid `user-scalable=no` and `maximum-scale=1.0` on mobile
3. **Layout Stability**: Use `min-h-0` on flex containers that need to shrink
4. **iOS Detection**: Use `/iPhone|iPad|iPod/.test(navigator.userAgent)` for iOS-specific handling
5. **Focus Timing**: Delay auto-focus by 100ms for viewport stability

This mobile rendering issue is now **completely resolved** and documented for future reference. 