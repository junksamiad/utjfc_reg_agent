#!/usr/bin/env python3
"""
UTJFC Registration MCP Server

A Model Context Protocol server that provides tools for managing
UTJFC player registrations through Airtable integration.
"""

import os
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Import our Airtable tool
from tools.airtable.airtable_agent import execute_airtable_request

# Create MCP server with HTTP transport
mcp = FastMCP("UTJFC Registration MCP Server")

@mcp.tool()
def airtable_database_operation(season: str, query: str) -> str:
    """
    Execute CRUD operations on UTJFC registration database with automatic data validation and normalization.
    
    This tool handles database operations while ensuring all data conforms to schema standards. It will:
    - Validate and normalize data according to table schema
    - Convert informal data formats to schema-compliant formats
    - Execute the database operation with clean data
    
    Data normalization examples:
    - Age groups: "u10s" → "U10", "under 12" → "U12"
    - Team names: "tigers" → "Tigers", "eagles" → "Eagles"  
    - Medical flags: "yes" → "Y", "no" → "N"
    - Names: Proper case formatting
    
    Use this tool for any database operation including:
    - CREATE: Add new player registrations
    - READ: Search and retrieve registration data
    - UPDATE: Modify existing registrations
    - DELETE: Remove registrations (use carefully)
    
    Args:
        season: Season identifier (2526 = 2025-26, 2425 = 2024-25)
        query: Natural language description of the database operation to perform
        
    Returns:
        JSON string containing the operation result
    """
    # Validate season parameter
    valid_seasons = ["2526", "2425"]
    if season not in valid_seasons:
        return json.dumps({
            "status": "error",
            "message": f"Invalid season '{season}'. Valid seasons: {valid_seasons}",
            "data": None
        }, indent=2)
    
    # Execute the Airtable operation using our existing agent
    try:
        result = execute_airtable_request(season, query)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error", 
            "message": f"MCP tool execution failed: {str(e)}",
            "data": None
        }, indent=2)

def main():
    """Main entry point for the MCP server"""
    # Get configuration from environment
    port = int(os.getenv("PORT", 8002))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting UTJFC Registration MCP Server")
    print(f"🛠️  Tools available: airtable_database_operation")
    print(f"🌐 Streamable HTTP Transport Mode")
    
    # Verify required environment variables
    required_vars = ["OPENAI_API_KEY", "AIRTABLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print(f"📝 Please create a .env file and fill in your values")
        return
    
    print(f"✅ Environment variables configured")
    print(f"📍 Starting server on http://{host}:{port}")
    print(f"🔗 MCP endpoint will be available at: http://{host}:{port}/mcp")
    
    # Run the server with Streamable HTTP transport
    # Note: Port and host configuration may need to be set via environment variables
    # or server configuration rather than run() parameters
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main() 