#!/usr/bin/env python3
"""
UTJFC Registration MCP Server - Fixed for OpenAI SSE Protocol v2

This version implements all fixes identified by the OpenAI agent:
1. Uses correct Mcp-Session-Id header (not X-MCP-Session-Id)
2. Returns wrapped tools array as per spec
3. Sends session ID in initialize response
4. Uses faster polling for immediate message delivery
"""

import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import AsyncGenerator, Optional, Dict, Any
import uuid

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our Airtable tool
from tools.airtable.airtable_agent import execute_airtable_request

# Create FastAPI app
app = FastAPI(title="UTJFC Registration MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.openai.com", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Tool definition
AIRTABLE_TOOL = {
    "name": "airtable_database_operation",
    "description": "Execute CRUD operations on UTJFC registration database with automatic data validation and normalization.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "season": {
                "type": "string",
                "description": "Season identifier (2526 = 2025-26, 2425 = 2024-25)",
                "enum": ["2526", "2425"]
            },
            "query": {
                "type": "string",
                "description": "Natural language description of the database operation to perform"
            }
        },
        "required": ["season", "query"]
    }
}

# Store active SSE connections
active_connections: Dict[str, Dict[str, Any]] = {}

# Map to track which SSE connection belongs to which session
session_to_connection: Dict[str, str] = {}

# Optional authentication
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

def check_auth(request: Request) -> bool:
    """Check if request is authorized"""
    if not MCP_AUTH_TOKEN:
        return True  # No auth configured
    
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == MCP_AUTH_TOKEN
    
    custom_token = request.headers.get("x-mcp-auth-token", "")
    return custom_token == MCP_AUTH_TOKEN

async def handle_jsonrpc_request(request_data: dict, request: Request) -> tuple[dict, dict]:
    """Handle JSON-RPC 2.0 requests and return (response, headers)"""
    jsonrpc = request_data.get("jsonrpc", "2.0")
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    # If no ID, it's a notification - don't process further
    if request_id is None:
        return None, {}
    
    try:
        if method == "initialize":
            # Generate a session ID for this client
            session_id = str(uuid.uuid4())
            
            response = {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "UTJFC Registration MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Return session ID in headers
            headers = {"Mcp-Session-Id": session_id}
            
            logger.info(f"Initialize request - assigned session ID: {session_id}")
            
            return response, headers
        
        elif method == "tools/list":
            # FIXED: Return wrapped array as per spec
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "result": {
                    "tools": [AIRTABLE_TOOL]  # Wrapped in object
                }
            }, {}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name != "airtable_database_operation":
                return {
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }, {}
            
            try:
                result = execute_airtable_request(
                    arguments.get("season"),
                    arguments.get("query")
                )
                
                return {
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }, {}
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return {
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }, {}
        
        else:
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, {}
    
    except Exception as e:
        logger.error(f"Error handling JSON-RPC request: {e}")
        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, {}

