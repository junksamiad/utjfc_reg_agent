# backend/tools/airtable/airtable_tool_definition.py
# OpenAI function tool definition for the main agent to call airtable operations

from .airtable_agent import execute_airtable_request

# Tool definition for OpenAI Responses API
AIRTABLE_DATABASE_OPERATION_TOOL = {
    "type": "function",
    "name": "airtable_database_operation",
    "description": """Execute CRUD operations on UTJFC registration database with automatic data validation and normalization.
    
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
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "season": {
                "type": "string",
                "enum": ["2526", "2425"],
                "description": "Season identifier (2526 = 2025-26, 2425 = 2024-25)"
            },
            "query": {
                "type": "string", 
                "description": """Natural language description of the database operation to perform.
                
                Examples:
                - "Create registration for Seb Charlton, age u10s, tigers team, parent John Charlton"
                - "Find all players with medical issues"
                - "Update Stefan Hayton's team to Eagles"
                - "Show all U12 players"
                - "Delete registration for duplicate entry"
                
                Include all relevant data in the query - the tool will validate and normalize it."""
            }
        },
        "required": ["season", "query"]
    }
}

# Function that gets called when the tool is invoked
def handle_airtable_tool_call(season: str, query: str) -> str:
    """
    Handle the airtable tool call from the main agent
    Returns a JSON string that can be parsed by the main agent
    """
    result = execute_airtable_request(season, query)
    
    # Convert the result to a JSON string for the main agent
    import json
    return json.dumps(result, indent=2) 