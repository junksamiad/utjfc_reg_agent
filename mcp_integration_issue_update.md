# MCP Integration Issue - Updated Analysis for OpenAI Coding Agent

## Previous Diagnosis
You correctly identified that the session header round-trip might be the issue. However, our tests show the MCP server IS handling this correctly.

## New Test Results

### 1. Session Header Test ✅
```
1️⃣ Testing initialize (no session header):
   Status: 200
   Response headers:
   - Mcp-Session-Id: 24c2c2c9-69da-49ad-b1e8-49294d04a736
   ✅ Session ID returned in header

2️⃣ Testing tools/list WITHOUT session header:
   Status: 200
   ✅ Server accepted request without session header
   Response: {"jsonrpc": "2.0", "id": 2, "result": {"tools": [...]}}
```

The MCP server:
- Returns session ID in initialize response headers ✅
- Accepts subsequent requests WITHOUT session headers ✅
- Returns 200 with JSON (not 202/SSE) when no session header present ✅

### 2. Direct OpenAI API Tests

**Test 1: Simple "hello" (NO tool calls)**
```python
response = client.responses.create(
    model="gpt-4.1",
    input="Just say hello",
    tools=[{
        "type": "mcp",
        "server_label": "test",
        "server_url": "https://utjfc-mcp-server.replit.app/mcp",
        "require_approval": "never"
    }]
)
```
Result: ✅ Works! Returns "Hello! 👋 How can I help you today?"

**Test 2: With tool call**
```python
response = client.responses.create(
    model="gpt-4.1",
    input="Use the test_connection tool with message 'hello'",
    tools=[{
        "type": "mcp",
        "server_label": "utjfc_registration",
        "server_url": "https://utjfc-mcp-server.replit.app/mcp",
        "require_approval": "never",
        "allowed_tools": ["test_connection"]
    }]
)
```
Result: ❌ Hangs indefinitely

### 3. MCP Server Logs (when hanging)
```
INFO: Initialize request - assigned session ID: 2eaca6c6-839f-49a5-bb50-ee90f77fd18b
INFO: 104.154.113.146:0 - "POST /mcp HTTP/1.1" 200 OK
INFO: New SSE connection established
INFO: Sending SSE message: {"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
INFO: Tool called: test_connection with message "hello from backend test"
INFO: Immediate response returned
INFO: Queued response for SSE delivery
INFO: Sending SSE message: {"jsonrpc": "2.0", "id": 0, "result": {"content": [...]}}
```

## The Mystery

1. OpenAI successfully connects to the MCP server
2. MCP server sends responses via SSE
3. But OpenAI never acknowledges receiving the SSE messages
4. The Responses API call hangs until timeout

## Critical Observations

1. **Works without tool calls** - When the model just responds without calling MCP tools
2. **Hangs with ANY tool call** - Even a simple echo tool that returns immediately
3. **SSE messages are sent** - Server logs show messages being sent successfully
4. **No errors** - No error messages from either side

## Questions for OpenAI

1. **Is there a known issue with SSE delivery in the Responses API with MCP tools?**
   - The server is sending SSE messages but OpenAI doesn't seem to receive them

2. **Are there specific requirements for SSE implementation that aren't documented?**
   - Our SSE uses standard `data: {json}\n\n` format
   - 100ms polling interval
   - Proper connection handling

3. **Why does it work without tool calls but hang with tool calls?**
   - This suggests the issue is specifically with tool response handling

4. **Debug logging shows no output** - Setting `OPENAI_LOG=debug` produces no debug output when using Responses API with MCP. Is this expected?

## Our SSE Implementation
```python
async def sse_generator(connection_id: str):
    yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
    
    while connection_id in active_connections:
        if active_connections[connection_id].get("pending_messages"):
            message = active_connections[connection_id]["pending_messages"].pop(0)
            yield f"data: {json.dumps(message)}\n\n"
        await asyncio.sleep(0.1)  # 100ms polling
```

## What We Need Help With

The MCP server appears to be implementing the protocol correctly, but OpenAI's Responses API isn't receiving/processing the SSE messages when tools are called. Is there:

1. A specific SSE format requirement we're missing?
2. A header or configuration needed for SSE to work with tool responses?
3. A known issue or limitation with MCP tools in the current Responses API?
4. An alternative transport method we should use?

Any insights would be greatly appreciated. We're completely stuck at this point. 