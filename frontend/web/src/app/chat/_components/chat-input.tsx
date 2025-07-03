import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ArrowUp, Plus, RotateCcw } from 'lucide-react'; // Added RotateCcw, REMOVED SendHorizonal
import { cn } from '@/lib/utils'; // Import cn
import TextareaAutosize from 'react-textarea-autosize'; // Import the library

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    onFileUpload: (file: File) => void; // Add file upload handler prop
    onReset: () => void; // Add reset handler prop
    isLoading: boolean;
    sticky: boolean; // Added sticky prop
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onFileUpload, onReset, isLoading, sticky }) => {
    const [input, setInput] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Keep a ref to the textarea so we can programmatically focus it
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-focus on mount
    useEffect(() => {
        textareaRef.current?.focus();
    }, []);

    // Re-focus whenever loading finishes (assistant response done)
    useEffect(() => {
        if (!isLoading) {
            textareaRef.current?.focus();
        }
    }, [isLoading]);

    const handleSend = useCallback(() => {
        if (input.trim() && !isLoading) {
            onSendMessage(input.trim());
            setInput('');
            // No need to manually reset height
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
            // Validate file type
            const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please select a valid image file (PNG, JPEG, WebP, or HEIC)');
                return;
            }
            
            // Validate file size (max 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                alert('File size must be less than 10MB');
                return;
            }
            
            onFileUpload(file);
        }
        // Reset the input so the same file can be selected again if needed
        event.target.value = '';
    }, [onFileUpload]);

    return (
         // When sticky, use positioning instead of background/border on the outer div
         // Add bottom padding/margin for the floating effect
        <div
            className={cn(
                "w-full transition-all",
                sticky 
                  ? "fixed bottom-4 left-0 right-0 pb-4 z-10" // Changed bottom-0 to bottom-4
                  : "mx-auto w-full max-w-4xl" // Keep centered when not sticky, full width on mobile
            )}
        >
             {/* Inner container: Use flex-col for vertical layout */}
            <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                 // Apply consistent styling here, center it within the sticky container
                 // Changed to flex-col
                 // Revert to semi-transparent background + blur
                className="mx-auto flex flex-col w-full max-w-4xl gap-2 p-3 sm:p-4 border border-gray-300/50 dark:border-gray-600/50 rounded-2xl sm:rounded-3xl bg-white/80 dark:bg-gray-800/80 shadow-lg backdrop-blur-md"
            >
                 {/* Row 1: Textarea */}
                 {/* Use TextareaAutosize component */}
                <TextareaAutosize
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask anything..."
                     // Remove flex-1 to prevent default vertical growth
                    className="w-full resize-none overflow-y-auto max-h-60 rounded-lg bg-transparent border-0 px-2.5 focus:outline-none focus:ring-0 placeholder:text-gray-400 dark:placeholder:text-gray-500 text-gray-900 dark:text-gray-100 text-sm leading-6"
                    disabled={isLoading}
                    // Add cacheMeasurements prop for potential performance boost
                    cacheMeasurements 
                />
                 {/* Row 2: Buttons - Ensure alignment */}
                 <div className="flex justify-between items-center h-8"> {/* Set height for alignment */}
                     {/* Left side buttons: Attach + Reset */}
                     <div className="flex items-center gap-1"> 
                        {/* File upload button */}
                        <button
                            type="button"
                            onClick={handleFileSelect}
                            title="Upload photo" // Tooltip
                            className="p-2 mr-1 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-md disabled:opacity-50 touch-manipulation" // Added mr-1
                            aria-label="Upload photo"
                            disabled={isLoading}
                        >
                            <Plus className="h-5 w-5" />
                        </button>
                        
                        {/* Hidden file input */}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/png,image/jpeg,image/jpg,image/webp,image/heic"
                            onChange={handleFileChange}
                            className="hidden"
                            aria-hidden="true"
                        />
                         {/* Add title attribute for tooltip */} 
                         <button
                            type="button"
                            onClick={onReset} 
                            title="Reset chat" // Tooltip
                            className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-md disabled:opacity-50 touch-manipulation"
                            aria-label="Reset chat"
                            disabled={isLoading} 
                         >
                             <RotateCcw className="h-5 w-5" />
                         </button>
                     </div>

                    {/* Send button - right side */}
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                         // Make round, adjust default colors, add inverted disabled/loading style
                        className={cn(
                           "flex items-center justify-center h-8 w-8 rounded-full transition-opacity shrink-0 p-1.5", // Base styles: round, size, etc.
                           !isLoading && input.trim() 
                             ? "bg-black dark:bg-white text-white dark:text-black hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black dark:focus:ring-white" // Enabled state
                             : "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400", // Disabled (empty input) state - removed cursor
                           isLoading && "bg-white dark:bg-black text-black dark:text-white opacity-100 cursor-wait" // Loading state (inverted colors)
                         )}
                        aria-label="Send message"
                    >
                        <ArrowUp size={18} /> 
                    </button>
                 </div>
            </form>
        </div>
    );
};

export default ChatInput; 