'use client';

import { useState } from 'react';

// These implementations will be moved to the main chat page after testing
const fetchWithTimeout = async (url: string, options: RequestInit, timeoutMs: number = 28000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error: any) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - the server is taking longer than expected');
        }
        throw error;
    }
};

const fetchWithRetry = async (
    url: string,
    options: RequestInit,
    maxRetries: number = 3,
    initialDelay: number = 1000,
    onRetryUpdate?: (message: string) => void
) => {
    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetchWithTimeout(url, options, 28000);
            
            if (response.status === 504) {
                throw new Error('Gateway timeout - server processing took too long');
            }
            
            return response;
        } catch (error) {
            lastError = error as Error;
            
            if (
                attempt < maxRetries && 
                (lastError.message.includes('timeout') || lastError.message.includes('504'))
            ) {
                const retryMessage = `Apologies for the extended delay, it seems the AI servers are very busy at present. Please bear with me for a moment whilst I try again. (Attempt ${attempt + 2} of ${maxRetries + 1})`;
                
                if (onRetryUpdate) {
                    onRetryUpdate(retryMessage);
                }
                
                const delay = initialDelay * Math.pow(2, attempt);
                console.log(`[RETRY] Waiting ${delay}ms before attempt ${attempt + 2}`);
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
            }
            
            break;
        }
    }
    
    throw lastError!;
};

export default function TestTimeoutPage() {
    const [results, setResults] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [startTime, setStartTime] = useState<number | null>(null);
    const [elapsedTime, setElapsedTime] = useState(0);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const addResult = (message: string) => {
        const timestamp = new Date().toLocaleTimeString();
        setResults(prev => [...prev, `[${timestamp}] ${message}`]);
    };

    const testScenario = async (scenario: string) => {
        setResults([]);
        setLoading(true);
        setStartTime(Date.now());
        setElapsedTime(0);

        // Update timer every 100ms
        const timerInterval = setInterval(() => {
            if (startTime) {
                setElapsedTime(Date.now() - startTime);
            }
        }, 100);

        addResult(`Starting test: ${scenario}`);

        try {
            const response = await fetchWithRetry(
                `${apiUrl}/test-timeout/${scenario}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: `test-${Date.now()}`,
                        user_message: 'Test message'
                    }),
                },
                3,
                1000,
                (retryMessage) => addResult(`RETRY: ${retryMessage}`)
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            addResult(`SUCCESS: ${data.response}`);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            
            if (errorMessage.includes('timeout')) {
                addResult(`FINAL ERROR: Apologies, but it seems there is too much traffic on the AI servers. Please could you try resubmitting your last response and hopefully we can process your request this time.`);
            } else {
                addResult(`ERROR: ${errorMessage}`);
            }
        } finally {
            clearInterval(timerInterval);
            setLoading(false);
            const totalTime = Date.now() - (startTime || Date.now());
            addResult(`Total time: ${(totalTime / 1000).toFixed(1)}s`);
        }
    };

    const formatElapsedTime = (ms: number) => {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-8">Timeout Retry Test Page</h1>
                
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4">Test Scenarios</h2>
                    
                    <div className="grid grid-cols-2 gap-4 mb-6">
                        <button
                            onClick={() => testScenario('normal')}
                            disabled={loading}
                            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                        >
                            Normal (Fast Response)
                        </button>
                        
                        <button
                            onClick={() => testScenario('always-timeout')}
                            disabled={loading}
                            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                        >
                            Always Timeout
                        </button>
                        
                        <button
                            onClick={() => testScenario('succeed-on-retry')}
                            disabled={loading}
                            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
                        >
                            Succeed on Retry
                        </button>
                        
                        <button
                            onClick={() => testScenario('flaky-success')}
                            disabled={loading}
                            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
                        >
                            Flaky (50/50 Success)
                        </button>
                    </div>

                    {loading && (
                        <div className="mb-4 p-4 bg-blue-50 rounded">
                            <div className="flex items-center justify-between">
                                <span className="font-semibold">Testing in progress...</span>
                                <span className="text-2xl font-mono">{formatElapsedTime(elapsedTime)}</span>
                            </div>
                            <div className="mt-2 text-sm text-gray-600">
                                Timeout will occur at 0:28 (28 seconds)
                            </div>
                        </div>
                    )}
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">Test Results</h2>
                    
                    <div className="bg-gray-100 rounded p-4 h-96 overflow-y-auto font-mono text-sm">
                        {results.length === 0 ? (
                            <div className="text-gray-500">Click a test scenario to see results...</div>
                        ) : (
                            results.map((result, index) => (
                                <div 
                                    key={index} 
                                    className={`mb-1 ${
                                        result.includes('ERROR') ? 'text-red-600' :
                                        result.includes('SUCCESS') ? 'text-green-600' :
                                        result.includes('RETRY') ? 'text-yellow-600' :
                                        'text-gray-800'
                                    }`}
                                >
                                    {result}
                                </div>
                            ))
                        )}
                    </div>
                    
                    <div className="mt-4 text-sm text-gray-600">
                        <p><strong>Expected behaviors:</strong></p>
                        <ul className="list-disc list-inside mt-2">
                            <li>Normal: Immediate success response</li>
                            <li>Always Timeout: 4 attempts (28s each), then final error</li>
                            <li>Succeed on Retry: Timeout once, then success on 2nd attempt</li>
                            <li>Flaky: Random success or timeout sequence</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}