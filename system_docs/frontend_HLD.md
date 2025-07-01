# UTJFC Conversational Agent Frontend - High-Level Design (HLD)

## Document Overview
**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Complete technical documentation for the UTJFC conversational agent frontend system  
**Scope**: Frontend architecture, implementation details, and development context  

---

## 1. System Overview

### 1.1 Purpose
The frontend provides an interactive chat interface for Urmston Town Juniors Football Club (UTJFC) members to interact with an AI-powered conversational agent system. The system handles football club registration, inquiries, and various administrative tasks through natural language conversations.

### 1.2 Core Objectives
- **Conversational Interface**: Natural chat experience with typing simulation
- **Agent Continuity**: Maintain conversation context across multiple agent handoffs
- **File Upload Support**: Handle photo uploads for registration processes
- **Session Management**: Persistent sessions with state tracking
- **Responsive Design**: Mobile-first approach for accessibility
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
- **Output**: Standalone (Docker-ready)
- **Styling**: PostCSS with Tailwind CSS 4.0
- **Development**: Turbopack enabled for fast refresh
- **TypeScript**: Strict mode with Next.js integration

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
├── src/lib/
│   └── utils.ts             # Utility functions (cn helper)
└── public/                  # Static assets including UTJFC logo
```

### 3.2 Routing Architecture
- **App Router**: Next.js 13+ pattern with file-based routing
- **Routes**:
  - `/` - Home page (not customized for UTJFC yet)
  - `/chat` - Main conversational interface

### 3.3 Component Hierarchy
```
RootLayout
├── Home Page ("/")
└── Chat Page ("/chat")
    ├── Header (navigation & controls)
    ├── ChatMessages (message display)
    ├── ChatInput (input & file upload)
    └── ScrollControls (auto-scroll management)
