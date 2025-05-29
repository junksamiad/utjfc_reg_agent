# MCP Server Setup Guide for OpenAI Integration

This guide provides a complete walkthrough for setting up an MCP (Model Context Protocol) server that successfully integrates with OpenAI's Responses API. It includes all the critical lessons learned from troubleshooting connection issues.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Critical Requirements](#critical-requirements)
4. [Server Implementation](#server-implementation)
5. [Deployment on Replit](#deployment-on-replit)
6. [Testing & Verification](#testing--verification)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Integration with OpenAI](#integration-with-openai)

## Overview

MCP (Model Context Protocol) is a protocol that allows AI models to interact with external tools and services. When integrating with OpenAI's Responses API, the MCP server acts as a bridge between OpenAI and your tools.

### Key Components
- **MCP Server**: Implements JSON-RPC 2.0 protocol with SSE (Server-Sent Events) transport
- **OpenAI Responses API**: Uses MCP tools via the `tools` parameter
- **Backend Application**: Configures OpenAI to use the MCP server

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your Backend  │────▶│     OpenAI      │────▶│   MCP Server    │
│  (FastAPI/etc)  │     │  Responses API  │     │  (FastAPI+SSE)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                           │
                              │ 1. Initialize             │
                              │ 2. List Tools             │
                              │ 3. Call Tools             │
                              │ 4. Get Results via SSE   │
                              └───────────────────────────┘
```

## Critical Requirements

### 1. Protocol Implementation
- **JSON-RPC 2.0**: All requests/responses must follow JSON-RPC 2.0 format
- **SSE Transport**: Responses must be delivered via Server-Sent Events
- **Protocol Version**: Use `"2025-03-26"` for OpenAI compatibility

### 2. Header Requirements
- **Session Header**: Use `Mcp-Session-Id` (NOT `X-MCP-Session-Id`)
- **Case Sensitivity**: Headers are case-insensitive but use exact casing for clarity
- **Content Type**: Always `application/json` for POST requests

### 3. Response Format Requirements
- **Tools List**: Must return `{"result": {"tools": [...]}}` (wrapped array)
- **Session ID**: Initialize must return session ID in response headers
- **SSE Routing**: POST requests with session ID must return 202 and route via SSE

### 4. Timing Requirements
- **Polling Speed**: SSE generator must poll every 100ms (NOT 30 seconds)
- **Timeout**: OpenAI times out after 30 seconds - ensure fast responses

## Server Implementation

### Complete Server Code Structure

```python
#!/usr/bin/env python3
"""MCP Server for OpenAI Integration"""

import os
import json
import asyncio
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import AsyncGenerator, Optional, Dict, Any
import uuid

# Setup
app = FastAPI(title="MCP Server")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS - CRITICAL for OpenAI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.openai.com", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Storage for SSE connections
active_connections: Dict[str, Dict[str, Any]] = {}
session_to_connection: Dict[str, str] = {}
```

### Critical Endpoint Implementations

#### 1. Initialize Handler
```python
async def handle_jsonrpc_request(request_data: dict, request: Request) -> tuple[dict, dict]:
    """Handle JSON-RPC requests - returns (response, headers)"""
    method = request_data.get("method")
    request_id = request_data.get("id")
    
    if method == "initialize":
        # CRITICAL: Generate session ID
        session_id = str(uuid.uuid4())
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "Your MCP Server",
                    "version": "1.0.0"
                }
            }
        }
        
        # CRITICAL: Return session ID in headers
        headers = {"Mcp-Session-Id": session_id}
        return response, headers
```

#### 2. Tools List Handler
```python
    elif method == "tools/list":
        # CRITICAL: Wrap tools array in result object
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "your_tool_name",
                        "description": "Tool description",
                        "inputSchema": {
                            "type": "object",
                            "properties": {...},
                            "required": [...]
                        }
                    }
                ]
            }
        }, {}
