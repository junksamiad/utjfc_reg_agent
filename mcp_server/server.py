#!/usr/bin/env python3
"""
UTJFC Registration MCP Server

A Model Context Protocol server that provides tools for managing
UTJFC player registrations through Airtable integration.
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

# Add CORS middleware - be more restrictive in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://api.openai.com", "*"],  # Allow OpenAI and others
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

# Optional authentication
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")

def check_auth(request: Request) -> bool:
    """Check if request is authorized"""
    if not MCP_AUTH_TOKEN:
        return True  # No auth configured
    
    # Check Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == MCP_AUTH_TOKEN
    
    # Check custom header (for OpenAI)
    custom_token = request.headers.get("x-mcp-auth-token", "")
    return custom_token == MCP_AUTH_TOKEN

async def handle_jsonrpc_request(request_data: dict) -> dict:
    """Handle JSON-RPC 2.0 requests"""
    jsonrpc = request_data.get("jsonrpc", "2.0")
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    try:
        if method == "initialize":
            # Handle initialization
            return {
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
        
        elif method == "tools/list":
            # Return list of available tools
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "result": {
                    "tools": [AIRTABLE_TOOL]
                }
            }
        
        elif method == "tools/call":
            # Execute tool call
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
                }
            
            # Execute the tool
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
                }
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return {
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution failed: {str(e)}"
                    }
                }
        
        else:
            # Method not found
            return {
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling JSON-RPC request: {e}")
        return {
            "jsonrpc": jsonrpc,
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

async def sse_generator(connection_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for a connection"""
    try:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        # Keep connection alive
        while connection_id in active_connections:
            # Check if there are any pending messages for this connection
            if active_connections[connection_id].get("pending_messages"):
                message = active_connections[connection_id]["pending_messages"].pop(0)
                yield f"data: {json.dumps(message)}\n\n"
            else:
                # Send keepalive
                await asyncio.sleep(30)
                if connection_id in active_connections:
                    yield ": keepalive\n\n"
    
    except asyncio.CancelledError:
        logger.info(f"SSE connection {connection_id} cancelled")
    finally:
        if connection_id in active_connections:
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
    # Check authentication
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    accept_header = request.headers.get("accept", "")
    
    if "text/event-stream" in accept_header:
        # Create new SSE connection
        connection_id = str(uuid.uuid4())
        active_connections[connection_id] = {
            "pending_messages": [],
            "created_at": asyncio.get_event_loop().time()
        }
        
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
        # Return 405 for non-SSE GET requests
        return Response(status_code=405)

@app.post("/mcp")
async def mcp_post_endpoint(request: Request):
    """Handle POST requests to MCP endpoint"""
    # Check authentication
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        # Check content type
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return JSONResponse(
                {"error": "Content-Type must be application/json"},
                status_code=400
            )
        
        # Parse request body
        body = await request.json()
        
        # Log request for debugging (remove in production)
        logger.info(f"MCP Request: {json.dumps(body, indent=2)}")
        
        # Handle single request or batch
        if isinstance(body, list):
            # Batch request
            responses = []
            for req in body:
                resp = await handle_jsonrpc_request(req)
                responses.append(resp)
            
            # Check if we should return SSE
            accept_header = request.headers.get("accept", "")
            if "text/event-stream" in accept_header and any(r.get("result") for r in responses):
                # Return SSE stream
                async def sse_response():
                    for resp in responses:
                        yield f"data: {json.dumps(resp)}\n\n"
                
                return StreamingResponse(
                    sse_response(),
                    media_type="text/event-stream",
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                    }
                )
            else:
                # Return JSON array
                return JSONResponse(responses)
        else:
            # Single request
            response = await handle_jsonrpc_request(body)
            
            # Check if this is just a notification/response (no result expected)
            if not body.get("id") or (body.get("method") and body["method"].startswith("notifications/")):
                return Response(status_code=202)  # Accepted
            
            # Check if we should return SSE
            accept_header = request.headers.get("accept", "")
            if "text/event-stream" in accept_header and response.get("result"):
                # Return SSE stream
                async def sse_response():
                    yield f"data: {json.dumps(response)}\n\n"
                
                return StreamingResponse(
                    sse_response(),
                    media_type="text/event-stream",
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                    }
                )
            else:
                # Return JSON response
                return JSONResponse(response)
    
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

# For Replit deployment
if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting UTJFC Registration MCP Server")
    print(f"🛠️  Tools available: airtable_database_operation")
    print(f"🌐 Streamable HTTP Transport (OpenAI Compatible)")
    print(f"📋 Protocol: MCP 2025-03-26")
    
    # Check if running on Replit
    if os.getenv("REPL_ID"):
        print(f"🔧 Running on Replit")
        host = "0.0.0.0"  # Replit requires this
        port = 8080  # Replit uses port 8080
    
    # Verify required environment variables
    required_vars = ["OPENAI_API_KEY", "AIRTABLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print(f"📝 Please set them in Replit Secrets")
    else:
        print(f"✅ Environment variables configured")
    
    # Check authentication
    if MCP_AUTH_TOKEN:
        print(f"🔐 Authentication enabled")
    else:
        print(f"⚠️  No authentication configured (set MCP_AUTH_TOKEN for security)")
    
    print(f"📍 Starting server on http://{host}:{port}")
    print(f"🔗 MCP endpoint: /mcp")
    print(f"❤️  Health check: /health")
    
    # Run the FastAPI server
    uvicorn.run(app, host=host, port=port, log_level="info") 