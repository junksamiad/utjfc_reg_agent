# MCP Integration Issue - Complete Summary for OpenAI Coding Agent

## Overview
We have successfully deployed an MCP (Model Context Protocol) server on Replit that provides Airtable database tools. The MCP server works perfectly when tested directly, but when our backend tries to use it via OpenAI's Responses API with MCP tools, the backend hangs indefinitely.

## Architecture
1. **Frontend** (Next.js) → Running locally on port 3000
2. **Backend** (FastAPI) → Running locally on port 8000
3. **MCP Server** (FastAPI with SSE) → Deployed on Replit at https://utjfc-mcp-server.replit.app
4. **OpenAI API** → Using Responses API with MCP tools

## What's Working ✅
1. **MCP Server is healthy and responsive**:
   - Health check: `GET /health` returns 200 OK
   - Tools list: `POST /mcp` with `tools/list` returns correct tool definitions
   - Direct tool calls work perfectly (tested with 10.6s response time)
   - SSE (Server-Sent Events) delivery works correctly

2. **Backend configuration is correct**:
   ```
   USE_MCP=true
   MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
   Agent: UTJFC Registration Assistant (MCP)
   Model: gpt-4.1
   ```

3. **Direct MCP server test succeeds**:
   - Initialize → Get session ID → Start SSE → Call tool → Receive response via SSE
   - Complete flow works in ~10 seconds

## What's Not Working ❌
When the backend calls OpenAI's Responses API with MCP tools configured, it hangs indefinitely (times out after 60 seconds).

## Backend Code (responses.py)
```python
# Simplified version of the problematic code
def chat_loop_1(agent: Agent, input_messages: list):
    api_params = {
        "model": agent.model,  # "gpt-4.1"
        "input": input_conversation
    }
    
    # Add MCP tools configuration
    if agent.use_mcp:
        api_params["tools"] = [{
            "type": "mcp",
            "server_label": "utjfc_registration",
            "server_url": agent.mcp_server_url,  # https://utjfc-mcp-server.replit.app/mcp
            "require_approval": "never",
            "allowed_tools": ["airtable_database_operation"]
        }]
    
    # This call hangs indefinitely
    response = client.responses.create(**api_params)
    return response
```

## Test Results
1. **Backend test** (`test_backend_mcp_flow.py`):
   ```
   1️⃣ Checking backend status:
      ✅ Backend running
      Agent: UTJFC Registration Assistant (MCP)
      MCP enabled: True
      MCP URL: https://utjfc-mcp-server.replit.app/mcp
   
   3️⃣ Sending test message:
      Message: How many players are registered for season 2526?
      
      ❌ Request timed out after 60.00s
      The backend is hanging when processing the MCP response
   ```

2. **Direct MCP test** (`test_mcp_server_direct.py`):
   ```
   ✅ All steps succeed
   - Initialize: 200 OK, got session ID
   - SSE connection established
   - Tool call accepted: 202
   - Response received via SSE in ~10 seconds
   ```

## MCP Server Implementation Details
- Uses FastAPI with SSE support
- Implements JSON-RPC 2.0 protocol
- Correct headers: `Mcp-Session-Id` (not `X-MCP-Session-Id`)
- Tools list wrapped correctly: `{"result": {"tools": [...]}}`
- SSE polling at 100ms intervals
- Timeout handling with 20-second limits

## Question for OpenAI Coding Agent
Why does the OpenAI Responses API hang when trying to connect to our MCP server, even though:
1. The MCP server works perfectly when tested directly
2. The backend is configured correctly with the right URL and model
3. The MCP server implements all the required protocols correctly

Is there something specific about how the Responses API connects to MCP servers that we're missing? Are there any known issues or additional requirements when using MCP tools with the Responses API?

## Additional Context
- Using `gpt-4.1` model (as shown in OpenAI docs)
- MCP server has enhanced logging but shows no connection attempts from OpenAI
- Backend uses `openai` Python SDK (latest version)
- No authentication on MCP server (to simplify debugging)

Any insights or debugging suggestions would be greatly appreciated! 