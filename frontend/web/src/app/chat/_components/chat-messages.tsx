import React, { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Clipboard } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    agentName?: string;
    isLoading?: boolean;
    startTime?: number; // Add timestamp for when assistant message started
}

interface MessageListProps {
    messages: Message[];
    loadingMessageId: string | null;
}

// Flag to toggle avatar rendering
const AVATAR_ON = true; // Set to false to hide avatars

// Component for the loading timer
const LoadingTimer: React.FC<{ startTime: number }> = ({ startTime }) => {
    const [seconds, setSeconds] = useState(0);

    useEffect(() => {
        const updateTimer = () => {
            const elapsed = (Date.now() - startTime) / 1000; // Keep as decimal
            setSeconds(elapsed);
        };

        // Update immediately
        updateTimer();

        // Update every 100ms for smooth millisecond display
        const interval = setInterval(updateTimer, 100);

        return () => clearInterval(interval);
    }, [startTime]);

    return (
        <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
            ({seconds.toFixed(1)}s)
        </span>
    );
};

const MessageList: React.FC<MessageListProps> = ({ messages, loadingMessageId }) => {

    const copyToClipboard = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            console.log("Copied to clipboard!");
        } catch (err) {
            console.error("Failed to copy text: ", err);
        }
    };

    return (
        <div className="flex-1 space-y-4">
            {messages.map((msg) => (
                <React.Fragment key={msg.id}>
                    {msg.role === 'user' ? (
                        <div className="flex justify-end" data-msg-id={msg.id}>
                            <div
                                className={cn(
                                    "rounded-2xl sm:rounded-3xl p-3 sm:p-4 prose prose-sm dark:prose-invert break-words max-w-[85%] sm:max-w-[75%] shadow-sm",
                                    'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                                )}
                            >
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {msg.content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-start gap-2 sm:gap-3" data-msg-id={msg.id} key={`assist-grp-${msg.id}`}> 
                            {AVATAR_ON && (
                                <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-full overflow-hidden flex-shrink-0 mt-1">
                                    <Image src="/logo.svg" alt="Avatar" width={40} height={40} />
                                </div>
                            )}
                            <div className="flex flex-col items-start min-w-0 flex-1">
                                <div
                                    className={cn(
                                        "rounded-lg sm:rounded-xl p-3 sm:p-4 prose prose-sm dark:prose-invert break-words max-w-full",
                                        'text-gray-900 dark:text-gray-100'
                                    )}
                                >
                                    {msg.isLoading && !msg.content ? (
                                        <div className="flex items-center">
                                            <span className="animate-pulse text-gray-500 dark:text-gray-400">
                                                Assistant working...
                                            </span>
                                            {msg.startTime && <LoadingTimer startTime={msg.startTime} />}
                                        </div>
                                    ) : (
                                        <>
                                            <ReactMarkdown 
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    a: ({ href, children, ...props }) => (
                                                        <a 
                                                            href={href} 
                                                            target="_blank" 
                                                            rel="noopener noreferrer"
                                                            {...props}
                                                        >
                                                            {children}
                                                        </a>
                                                    )
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                            {/* Pulsing cursor only shown when loading and content exists */}
                                            {loadingMessageId === msg.id && msg.content && <span className="animate-pulse animate-fade-in ml-1">▍</span>}
                                        </>
                                    )}
                                </div>
                                {!msg.isLoading && msg.content && (
                                    <button
                                        onClick={() => copyToClipboard(msg.content)}
                                        className="p-2 mt-1 sm:mt-2 pl-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md touch-manipulation"
                                        aria-label="Copy message"
                                        title="Copy message"
                                    >
                                        <Clipboard className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};

export default MessageList; 