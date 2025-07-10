# UTJFC Registration Agent Frontend - High-Level Design (HLD)

## Document Overview
**Version**: 2.0  
**Date**: January 2025  
**Purpose**: Complete technical documentation for the UTJFC registration agent frontend system  
**Scope**: Frontend architecture, implementation details, and current state  

---

## 1. System Overview

### 1.1 Purpose
The frontend provides an interactive chat interface for Urmston Town Juniors Football Club (UTJFC) members to complete football club registrations through an AI-powered conversational agent system. The system handles new player registrations, re-registrations, and manages the complete registration workflow through natural language conversations.

### 1.2 Core Objectives
- **Conversational Interface**: Natural chat experience with realistic typing simulation
- **Agent Continuity**: Maintain conversation context across 35-step registration flow
- **Photo Upload Support**: Async photo processing for player registration
- **Session Management**: Persistent sessions with agent state tracking
- **Mobile-First Design**: Optimized for mobile devices where most registrations occur
- **Real-time Feedback**: Loading states, timers, and progress indicators

---

## 2. Technology Stack

### 2.1 Core Framework
```json
{
  "framework": "Next.js 15.3.1",
  "react": "19.0.0",
  "typescript": "^5",
  "styling": "Tailwind CSS 4.0",
  "package_manager": "pnpm"
}
```

### 2.2 Key Dependencies
```json
{
  "ui_components": {
    "lucide-react": "^0.507.0",
    "react-textarea-autosize": "^8.5.9",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.2.0"
  },
  "content_rendering": {
    "react-markdown": "^10.1.0",
    "remark-gfm": "^4.0.1",
    "@tailwindcss/typography": "^0.5.16"
  },
  "development": {
    "eslint": "^9",
    "postcss": "^8.5.3",
    "tailwindcss-animate": "^1.0.7"
  }
}
```

### 2.3 Build Configuration
- **Output**: Static Export (`output: 'export'`) for CloudFront deployment
- **Trailing Slash**: Enabled (`trailingSlash: true`)
- **Styling**: PostCSS with Tailwind CSS 4.0
- **Development**: Turbopack enabled for fast refresh
- **TypeScript**: Strict mode with Next.js integration
- **ESLint**: Configured to ignore errors during production builds

---

## 3. Architecture Overview

### 3.1 Application Structure
```
frontend/web/
├── src/app/
│   ├── layout.tsx           # Root layout with fonts & metadata
│   ├── page.tsx             # Home page (default Next.js template)
│   ├── globals.css          # Global styles & CSS variables
│   └── chat/
│       ├── page.tsx         # Main chat interface
│       └── _components/
│           ├── chat-input.tsx    # Input component with file upload
│           └── chat-messages.tsx # Message display component
├── src/config/
│   └── environment.ts       # Environment configuration
├── src/lib/
│   └── utils.ts             # Utility functions (cn helper)
├── public/                  # Static assets including UTJFC logo
└── out/                     # Static build output for deployment
```

### 3.2 Routing Architecture
- **App Router**: Next.js 13+ pattern with file-based routing
- **Static Export**: Generates static HTML for CloudFront deployment
- **Routes**:
  - `/` - Home page (default Next.js template)
  - `/chat` - Main registration chat interface

### 3.3 Component Hierarchy
```
RootLayout
├── Home Page ("/")
└── Chat Page ("/chat")
    ├── Header (navigation & clear chat controls)
    ├── ChatMessages (message display with avatars)
    ├── ScrollControls (auto-scroll management)
    └── ChatInput (input, file upload & send controls)
```

---

## 4. State Management Architecture

### 4.1 State Management Pattern
**Primary Pattern**: `useReducer` with TypeScript for complex chat state management

### 4.2 Chat State Structure
```typescript
interface ChatState {
    messages: { [id: string]: Message };         // Keyed message storage
    messageOrder: string[];                      // Maintains message sequence
    isLoading: boolean;                          // Global loading state
    loadingMessageId: string | null;             // Tracks which message is loading
    currentAssistantMessageId: string | null;    // Current assistant response
    processingMessages: { [id: string]: boolean }; // Background processing state
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentName?: string;                          // Which agent is responding
    isLoading?: boolean;                         // Message-level loading state
    startTime?: number;                          // Timestamp for response timing
}
```

### 4.3 State Actions
```typescript
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

### 4.4 Session Management
**Storage**: `sessionStorage` for browser session persistence

**Session Data**:
```typescript
// Session tracking
sessionStorage.setItem('chat_session_id', generateSessionId());

