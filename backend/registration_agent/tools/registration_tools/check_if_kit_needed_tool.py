# backend/registration_agent/tools/registration_tools/check_if_kit_needed_tool.py
# OpenAI function tool definition for checking if returning player's team needs new kit

import json
try:
    from .check_if_kit_needed import check_if_kit_needed
    print("🔧 DEBUG: Successfully imported check_if_kit_needed from relative import")
except ImportError:
    from check_if_kit_needed import check_if_kit_needed
    print("🔧 DEBUG: Imported check_if_kit_needed from absolute import (fallback)")


# Tool definition for OpenAI Responses API
CHECK_IF_KIT_NEEDED_TOOL = {
    "type": "function",
    "name": "check_if_kit_needed",
    "description": """Check if a returning player's team needs new kit this season.
    
    This tool queries the team_info database to determine whether a specific team 
    and age group combination requires new kit for the current season. It's used 
    in routine 30 to implement smart kit routing logic.
    
    The tool should be called when:
    - A returning player (played for Urmston Town last season) is registering
    - After SMS payment link confirmation in routine 30
    - To determine if they need kit selection (routine 32) or can skip to photo upload (routine 34)
    
    The agent should extract team and age group information from the conversation history
    where this data was injected as system messages when the registration code was validated.
    
    Returns whether new kit is required ('Y') or not required ('N') for routing decisions.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "team_name": {
                "type": "string",
                "description": "Team name with proper capitalization (e.g., 'Tigers', 'Eagles', 'Leopards') - extract from conversation history and ensure first letter is capitalized"
            },
            "age_group": {
                "type": "string",
                "pattern": "^u\\d{1,2}s$",
                "description": "Age group in format u##s (e.g., 'u10s', 'u16s') - extract from conversation history, convert to lowercase, and add 's' suffix"
            }
        },
        "required": ["team_name", "age_group"]
    }
}


def handle_check_if_kit_needed(**kwargs) -> str:
    """
    Handle the check_if_kit_needed tool call from agents.
    
    This function checks if a returning player's team needs new kit this season
    by querying the team_info table in Airtable.
    
    Args:
        **kwargs: Tool call parameters including:
            - team_name (str): Team name with proper capitalization (e.g., 'Tigers')
            - age_group (str): Age group in format u##s (e.g., 'u10s')
        
    Returns:
        str: JSON string with kit requirement check results
    """
    try:
        # Extract parameters from kwargs
        team_name = kwargs.get('team_name', '')
        age_group = kwargs.get('age_group', '')
        
        print(f"🔧 DEBUG: check_if_kit_needed tool called")
        print(f"   team_name='{team_name}'")
        print(f"   age_group='{age_group}'")
        
        # Validate inputs
        if not team_name or not team_name.strip():
            error_result = {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name,
                "age_group": age_group,
                "message": "Team name is required and must be properly capitalized (e.g., 'Tigers', 'Eagles')",
                "usage_note": "Missing required team name - extract this from conversation history where it was injected as a system message"
            }
            return json.dumps(error_result, indent=2)
        
        if not age_group or not age_group.strip():
            error_result = {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name,
                "age_group": age_group,
                "message": "Age group is required and must be in format u##s (e.g., 'u10s', 'u16s')",
                "usage_note": "Missing required age group - extract from conversation history and add 's' suffix"
            }
            return json.dumps(error_result, indent=2)
        
        # Call the core function
        print(f"🔧 DEBUG: Calling check_if_kit_needed function")
        print(f"   Parameters: team_name='{team_name.strip()}', age_group='{age_group.strip()}'")
        
        result = check_if_kit_needed(
            team_name=team_name.strip(),
            age_group=age_group.strip()
        )
        
        print(f"🔧 DEBUG: check_if_kit_needed function completed")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Kit needed: {result.get('kit_needed', 'Unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        # Add usage guidance based on result
        if result.get("success"):
            kit_needed = result.get("kit_needed", "N")
            team = result.get("team_name", team_name)
            age = result.get("age_group", age_group)
            
            if kit_needed == "Y":
                result["usage_note"] = (
                    f"Kit IS required for {team} {age}. "
                    f"Route to kit selection (routine 32) to collect kit size and shirt number."
                )
            else:
                result["usage_note"] = (
                    f"Kit NOT required for {team} {age}. "
                    f"Skip kit selection and route directly to photo upload (routine 34)."
                )
        else:
            result["usage_note"] = (
                f"Kit check failed: {result.get('message', 'Unknown error')}. "
                f"Default to requiring kit selection for safety - route to routine 32."
            )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "success": False,
            "kit_needed": "N",
            "team_name": kwargs.get('team_name', ''),
            "age_group": kwargs.get('age_group', ''),
            "message": f"Tool error occurred: {str(e)}",
            "error_details": str(e),
            "usage_note": "Function call failed - default to requiring kit selection (routine 32) for safety"
        }
        print(f"❌ DEBUG: Tool error in handle_check_if_kit_needed: {str(e)}")
        return json.dumps(error_result, indent=2)