```

#### 3. SSE Generator
```python
async def sse_generator(connection_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events - CRITICAL: Fast polling"""
    try:
        # Send connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'connectionId': connection_id})}\n\n"
        
        while connection_id in active_connections:
            if active_connections[connection_id].get("pending_messages"):
                message = active_connections[connection_id]["pending_messages"].pop(0)
                yield f"data: {json.dumps(message)}\n\n"
            
            # CRITICAL: 100ms polling for immediate delivery
            await asyncio.sleep(0.1)
    finally:
        # Cleanup
        if connection_id in active_connections:
            del active_connections[connection_id]
```

#### 4. POST Endpoint with SSE Routing
```python
@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    """Handle POST requests - CRITICAL: SSE routing logic"""
    body = await request.json()
    
    # CRITICAL: Check for correct header name
    session_id = request.headers.get("mcp-session-id")
    
    # Handle request
    response, headers = await handle_jsonrpc_request(body, request)
    
    # CRITICAL: Route via SSE if session exists
    if session_id and session_id in session_to_connection:
        connection_id = session_to_connection[session_id]
        if connection_id in active_connections:
            # Queue response for SSE delivery
            active_connections[connection_id]["pending_messages"].append(response)
            # Return 202 Accepted
            return Response(status_code=202, headers=headers)
    
    # No SSE session - return directly
    return JSONResponse(response, headers=headers)
```

#### 5. DELETE Endpoint for Connection Cleanup
```python
@app.delete("/mcp")
async def mcp_delete_endpoint(request: Request):
    """Handle DELETE requests for connection cleanup - CRITICAL for OpenAI"""
    # Check authentication if needed
    # if not check_auth(request):
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get session ID from headers
    session_id = request.headers.get("mcp-session-id")
    
    if session_id and session_id in session_to_connection:
        connection_id = session_to_connection[session_id]
        
        # Clean up the connection
        if connection_id in active_connections:
            del active_connections[connection_id]
        del session_to_connection[session_id]
        
        logger.info(f"Cleaned up connection for session: {session_id}")
        return Response(status_code=204)  # No Content
    
    # Session not found, but that's OK
    return Response(status_code=204)
```

@app.options("/mcp")
async def mcp_options():
    """Handle OPTIONS requests for CORS preflight"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, DELETE",
            "Access-Control-Max-Age": "86400",
        }
    )

## Deployment on Replit

### 1. File Structure
```
/
├── main.py          # Your MCP server code
├── requirements.txt # Dependencies
├── .env            # Environment variables (use Secrets in Replit)
└── tools/          # Your tool implementations
```

### 2. Requirements.txt
```txt
fastapi==0.115.12
uvicorn==0.34.2
python-dotenv==1.1.0
openai==1.81.0
pyairtable==3.1.1  # If using Airtable
httpx==0.28.1
pydantic==2.11.4
```

### 3. Environment Variables (Replit Secrets)
```bash
OPENAI_API_KEY=your_key_here
AIRTABLE_API_KEY=your_key_here  # If using Airtable
PORT=8080  # Replit uses this
HOST=0.0.0.0
```

### 4. Main Entry Point
```python
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    # CRITICAL: Use correct module name
    uvicorn.run("main:app", host=host, port=port, log_level="info", reload=False)
```

### 5. Replit Configuration
- **Run Command**: `python main.py`
- **Language**: Python 3.11+
- **Always On**: Enable for production use

## Testing & Verification

### 1. Direct JSON-RPC Test
```python
import requests

# Test initialize
response = requests.post(
    "https://your-server.replit.app/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
)
print(f"Status: {response.status_code}")
print(f"Session ID: {response.headers.get('Mcp-Session-Id')}")
```

### 2. SSE Routing Test
```python
# Test with session ID
session_id = "test-123"

# Start SSE listener
sse_response = requests.get(
    "https://your-server.replit.app/mcp",
    headers={
        "Accept": "text/event-stream",
        "Mcp-Session-Id": session_id
    },
    stream=True
)

# Send request with same session ID
post_response = requests.post(
    "https://your-server.replit.app/mcp",
    json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    headers={"Mcp-Session-Id": session_id}
)

# Should get 202 status
assert post_response.status_code == 202
```

### 3. OpenAI Integration Test
```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    input=[{"role": "user", "content": "Test"}],
    tools=[{
        "type": "mcp",
        "server_label": "my_server",
        "server_url": "https://your-server.replit.app/mcp",
        "require_approval": "never"
    }]
)
```

## Common Issues & Solutions

### Issue 1: OpenAI Timeout (30 seconds)
**Symptom**: OpenAI connection times out without response
**Causes & Solutions**:
- ❌ Slow polling (30s) → ✅ Use 100ms polling
- ❌ Wrong header name → ✅ Use `Mcp-Session-Id`
- ❌ Missing SSE routing → ✅ Return 202 for requests with session
- ❌ ID mismatch in responses → ✅ Echo exact request ID in response