// Agent state for conversation continuity
sessionStorage.setItem('last_agent', agentName);
sessionStorage.setItem('routine_number', routineNumber.toString());
```

**Session Functions**:
- `getOrCreateSessionId()`: Generates or retrieves session ID
- `storeAgentState()`: Persists agent context
- `getAgentState()`: Retrieves agent context
- `clearAgentState()`: Resets agent state on chat reset

---

## 5. Core Features Implementation

### 5.1 Conversational Interface

#### 5.1.1 Typing Simulation
```typescript
const simulateTyping = (
    dispatch: React.Dispatch<ChatAction>,
    messageId: string,
    fullContent: string,
    agentName?: string
) => {
    // Character-by-character typing at 2ms per character
    // Creates realistic assistant response experience
};
```

#### 5.1.2 Message Flow
1. User sends message → `ADD_USER_MESSAGE`
2. Assistant message starts → `START_ASSISTANT_MESSAGE`
3. Backend response received → `simulateTyping()` called
4. Characters streamed → `APPEND_DELTA` actions
5. Message completed → `COMPLETE_ASSISTANT_MESSAGE`

### 5.2 Async Photo Upload System

#### 5.2.1 Supported Formats
```typescript
const allowedTypes = [
    'image/png',
    'image/jpeg', 
    'image/jpg',
    'image/webp',
    'image/heic'  // HEIC support for iOS photos
];
const maxSize = 10 * 1024 * 1024; // 10MB limit
```

#### 5.2.2 Upload Flow
1. File selection via hidden input
2. Client-side validation (type, size)
3. FormData creation with session context
4. POST to `/upload-async` endpoint
5. Immediate response with processing message
6. Background polling to `/upload-status` endpoint
7. Status updates until processing complete
8. Final response with agent state update

#### 5.2.3 Polling Mechanism
```typescript
// Poll for upload status every 1 second
const pollInterval = setInterval(async () => {
    const statusResponse = await fetch(`${API_URL}/upload-status?session_id=${sessionId}`);
    const statusData = await statusResponse.json();
    
    if (statusData.status === 'completed') {
        clearInterval(pollInterval);
        // Update message and agent state
    }
}, 1000);
```

### 5.3 Agent Continuity System

#### 5.3.1 Context Propagation
```typescript
// Request payload includes agent state
const requestPayload = {
    user_message: input,
    session_id: sessionId,
    last_agent: agentState.last_agent,      // Previous agent context
    routine_number: agentState.routine_number // Workflow position (1-35)
};
```

#### 5.3.2 State Updates
Backend responses update frontend agent state:
```typescript
// Store agent state from backend response
storeAgentState(
    data.last_agent || null,
    data.routine_number || null
);
```

---

## 6. UI/UX Implementation

### 6.1 Design System

#### 6.1.1 Color Scheme
```css
:root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* Full HSL color palette defined */
}

.dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* Dark mode variants */
}
```

#### 6.1.2 Typography
- **Primary**: Geist Sans (modern, clean)
- **Monospace**: Geist Mono (for code)
- **Base Size**: 16px (prevents iOS zoom on input focus)
- **Responsive**: Tailwind typography plugin

### 6.2 Layout & Responsiveness

#### 6.2.1 Chat Layout
```css
/* Dynamic viewport height for mobile browsers */
.chat-container {
    height: calc(100dvh - 0px);
    display: flex;
    flex-direction: column;
}

/* Responsive message display */
.message-area {
    flex: 1;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch; /* iOS smooth scrolling */
}
```

#### 6.2.2 Mobile-First Design
- Auto-resizing textarea with `react-textarea-autosize`
- Touch-friendly button sizes (44px minimum)
- Safe area support for iPhone notch/dynamic island
- Sticky input area with glassmorphism effect
- iOS-specific input focus handling

### 6.3 Mobile Optimizations

#### 6.3.1 Viewport Configuration
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```
**Note**: Previously problematic `user-scalable=no` has been removed

#### 6.3.2 iOS Input Focus Handling
```typescript
// Prevent viewport jumping on iOS
const handleFocus = () => {
    if (isIOS) {
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
    }
};
```

#### 6.3.3 Safe Area Support
```css
.safe-area-bottom {
    padding-bottom: calc(env(safe-area-inset-bottom, 0) + 2.5rem);
}
```

### 6.4 Loading States & Feedback

#### 6.4.1 Response Timer
- Shows elapsed time with 0.1s precision
- Format: "00:00.0" (minutes:seconds.tenths)
- Stops when message completes

#### 6.4.2 Loading Indicators
- Pulsing cursor during typing simulation
- Disabled input during processing
- Processing spinner for background tasks

---

## 7. Backend Integration

### 7.1 Environment Configuration
```typescript
const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 
    (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
      ? 'http://localhost:8000'
      : 'https://d1ahgtos8kkd8y.cloudfront.net/api'),
  
  get UPLOAD_ASYNC_URL() {
    return `${this.API_BASE_URL}/upload-async`;
  },
  
  get UPLOAD_STATUS_URL() {
    return `${this.API_BASE_URL}/upload-status`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};
```

### 7.2 API Endpoints

