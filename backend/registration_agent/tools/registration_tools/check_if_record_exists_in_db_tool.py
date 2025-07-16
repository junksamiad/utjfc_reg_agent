from typing import Dict, Any
from .check_if_record_exists_in_db import check_if_record_exists_in_db


def handle_check_if_record_exists_in_db(**kwargs) -> Dict[str, Any]:
    """
    Handler function for the check_if_record_exists_in_db tool.
    This wrapper follows the established pattern for tool handlers.
    
    Args:
        **kwargs: Arguments passed from the AI function call
        
    Returns:
        dict: Result from the core check_if_record_exists_in_db function
    """
    return check_if_record_exists_in_db(**kwargs)


def generate_check_record_exists_schema():
    """Generate OpenAI function schema for existing record checking."""
    return {
        "type": "function",
        "name": "check_if_record_exists_in_db",
        "description": """
        Search for existing registration record by player and parent names.
        
        This function searches the registrations_2526 database for existing records
        matching the provided names to determine if this is a returning user who
        accidentally disconnected during their registration process.
        
        CRITICAL: Ensure names are properly capitalized as they appear in the database.
        Extract the names from the conversation history where they were previously collected
        and validated during routines 1 and 2.
        
        Use this function in routine 2 when a valid registration code is provided to check
        if the user is resuming a previous registration attempt.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "player_full_name": {
                    "type": "string",
                    "description": "Child's full name with proper capitalization (e.g., 'John Smith') - extract from conversation history and ensure proper capitalization"
                },
                "parent_full_name": {
                    "type": "string", 
                    "description": "Parent's full name with proper capitalization (e.g., 'Sarah Smith') - extract from conversation history and ensure proper capitalization"
                },
            },
            "required": ["player_full_name", "parent_full_name"]
        }
    }


# The tool definition for the registration agent
CHECK_IF_RECORD_EXISTS_IN_DB_TOOL = generate_check_record_exists_schema()