### Issue 2: Protocol Errors
**Symptom**: OpenAI reports protocol errors
**Causes & Solutions**:
- ❌ Bare tools array → ✅ Wrap in `{"result": {"tools": [...]}}`
- ❌ Missing session ID → ✅ Return in initialize headers
- ❌ Wrong protocol version → ✅ Use `"2025-03-26"`
- ❌ Hardcoded response IDs → ✅ Always use request ID from incoming request

### Issue 3: Authentication Issues
**Symptom**: OpenAI can't authenticate
**Solution**: Remove custom auth headers - OpenAI can't pass them

### Issue 4: CORS Errors
**Symptom**: Browser/OpenAI CORS errors
**Solution**: Ensure CORS middleware allows `https://api.openai.com`

### Issue 5: Deployment Issues
**Symptom**: Server doesn't start on Replit
**Causes & Solutions**:
- ❌ Wrong module name in uvicorn → ✅ Match filename
- ❌ Missing HOST env var → ✅ Default to "0.0.0.0"
- ❌ Python vs python3 → ✅ Use `python` on Replit

### Issue 6: DELETE Method Not Allowed (405)
**Symptom**: Logs show "DELETE /mcp HTTP/1.1" 405 Method Not Allowed
**Cause**: OpenAI sends DELETE requests to clean up connections
**Solution**: Implement DELETE endpoint handler and include in CORS allowed methods

### Issue 7: JSON-RPC ID Handling
**Symptom**: OpenAI might hang if response IDs don't match request IDs
**Cause**: Server returns wrong ID in JSON-RPC response
**Solution**: Always echo the exact `id` from the request in your response:
```python
request_id = request_data.get("id")  # Could be number, string, or null
# ... process request ...
response = {
    "jsonrpc": "2.0",
    "id": request_id,  # Use exact same ID
    "result": {...}
}
```

## Integration with OpenAI

### Backend Configuration
```python
# In your backend agents.py
class Agent(BaseModel):
    use_mcp: bool = True
    mcp_server_url: str = "https://your-server.replit.app/mcp"
    
    def get_tools_for_openai(self):
        if self.use_mcp:
            return [{
                "type": "mcp",
                "server_label": "your_label",
                "server_url": self.mcp_server_url,
                "require_approval": "never",
                "allowed_tools": self.tools
            }]
```

### Using with Responses API
```python
# In your backend responses.py
response = client.responses.create(
    model="gpt-4.1",
    input=messages,
    tools=agent.get_tools_for_openai()
)
```

### Environment Configuration

#### Backend .env File - CRITICAL SETUP

Your backend needs a `.env` file with the following configuration:

```bash
# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Tool-Specific Configuration (REQUIRED for your tools)
# Example: Airtable
AIRTABLE_API_KEY=patxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# MCP Server Configuration (REQUIRED for MCP mode)
# ⚠️ CRITICAL: Must include the full URL with /mcp endpoint!
MCP_SERVER_URL=https://your-mcp-server.replit.app/mcp  # ← Note the /mcp at the end!
# ❌ WRONG: https://your-mcp-server.replit.app
# ✅ CORRECT: https://your-mcp-server.replit.app/mcp

# Enable/Disable MCP Mode
USE_MCP=true  # Set to 'false' to use local function calling instead

# Server Configuration
PORT=8000     # Backend server port
HOST=0.0.0.0  # Listen on all interfaces
```

#### Common .env Mistakes to Avoid:

1. **Missing `/mcp` endpoint**:
   ```bash
   # ❌ WRONG - Missing endpoint
   MCP_SERVER_URL=https://utjfc-mcp-server.replit.app
   
   # ✅ CORRECT - Includes /mcp endpoint
   MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
   ```

2. **Using localhost for deployed MCP server**:
   ```bash
   # ❌ WRONG - Points to local server
   MCP_SERVER_URL=http://localhost:8002/mcp
   
   # ✅ CORRECT - Points to deployed server
   MCP_SERVER_URL=https://your-mcp-server.replit.app/mcp
   ```

3. **Missing API keys**:
   - Without `OPENAI_API_KEY`: Backend can't call OpenAI
   - Without tool keys (e.g., `AIRTABLE_API_KEY`): MCP server can't execute tools