```

---

## 4. State Management Architecture

### 4.1 State Management Pattern
**Primary Pattern**: `useReducer` with TypeScript for complex chat state management

### 4.2 Chat State Structure
```typescript
interface ChatState {
    messages: { [id: string]: Message };     // Keyed message storage
    messageOrder: string[];                  // Maintains message sequence
    isLoading: boolean;                      // Global loading state
    loadingMessageId: string | null;         // Tracks which message is loading
    currentAssistantMessageId: string | null; // Current assistant response
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentName?: string;                      // Which agent is responding
    isLoading?: boolean;                     // Message-level loading state
    startTime?: number;                      // Timestamp for response timing
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
    | { type: 'RESET_CHAT' };
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

### 5.2 File Upload System

#### 5.2.1 Supported Formats
```typescript
const allowedTypes = [
    'image/png',
    'image/jpeg', 
    'image/jpg',
    'image/webp',
    'image/heic'
];
const maxSize = 10 * 1024 * 1024; // 10MB limit
```

#### 5.2.2 Upload Flow
1. File selection via hidden input
2. Client-side validation (type, size)
3. FormData creation with session context
4. POST to `/upload` endpoint
5. Response handling with agent state update

### 5.3 Agent Continuity System

#### 5.3.1 Context Propagation
```typescript
// Request payload includes agent state
const requestPayload = {
    user_message: input,
    session_id: sessionId,
    last_agent: agentState.last_agent,      // Previous agent context
    routine_number: agentState.routine_number // Workflow position
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
- **Responsive**: Tailwind typography plugin

### 6.2 Layout & Responsiveness

#### 6.2.1 Chat Layout
```css
/* Full viewport height with fixed header and input */
.chat-container {
    height: calc(100dvh - 0px);
    display: flex;
    flex-direction: column;
}

/* Responsive message display */
.message-area {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 320px; /* Space for input area */
}
```

#### 6.2.2 Mobile-First Design
- Auto-resizing textarea with `react-textarea-autosize`
- Touch-friendly button sizes (44px minimum)
- Optimized spacing for mobile keyboards
- Sticky input area with glassmorphism effect

### 6.3 Interaction Patterns

#### 6.3.1 Scroll Management
```typescript
// Smart auto-scroll behavior
const [isScrolledToVeryBottom, setIsScrolledToVeryBottom] = useState(true);
const [showScrollDownButton, setShowScrollDownButton] = useState(false);

// Auto-scroll on new messages
// Manual scroll-to-bottom button when needed
// Threshold-based detection (10px tolerance)
```

#### 6.3.2 Loading States
- **Global loading**: Prevents multiple concurrent requests
- **Message loading**: Individual message loading indicators
- **Response timing**: Real-time timer showing response duration
- **Typing indicator**: Pulsing cursor during message streaming

---

## 7. Backend Integration

### 7.1 API Endpoints

#### 7.1.1 Chat Endpoint
```typescript
POST http://localhost:8000/chat
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

#### 7.1.2 Upload Endpoint
```typescript
POST http://localhost:8000/upload
Content-Type: multipart/form-data

FormData:
- file: File
- session_id: string
- last_agent?: string
- routine_number?: string

Response: {
    "response": string,
    "last_agent"?: string,
    "routine_number"?: number
}
```

### 7.2 Error Handling
```typescript
// Comprehensive error handling
try {
    const response = await fetch(endpoint, config);
    if (!response.ok) {
        const errorData = await response.text();
        throw new Error(errorData || `Request failed with status ${response.status}`);
    }
    // Handle successful response
} catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    dispatch({ type: 'SET_ERROR', payload: { errorContent: errorMessage } });
}
```

---

## 8. Development Workflow

### 8.1 Local Development
```bash
# Frontend development server
cd frontend/web
pnpm dev    # Runs on localhost:3000 with Turbopack
```

### 8.2 Build & Deployment

#### 8.2.1 Docker Configuration
```dockerfile
# Multi-stage build optimized for production
FROM node:20-slim AS base
# Dependencies, build, and runtime stages
# Standalone output for efficient containers
```

#### 8.2.2 Environment Configuration
```typescript
// Backend URL configuration needed
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Currently hardcoded - should be environment variable
// Different URLs for development, Docker, and production
```

---

## 9. Key Technical Decisions

### 9.1 State Management Choice
**Decision**: `useReducer` over useState or external state management  
**Rationale**: 
- Complex state with multiple interdependent values
- Predictable state transitions for chat flow
- Better debugging with action-based updates
- TypeScript integration for type safety

### 9.2 Typing Simulation
**Decision**: Client-side character-by-character streaming  
**Rationale**:
- Improved perceived performance
- Better UX with immediate feedback
- Reduced server complexity
- Consistent timing regardless of network conditions

### 9.3 Session Management
**Decision**: sessionStorage over localStorage  
**Rationale**:
- Session-scoped persistence (clears on tab close)
- Appropriate for chat conversations
- Reduces storage accumulation
- Better privacy (temporary storage)

---

## 10. Future Considerations

### 10.1 Immediate Improvements Needed
1. **Branding**: Update metadata and home page for UTJFC
2. **Environment Variables**: Configure API URLs properly
3. **Error Boundaries**: Add React Error Boundaries
4. **Accessibility**: Enhanced ARIA labels and keyboard navigation

### 10.2 Potential Enhancements
1. **Offline Support**: Service worker for basic offline functionality
2. **Push Notifications**: Real-time updates for admin responses
3. **Theme Customization**: UTJFC brand colors and styling
4. **Analytics**: User interaction tracking
5. **Performance**: Virtual scrolling for large conversations

### 10.3 Scalability Considerations
1. **State Optimization**: Consider virtual scrolling for message lists
2. **Memory Management**: Clean up old messages in long conversations
3. **Caching**: Implement response caching for common queries
4. **CDN**: Static asset optimization for production

---

## 11. Troubleshooting & Common Issues

### 11.1 Development Issues
- **CORS**: Backend must handle CORS for localhost:3000
- **Session Loss**: Check sessionStorage persistence
- **Typing Delays**: Adjust TYPING_SPEED_MS constant

### 11.2 Production Considerations
- **API URL**: Ensure NEXT_PUBLIC_API_URL is set correctly
- **File Upload Limits**: Coordinate with backend file size limits
- **Error Handling**: Implement proper error boundaries

---

## 12. Code Quality & Standards

### 12.1 TypeScript Usage
- Strict mode enabled
- Full type coverage for components and state
- Interface definitions for all data structures
- Proper error type handling

### 12.2 React Best Practices
- Functional components with hooks
- useCallback for performance optimization
- Proper dependency arrays in useEffect
- Clean component separation

### 12.3 Accessibility
- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Screen reader compatibility

---

## Conclusion

The frontend represents a production-ready conversational interface with sophisticated state management, real-time interactions, and comprehensive feature set. The architecture supports complex agent workflows while maintaining excellent user experience through modern React patterns and responsive design.

**Status**: Production-ready with minor branding updates needed  
**Maintainability**: High - clean architecture with good separation of concerns  
**Scalability**: Good - patterns support growth and feature additions  
**User Experience**: Excellent - modern chat interface with professional polish 