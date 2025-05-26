#!/usr/bin/env python3
"""
Debug proxy to see what OpenAI is sending to our MCP server
"""

import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Target MCP server
TARGET_URL = "http://localhost:8002"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy(path: str, request: Request):
    """Proxy all requests and log them"""
    
    # Log incoming request
    logger.info(f"\n{'='*60}")
    logger.info(f"[{datetime.now().isoformat()}] Incoming Request")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: /{path}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Get body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        if body:
            try:
                body_json = json.loads(body)
                logger.info(f"Body (JSON): {json.dumps(body_json, indent=2)}")
            except:
                logger.info(f"Body (Raw): {body}")
    
    # Forward request to target
    async with httpx.AsyncClient() as client:
        try:
            # Build target URL
            target_url = f"{TARGET_URL}/{path}"
            
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']},
                content=body,
                params=dict(request.query_params)
            )
            
            # Log response
            logger.info(f"\nResponse from target:")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Headers: {dict(response.headers)}")
            
            # Handle streaming responses
            if "text/event-stream" in response.headers.get("content-type", ""):
                logger.info("Response is SSE stream")
                
                async def stream_response():
                    async for chunk in response.aiter_text():
                        logger.info(f"SSE Chunk: {chunk}")
                        yield chunk
                
                return StreamingResponse(
                    stream_response(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="text/event-stream"
                )
            else:
                # Regular response
                content = response.content
                try:
                    content_json = json.loads(content)
                    logger.info(f"Response Body (JSON): {json.dumps(content_json, indent=2)}")
                except:
                    logger.info(f"Response Body (Raw): {content}")
                
                return Response(
                    content=content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=500,
                media_type="application/json"
            )

if __name__ == "__main__":
    import uvicorn
    print("🔍 Starting Debug Proxy on port 8003")
    print("🎯 Proxying to: http://localhost:8002")
    print("📝 Use http://localhost:8003 instead of http://localhost:8002 to see all traffic")
    uvicorn.run(app, host="0.0.0.0", port=8003) 