#### Verifying Your Configuration:

1. **Check backend is using correct MCP URL**:
   ```bash
   curl http://localhost:8000/agent/status
   ```
   Should show:
   ```json
   {
     "current_agent": {
       "use_mcp": true,
       "mcp_server_url": "https://your-mcp-server.replit.app/mcp"
     }
   }
   ```

2. **Test MCP server is accessible**:
   ```bash
   curl https://your-mcp-server.replit.app/health
   ```

3. **If backend shows wrong URL**, restart it after fixing .env:
   ```bash
   cd backend && python server.py
   ```

### Complete Integration Flow

1. **User Query** → Frontend sends to backend `/chat` endpoint
2. **Backend Processing**:
   ```python
   # Backend receives message
   # Uses MCP-configured agent
   # Calls OpenAI Responses API with MCP tool configuration
   ```
3. **OpenAI → MCP Server**:
   - Establishes SSE connection
   - Sends initialize request
   - Lists available tools
   - Calls specific tool with parameters
4. **MCP Server Processing**:
   - Receives tool call
   - Uses Responses API with code interpreter (if needed)
   - Executes actual tool operation (e.g., Airtable query)
   - Returns results via SSE stream
5. **Response Flow**:
   - MCP Server → OpenAI (via SSE)
   - OpenAI → Backend (formatted response)
   - Backend → Frontend (chat response)

## Tool Implementation with Responses API

### Critical Requirements for Code Interpreter Tools

When implementing tools that use OpenAI's Responses API with code interpreter:

#### 1. Tool Definition Format
```python
# CRITICAL: Must include container specification
tools = [{
    "type": "code_interpreter",
    "container": {"type": "auto"}  # Required for Responses API
}]
```

#### 2. Response Extraction
```python
# WRONG - Chat Completions format
if hasattr(response, 'choices'):
    content = response.choices[0].message.content

# CORRECT - Responses API format
if hasattr(response, 'output') and response.output:
    for output in response.output:
        if output.type == 'message':
            for content in output.content:
                if hasattr(content, 'text'):
                    extracted_text = content.text
```

#### 3. Complete Airtable Tool Example
```python
def execute_airtable_request(season: str, query: str) -> dict:
    """Execute Airtable operations using Responses API"""
    client = OpenAI()
    
    # CRITICAL: Use client.responses.create, NOT client.chat.completions.create
    response = client.responses.create(
        model="gpt-4o",
        input=[{
            "role": "user", 
            "content": f"Parse this request: {query}"
        }],
        tools=[{
            "type": "code_interpreter",
            "container": {"type": "auto"}  # Required!
        }],
        temperature=1.0
    )
    
    # Extract operation plan from response.output
    # (See response extraction pattern above)
```

### Common Tool Implementation Errors

1. **Missing Container Specification**
   - Error: `"Missing required parameter: 'tools[0].container'"`
   - Fix: Add `"container": {"type": "auto"}` to tool definition

2. **Wrong API Method**
   - Error: `"Missing required parameter: 'tools[0].function'"`
   - Cause: Using `chat.completions.create` instead of `responses.create`
   - Fix: Use `client.responses.create()` for code interpreter

3. **Wrong Response Format**
   - Error: `AttributeError: 'Response' object has no attribute 'choices'`
   - Cause: Trying to access Chat Completions format on Responses API
   - Fix: Use `response.output` instead of `response.choices`

## Best Practices

1. **Logging**: Add comprehensive logging for debugging
2. **Error Handling**: Return proper JSON-RPC error responses
3. **Health Checks**: Implement `/health` endpoint
4. **Testing**: Test each component independently
5. **Monitoring**: Monitor SSE connections and cleanup
6. **Security**: Use environment variables for secrets
7. **Documentation**: Document your tools clearly
8. **API Keys**: Ensure both OPENAI_API_KEY and tool-specific keys (e.g., AIRTABLE_API_KEY) are set
9. **Response Parsing**: Always check response structure before accessing nested properties

## Conclusion

Setting up an MCP server for OpenAI requires careful attention to:
- Exact protocol implementation
- Correct header names and formats
- Fast SSE polling
- Proper response routing
- Correct Responses API usage for code interpreter tools
- Proper tool definition format with container specification

Following this guide should help you avoid the common pitfalls and get a working MCP server on the first try. 