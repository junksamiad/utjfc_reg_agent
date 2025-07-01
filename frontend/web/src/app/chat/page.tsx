"use client";

import React, { useReducer, useCallback, useRef, useEffect, useState, useMemo } from 'react';
import { cn } from '@/lib/utils'; // Import the cn utility
import ChatMessages from './_components/chat-messages'; // Renamed component
import ChatInput from './_components/chat-input';
import { ChevronDown, Home, RotateCcw } from 'lucide-react'; // Added RotateCcw Icon for scroll button and Home icon
// import { useTypingEffect } from '@/hooks/useTypingEffect'; // Remove hook import

// --- Helper function to generate and manage session ID ---
function generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('chat_session_id');
    if (!sessionId) {
        sessionId = generateSessionId();
        sessionStorage.setItem('chat_session_id', sessionId);
        console.log('Generated new session ID:', sessionId);
    } else {
        console.log('Using existing session ID:', sessionId);
    }
    return sessionId;
}

// --- Helper functions for agent state management ---
function storeAgentState(lastAgent: string | null, routineNumber: number | null): void {
    if (lastAgent !== null) {
        sessionStorage.setItem('last_agent', lastAgent);
        console.log('Stored last_agent:', lastAgent);
    }
    if (routineNumber !== null) {
        sessionStorage.setItem('routine_number', routineNumber.toString());
        console.log('Stored routine_number:', routineNumber);
    }
}

function getAgentState(): { last_agent: string | null; routine_number: number | null } {
    const lastAgent = sessionStorage.getItem('last_agent');
    const routineNumberStr = sessionStorage.getItem('routine_number');
    const routineNumber = routineNumberStr ? parseInt(routineNumberStr, 10) : null;
    
    console.log('Retrieved agent state:', { last_agent: lastAgent, routine_number: routineNumber });
    return {
        last_agent: lastAgent,
        routine_number: routineNumber
    };
}

function clearAgentState(): void {
    sessionStorage.removeItem('last_agent');
    sessionStorage.removeItem('routine_number');
    console.log('Cleared agent state');
}

// --- Interfaces (Revert Message interface) --- 
interface Message {
  id: string;
  role: 'user' | 'assistant'; 
  content: string; // Back to just content
  agentName?: string; 
  isLoading?: boolean;
  startTime?: number; // Add timestamp for when assistant message started
}

interface ChatMessageInput {
  role: string;
  content: string;
}

// --- Reducer Logic (Revert changes) --- 

interface ChatState {
    messages: { [id: string]: Message }; 
    messageOrder: string[];
    isLoading: boolean;
    loadingMessageId: string | null; 
    currentAssistantMessageId: string | null; 
}

type ChatAction =
    | { type: 'START_ASSISTANT_MESSAGE'; payload: { id: string; agentName?: string } }
    | { type: 'APPEND_DELTA'; payload: { id: string; delta: string } } // Back to APPEND_DELTA
    // | { type: 'UPDATE_DISPLAYED_CONTENT'; payload: { id: string; newContent: string } } // Remove this
    | { type: 'UPDATE_AGENT_NAME'; payload: { id: string; agentName: string } }
    | { type: 'COMPLETE_ASSISTANT_MESSAGE'; payload: { id: string } }
    | { type: 'ADD_USER_MESSAGE'; payload: Message }
    | { type: 'SET_ERROR'; payload: { errorContent: string } }
    | { type: 'RESET_CHAT' }; // Add reset action type