async def sse_generator(connection_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for a connection"""
    try:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'connectionId': connection_id})}\n\n"
        
        # Keep connection alive and send queued messages
        while connection_id in active_connections:
            # Check if there are any pending messages for this connection
            if active_connections[connection_id].get("pending_messages"):
                message = active_connections[connection_id]["pending_messages"].pop(0)
                yield f"data: {json.dumps(message)}\n\n"
            
            # FIXED: Use much shorter sleep for immediate delivery
            await asyncio.sleep(0.1)  # 100ms polling
    
    except asyncio.CancelledError:
        logger.info(f"SSE connection {connection_id} cancelled")
    finally:
        # Clean up connection
        if connection_id in active_connections:
            session_id = active_connections[connection_id].get("session_id")
            if session_id and session_id in session_to_connection:
                del session_to_connection[session_id]
            del active_connections[connection_id]

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return JSONResponse({
        "status": "healthy",
        "server": "UTJFC Registration MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        }
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "server": "UTJFC Registration MCP Server",
        "version": "1.0.0",
        "transport": "Streamable HTTP",
        "protocol": "MCP 2025-03-26",
        "environment": "production" if os.getenv("REPL_ID") else "development"
    })

@app.get("/mcp")
async def mcp_get_endpoint(request: Request):
    """Handle GET requests to MCP endpoint (SSE stream)"""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    accept_header = request.headers.get("accept", "")
    
    if "text/event-stream" in accept_header:
        # Create new SSE connection
        connection_id = str(uuid.uuid4())
        
        # FIXED: Check for correct header name (case-insensitive)
        session_id = request.headers.get("mcp-session-id", connection_id)
        
        active_connections[connection_id] = {
            "pending_messages": [],
            "created_at": asyncio.get_event_loop().time(),
            "session_id": session_id
        }
        
        # Map session to connection for message routing
        if session_id:
            session_to_connection[session_id] = connection_id
        
        logger.info(f"New SSE connection: {connection_id} for session: {session_id}")
        
        return StreamingResponse(
            sse_generator(connection_id),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
            }
        )
    else:
        return Response(status_code=405)

@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    """Handle POST requests to MCP endpoint"""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return JSONResponse(
                {"error": "Content-Type must be application/json"},
                status_code=400
            )
        
        body = await request.json()
        
        # Log request for debugging
        logger.info(f"MCP Request: {json.dumps(body, indent=2)}")
        
        # FIXED: Check for correct header name (case-insensitive)
        session_id = request.headers.get("mcp-session-id")
        
        # Handle single request or batch
        if isinstance(body, list):
            responses = []
            response_headers = {}
            
            for req in body:
                resp, headers = await handle_jsonrpc_request(req, request)
                if resp:  # Only add non-None responses
                    responses.append(resp)
                    response_headers.update(headers)
            
            # Route responses through SSE if session exists
            if session_id and session_id in session_to_connection:
                connection_id = session_to_connection[session_id]
                if connection_id in active_connections:
                    # Queue all responses for SSE delivery
                    for resp in responses:
                        active_connections[connection_id]["pending_messages"].append(resp)
                    return Response(status_code=202, headers=response_headers)
            
            # No SSE session, return responses directly
            return JSONResponse(responses, headers=response_headers)
        
        else:
            # Single request
            response, headers = await handle_jsonrpc_request(body, request)
            
            # If it's a notification (no response), return 202
            if response is None:
                return Response(status_code=202)
            
            # Route response through SSE if session exists
            if session_id and session_id in session_to_connection:
                connection_id = session_to_connection[session_id]
                if connection_id in active_connections:
                    # Queue response for SSE delivery
                    active_connections[connection_id]["pending_messages"].append(response)
                    logger.info(f"Queued response for SSE delivery to session {session_id}")
                    return Response(status_code=202, headers=headers)
            
            # No SSE session, return response directly
            return JSONResponse(response, headers=headers)
    
    except json.JSONDecodeError:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error handling POST request: {e}")
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            },
            status_code=500
        )

@app.options("/mcp")
async def mcp_options():
    """Handle OPTIONS requests for CORS preflight"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting UTJFC Registration MCP Server (Fixed v2)")
    print(f"🛠️  Tools available: airtable_database_operation")
    print(f"🌐 Streamable HTTP Transport with SSE Response Routing")
    print(f"📋 Protocol: MCP 2025-03-26")
    print(f"✨ Fixes: Correct headers, wrapped tools, fast polling")
    
    if os.getenv("REPL_ID"):
        print(f"🔧 Running on Replit")
    
    required_vars = ["OPENAI_API_KEY", "AIRTABLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print(f"📝 Please set them in Replit Secrets")
    else:
        print(f"✅ Environment variables configured")
    
    if MCP_AUTH_TOKEN:
        print(f"🔐 Authentication enabled")
    else:
        print(f"⚠️  No authentication configured (set MCP_AUTH_TOKEN for security)")
    
    print(f"📍 Starting server on http://{host}:{port}")
    print(f"🔗 MCP endpoint: /mcp")
    print(f"❤️  Health check: /health")
    
    uvicorn.run("server:app", host=host, port=port, log_level="info", reload=False) 