#### 7.2.1 Chat Endpoint
```typescript
POST /chat
Content-Type: application/json

{
    "user_message": string,
    "session_id": string,
    "last_agent"?: string,
    "routine_number"?: number
}

Response: {
    "response": string,
    "last_agent"?: string,
    "routine_number"?: number
}
```

#### 7.2.2 Async Upload Endpoints
```typescript
// Initial upload
POST /upload-async
Content-Type: multipart/form-data

FormData:
- file: File
- session_id: string
- last_agent?: string
- routine_number?: string

Response: {
    "message": string,
    "session_id": string
}

// Status polling
GET /upload-status?session_id={session_id}

Response: {
    "status": "processing" | "completed" | "error",
    "response"?: string,
    "last_agent"?: string,
    "routine_number"?: number,
    "error"?: string
}
```

### 7.3 Error Handling
```typescript
// Comprehensive error handling with user feedback
try {
    const response = await fetch(endpoint, config);
    if (!response.ok) {
        const errorData = await response.text();
        throw new Error(errorData || `Request failed with status ${response.status}`);
    }
} catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    dispatch({ type: 'SET_ERROR', payload: { errorContent: errorMessage } });
}
```

---

## 8. Deployment Architecture

### 8.1 Build Process
```bash
# Production build with static export
npm run build

# Generates:
# - out/ directory with static HTML/CSS/JS
# - Optimized for CloudFront deployment
# - No server-side rendering required
```

### 8.2 CloudFront Integration
- **Distribution**: `d1ahgtos8kkd8y.cloudfront.net`
- **Origin**: S3 bucket with static build files
- **Path**: `/chat/*` routes to frontend
- **API**: `/api/*` routes to backend ALB

### 8.3 Docker Support
```dockerfile
# Multi-stage build for development
FROM node:20-slim AS base
# Note: Production uses static export, not Docker
```

---

## 9. Key Technical Decisions

### 9.1 Static Export
**Decision**: Use Next.js static export instead of server-side rendering  
**Rationale**: 
- Simplified deployment to CloudFront
- Better performance with CDN caching
- No server infrastructure needed
- Lower operational costs

### 9.2 Async Photo Upload
**Decision**: Polling-based status updates instead of WebSockets  
**Rationale**:
- Simpler infrastructure requirements
- Works well with CloudFront
- Adequate for photo processing use case
- Easier error recovery

### 9.3 Mobile-First Design
**Decision**: Optimize primarily for mobile devices  
**Rationale**:
- Most registrations happen on mobile
- Parents register kids on phones
- Touch-first interaction patterns
- Simplified responsive design

---

## 10. Current State & Known Issues

### 10.1 What's Working
- ✅ Complete registration flow (35 steps)
- ✅ Photo upload with HEIC support
- ✅ Agent state persistence
- ✅ Mobile optimizations (viewport issues fixed)
- ✅ Production deployment on CloudFront
- ✅ Typing simulation and loading states

### 10.2 Areas for Improvement
1. **Branding**: Still using default Next.js home page
2. **Dark Mode**: Implemented but not user-toggleable
3. **Accessibility**: Basic ARIA labels but could be enhanced
4. **Error Recovery**: Could improve retry mechanisms

---

## 11. Future Considerations

### 11.1 Immediate Priorities
1. **UTJFC Branding**: Update home page and metadata
2. **User Preferences**: Dark mode toggle
3. **Enhanced Error Messages**: More user-friendly error handling
4. **Analytics**: Add registration funnel tracking

### 11.2 Potential Enhancements
1. **Progressive Web App**: Offline support and installability
2. **Real-time Updates**: WebSocket for live admin responses
3. **Multi-language**: Support for non-English speakers
4. **Voice Input**: Speech-to-text for accessibility
5. **Registration Progress**: Visual progress indicator

### 11.3 Performance Optimizations
1. **Code Splitting**: Lazy load chat components
2. **Image Optimization**: Next.js image component usage
3. **Bundle Size**: Analyze and reduce JavaScript payload
4. **Caching Strategy**: Implement service worker caching

---

## 12. Development & Maintenance

### 12.1 Local Development
```bash
cd frontend/web
pnpm install
pnpm dev    # Runs on localhost:3000
```

### 12.2 Testing Approach
- Manual testing on real devices (iOS/Android)
- Focus on registration flow completion
- Photo upload verification
- Agent state persistence checks

### 12.3 Monitoring
- CloudFront access logs
- Client-side error tracking needed
- Performance metrics via Web Vitals
- User session analytics

---

## Conclusion

The UTJFC Registration Agent frontend is a production-ready, mobile-optimized chat interface that successfully handles complex multi-step registration workflows. Built with modern React and Next.js, it provides an excellent user experience while maintaining clean architecture and good performance characteristics.

**Status**: In production with minor enhancements needed  
**Architecture**: Clean, maintainable, and scalable  
**User Experience**: Smooth, responsive, and intuitive  
**Technical Debt**: Minimal - mainly configuration updates needed