const initialState: ChatState = {
    messages: {},
    messageOrder: [],
    isLoading: false,
    loadingMessageId: null,
    currentAssistantMessageId: null,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
    switch (action.type) {
        case 'ADD_USER_MESSAGE':
             // Revert - just add the message as is
            return {
                ...state,
                isLoading: true, 
                messages: { ...state.messages, [action.payload.id]: action.payload },
                messageOrder: [...state.messageOrder, action.payload.id],
            };

        case 'START_ASSISTANT_MESSAGE':
            const newMessage: Message = {
                id: action.payload.id,
                role: 'assistant',
                content: '', // Start empty
                agentName: action.payload.agentName || 'Assistant',
                isLoading: true,
                startTime: Date.now(), // Add timestamp when assistant starts
            };
            return {
                ...state,
                isLoading: true, // Ensure global loading state is active
                currentAssistantMessageId: action.payload.id, 
                loadingMessageId: action.payload.id, 
                messages: { ...state.messages, [action.payload.id]: newMessage },
                messageOrder: [...state.messageOrder, action.payload.id],
            };

        case 'APPEND_DELTA': // Renamed back
            if (!state.messages[action.payload.id] || state.loadingMessageId !== action.payload.id) return state;
            const msgToAppend = state.messages[action.payload.id];
            return {
                ...state,
                messages: {
                    ...state.messages,
                    [action.payload.id]: {
                        ...msgToAppend,
                        content: msgToAppend.content + action.payload.delta, // Update content directly
                    }
                }
            };
        
        // case 'UPDATE_DISPLAYED_CONTENT': // Remove this case
        //     return state; // Or handle appropriately if needed elsewhere

        case 'UPDATE_AGENT_NAME':
             if (!state.messages[action.payload.id] || state.loadingMessageId !== action.payload.id) return state;
             const msgToUpdateAgent = state.messages[action.payload.id];
            return {
                ...state,
                messages: {
                    ...state.messages,
                    [action.payload.id]: {
                        ...msgToUpdateAgent,
                        agentName: action.payload.agentName,
                    }
                }
            };

        case 'COMPLETE_ASSISTANT_MESSAGE':
            if (state.loadingMessageId !== action.payload.id) return state;
            const completedMsg = state.messages[action.payload.id];
            const updatedMessages = completedMsg ? { 
                ...state.messages, 
                [action.payload.id]: { ...completedMsg, isLoading: false } // Just set isLoading false
            } : state.messages;
            
            return {
                ...state,
                messages: updatedMessages,
                isLoading: false, // Deactivate global loading state
                loadingMessageId: null,
                currentAssistantMessageId: null,
            };
        
        case 'SET_ERROR':
             const errorId = `error-${Date.now()}`;
             const errorMessage: Message = {
                 id: errorId,
                 role: 'assistant',
                 content: `Error: ${action.payload.errorContent}`, // Back to content
                 agentName: 'System Error'
             };
            return {
                ...state,
                isLoading: false,
                loadingMessageId: null,
                currentAssistantMessageId: null,
                messages: { ...state.messages, [errorId]: errorMessage },
                messageOrder: [...state.messageOrder, errorId],
            };

        case 'RESET_CHAT': // Add reset case
            console.log("Resetting chat state...");
            return initialState;

        default:
            return state;
    }
}

const TYPING_SPEED_MS = 2; // Milliseconds per chunk for simulated typing

const simulateTyping = (
    dispatch: React.Dispatch<ChatAction>,
    messageId: string,
    fullContent: string,
    agentName?: string
) => {
    // Add error handling for undefined or empty content
    if (!fullContent || typeof fullContent !== 'string') {
        console.error('simulateTyping: Invalid content provided:', fullContent);
        dispatch({ type: 'COMPLETE_ASSISTANT_MESSAGE', payload: { id: messageId } });
        return;
    }

    if (agentName) {
        dispatch({ type: 'UPDATE_AGENT_NAME', payload: { id: messageId, agentName } });
    }

    // Split content into small chunks (e.g., characters or words)
    // Splitting by character for a smoother, more granular typing effect
    const chunks = fullContent.split(''); 
    let currentChunkIndex = 0;

    function typeNextChunk() {
        if (currentChunkIndex < chunks.length) {
            const delta = chunks[currentChunkIndex];
            dispatch({ type: 'APPEND_DELTA', payload: { id: messageId, delta } });
            currentChunkIndex++;
            setTimeout(typeNextChunk, TYPING_SPEED_MS);
        } else {
            dispatch({ type: 'COMPLETE_ASSISTANT_MESSAGE', payload: { id: messageId } });
        }
    }
    typeNextChunk();
};

