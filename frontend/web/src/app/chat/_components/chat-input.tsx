import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ArrowUp, Plus, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import TextareaAutosize from 'react-textarea-autosize';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    onFileUpload: (file: File) => void;
    onReset: () => void;
    isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onFileUpload, onReset, isLoading }) => {
    const [input, setInput] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        // Delay focus to ensure viewport stability on mobile
        const timer = setTimeout(() => {
            textareaRef.current?.focus();
        }, 100);
        return () => clearTimeout(timer);
    }, []);

    useEffect(() => {
        if (!isLoading) {
            // Delay focus to ensure viewport stability on mobile
            const timer = setTimeout(() => {
                textareaRef.current?.focus();
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [isLoading]);

    const handleSend = useCallback(() => {
        if (input.trim() && !isLoading) {
            onSendMessage(input.trim());
            setInput('');
        }
    }, [input, isLoading, onSendMessage]);

    const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    }, [handleSend]);

    const handleFileSelect = useCallback(() => {
        fileInputRef.current?.click();
    }, []);

    const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please select a valid image file (PNG, JPEG, WebP, or HEIC)');
                return;
            }
            
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                alert('File size must be less than 10MB');
                return;
            }
            
            onFileUpload(file);
        }
        event.target.value = '';
    }, [onFileUpload]);

    // iOS-specific input focus/blur handlers to prevent layout issues
    const handleInputFocus = useCallback(() => {
        // Detect iOS devices
        if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
            // Prevent document scroll during input focus
            document.body.style.position = 'fixed';
            document.body.style.width = '100%';
            document.body.style.top = `-${window.scrollY}px`;
        }
    }, []);

    const handleInputBlur = useCallback(() => {
        // Detect iOS devices
        if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
            // Restore document scroll after input blur
            const scrollY = document.body.style.top;
            document.body.style.position = '';
            document.body.style.width = '';
            document.body.style.top = '';
            if (scrollY) {
                window.scrollTo(0, parseInt(scrollY || '0', 10) * -1);
            }
        }
    }, []);

    return (
        <form
            onSubmit={(e) => {
                e.preventDefault();
                handleSend();
            }}
            className="flex flex-col w-full max-w-full mx-auto gap-2 p-3 sm:p-4 border border-gray-300/50 dark:border-gray-600/50 rounded-2xl sm:rounded-3xl bg-white/80 dark:bg-gray-800/80 shadow-lg backdrop-blur-md overflow-hidden"
        >
            <TextareaAutosize
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder="Ask anything..."
                className="w-full resize-none overflow-y-auto max-h-60 rounded-lg bg-transparent border-0 px-2.5 focus:outline-none focus:ring-0 placeholder:text-gray-400 dark:placeholder:text-gray-500 text-gray-900 dark:text-gray-100 leading-6"
                style={{ fontSize: '16px' }}
                disabled={isLoading}
                cacheMeasurements 
            />
            <div className="flex justify-between items-center h-8">
                <div className="flex items-center gap-1"> 
                    <button
                        type="button"
                        onClick={handleFileSelect}
                        title="Upload photo"
                        className="p-2 mr-1 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-md disabled:opacity-50 touch-manipulation"
                        aria-label="Upload photo"
                        disabled={isLoading}
                    >
                        <Plus className="h-5 w-5" />
                    </button>
                    
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/webp,image/heic"
                        onChange={handleFileChange}
                        className="hidden"
                        aria-hidden="true"
                    />
                    <button
                        type="button"
                        onClick={onReset} 
                        title="Reset chat"
                        className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-md disabled:opacity-50 touch-manipulation"
                        aria-label="Reset chat"
                        disabled={isLoading} 
                    >
                        <RotateCcw className="h-5 w-5" />
                    </button>
                </div>

                <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className={cn(
                        "flex items-center justify-center h-8 w-8 rounded-full transition-opacity shrink-0 p-1.5",
                        !isLoading && input.trim() 
                            ? "bg-black dark:bg-white text-white dark:text-black hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black dark:focus:ring-white"
                            : "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400",
                        isLoading && "bg-white dark:bg-black text-black dark:text-white opacity-100 cursor-wait"
                    )}
                    aria-label="Send message"
                >
                    <ArrowUp size={18} /> 
                </button>
            </div>
        </form>
    );
};

export default ChatInput; 