// --- Page Component --- 
export default function ChatPage() {
    const [state, dispatch] = useReducer(chatReducer, initialState);
    const { messages, messageOrder, isLoading, loadingMessageId } = state;
    const orderedMessages = useMemo(() => 
        messageOrder.map(id => messages[id]).filter(Boolean)
    , [messageOrder, messages]);
    const hasStarted = state.messageOrder.length > 0;

    // Ref for the scrollable message container
    const scrollRef = useRef<HTMLDivElement>(null);
    // State to track if scroll is at the very bottom
    const [isScrolledToVeryBottom, setIsScrolledToVeryBottom] = useState(true);
    // State to control visibility of scroll to bottom button
    const [showScrollDownButton, setShowScrollDownButton] = useState(false);
    const [chatInput, setChatInput] = useState(''); // Added for controlled ChatInput

    // Refs for scroll behavior management
    const userJustSentRef = useRef(false); 
    const lastUserSend = useRef<number>(0);

    // Helper to scroll a specific message to the top of the viewport, accounting for input area
    const scrollToMessageTop = useCallback((messageId: string) => {
        const messageElement = scrollRef.current?.querySelector(`[data-msg-id="${messageId}"]`);
        if (messageElement && scrollRef.current) {
            const container = scrollRef.current;
            const messageRect = messageElement.getBoundingClientRect();
            const containerRect = container.getBoundingClientRect();
            
            // Calculate how much space the input area takes up (approximately 200px including padding)
            const inputAreaHeight = 200;
            const availableHeight = containerRect.height - inputAreaHeight;
            
            // Position the message in the upper portion of available space
            const targetPosition = container.scrollTop + messageRect.top - containerRect.top - 40; // 40px from top
            
            container.scrollTo({
                top: Math.max(0, targetPosition),
                behavior: 'smooth'
            });
        }
    }, []); // scrollRef is stable

    const scrollToVeryBottom = useCallback(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    }, []);

    const handleScroll = useCallback(() => {
        const el = scrollRef.current;
        if (!el) {
            setShowScrollDownButton(false);
            setIsScrolledToVeryBottom(true);
            return;
        }
        const isAtAbsoluteBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 10; // Small threshold
        setIsScrolledToVeryBottom(isAtAbsoluteBottom);
        setShowScrollDownButton(!isAtAbsoluteBottom && el.scrollHeight > el.clientHeight); // Show if not at bottom AND scrollable
    }, []);

    // Scroll listener effect for the scroll-down button
    useEffect(() => {
        const el = scrollRef.current;
        if (!el) return;

        el.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll(); // Initial check

        return () => {
            el.removeEventListener('scroll', handleScroll);
        };
    }, [handleScroll]);

    // Add handler for resetting chat
    const handleReset = useCallback(() => {
        dispatch({ type: 'RESET_CHAT' });
        // Clear session storage to generate new session ID
        sessionStorage.removeItem('chat_session_id');
        // Clear agent state
        clearAgentState();
        console.log('Chat reset - session ID and agent state cleared');
    }, [dispatch]);

    const handleFileUpload = useCallback(async (file: File) => {
        console.log('File uploaded:', file.name, file.type, file.size);
        
        // Create a user message indicating file upload
        const fileMessage: Message = {
            id: `user-file-${Date.now()}`,
            role: 'user',
            content: `📎 Uploaded photo: ${file.name}`,
        };
        dispatch({ type: 'ADD_USER_MESSAGE', payload: fileMessage });

        const assistantMessageId = `assistant-${Date.now()}`;
        dispatch({ 
            type: 'START_ASSISTANT_MESSAGE', 
            payload: { id: assistantMessageId, agentName: 'Assistant' } 
        });

        // Scroll to bottom to show the new conversation
        setTimeout(() => {
            scrollToVeryBottom();
        }, 0);

        try {
            const sessionId = getOrCreateSessionId();
            const agentState = getAgentState();
            
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', sessionId);
            
            // Add agent state if available
            if (agentState.last_agent) {
                formData.append('last_agent', agentState.last_agent);
            }
            if (agentState.routine_number !== null) {
                formData.append('routine_number', agentState.routine_number.toString());
            }
            
            console.log('Uploading file with session ID:', sessionId);
            
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(errorData || `File upload failed with status ${response.status}`);
            }

            const data = await response.json();
            console.log('Received upload response:', data);
            
            // Store agent state from response
            storeAgentState(
                data.last_agent || null,
                data.routine_number || null
            );
            
            simulateTyping(dispatch, assistantMessageId, data.response, 'UTJFC Assistant');

        } catch (error) {
            console.error("Failed to upload file:", error);
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred during file upload";
            dispatch({ type: 'SET_ERROR', payload: { errorContent: errorMessage } });
        }
    }, [dispatch, scrollToVeryBottom]);

    const handleSendMessage = useCallback(async (currentInput: string) => {
        if (!currentInput.trim()) return;

        const userInput: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: currentInput,
        };
        dispatch({ type: 'ADD_USER_MESSAGE', payload: userInput });
        
        userJustSentRef.current = true;
        lastUserSend.current = Date.now();

        const assistantMessageId = `assistant-${Date.now()}`;
        dispatch({ 
            type: 'START_ASSISTANT_MESSAGE', 
            payload: { id: assistantMessageId, agentName: 'Assistant' } 
        });

        // Scroll to bottom to show the new conversation
        setTimeout(() => {
            scrollToVeryBottom();
        }, 0);

        try {
            const sessionId = getOrCreateSessionId();
            const agentState = getAgentState();
            
            // Build request payload with agent state
            const requestPayload: any = { 
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
            
            console.log('Sending request with payload:', requestPayload);
            
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPayload), 
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(errorData || `API request failed with status ${response.status}`);
            }

            const data = await response.json();
            console.log('Received response data:', data);
            
            // Store agent state from response
            storeAgentState(
                data.last_agent || null,
                data.routine_number || null
            );
            
            simulateTyping(dispatch, assistantMessageId, data.response, 'UTJFC Assistant');

        } catch (error) {
            console.error("Failed to send message to simple backend:", error);
            const errorMessage = error instanceof Error ? error.message : "An unknown error occurred with simple backend";
            dispatch({ type: 'SET_ERROR', payload: { errorContent: errorMessage } });
        }
    }, [dispatch, scrollToMessageTop]);

    // Effect for initial welcome message
    useEffect(() => {
        if (state.messageOrder.length === 0) {
            const welcomeMessageId = `assistant-welcome-${Date.now()}`;
            const welcomeText = "Welcome to Urmston Town Juniors Football Club. What can I help you with today?";
            
            dispatch({ 
                type: 'START_ASSISTANT_MESSAGE', 
                payload: { id: welcomeMessageId, agentName: 'AI Assistant' } 
            });
            
            simulateTyping(dispatch, welcomeMessageId, welcomeText, 'AI Assistant');
            // Scroll to bottom to show the welcome message
            setTimeout(() => scrollToVeryBottom(), 0);
        }
    }, [dispatch, scrollToVeryBottom, state.messageOrder.length]);

    return (
        <div className="flex flex-col h-[calc(100dvh-0px)] bg-white dark:bg-gray-900">
            {/* Header */}
            <header className="sticky top-0 z-10 flex items-center justify-between p-3 bg-white dark:bg-gray-800 h-[60px]">
                {/* <h1 className="text-xl font-semibold text-gray-800 dark:text-white">AI Agent UI</h1> */}
                <div className="flex-grow"></div> 
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleReset}
                        className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-sm flex items-center gap-1.5"
                        aria-label="Clear chat"
                    >
                        <RotateCcw size={16}/>
                        Clear Chat
                    </button>
                    <a
                        href="/" 
                        className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-sm flex items-center gap-1.5"
                        aria-label="Go to Home"
                    >
                        <Home size={16}/>
                        Home
                    </a>
                </div>
            </header>

            {/* Message Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto py-4 bg-gray-50 dark:bg-gray-850 scroll-smooth" 
                onScroll={handleScroll}
            >
                <div className="mx-auto max-w-3xl px-4 pb-80"> {/* Added pb-80 (320px) for maximum bottom padding to push content higher up the page */}
                    <ChatMessages messages={orderedMessages} loadingMessageId={loadingMessageId} />
                </div>
            </div>
            
            {/* Scroll to very bottom button */}
            {showScrollDownButton && (
                 <button
                    onClick={scrollToVeryBottom}
                    className="fixed bottom-32 left-1/2 -translate-x-1/2 z-20 p-2 bg-gray-700 dark:bg-gray-200 text-white dark:text-black rounded-full shadow-lg hover:bg-gray-800 dark:hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-600 dark:focus:ring-gray-400 transition-opacity duration-300"
                    aria-label="Scroll to bottom"
                 >
                     <ChevronDown size={20} />
                 </button>
            )}

            {/* Input Area - This outer div will be sticky */}
            <div className="sticky bottom-0 z-10 p-8 bg-gray-50 dark:bg-gray-850" data-sticky-input>
                 <ChatInput
                    onSendMessage={handleSendMessage}
                    onFileUpload={handleFileUpload}
                    onReset={handleReset}
                    isLoading={isLoading}
                    sticky={false} 
                />
            </div>
        </div>
    );
} 