from typing import Dict, Any, List
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')


def check_shirt_number_availability(**kwargs) -> Dict[str, Any]:
    """
    Get all existing shirt numbers for a specific team and age group.
    
    Searches the registrations_2526 table for existing records matching the team 
    and age_group, then returns the shirt_number data for AI analysis.
    
    Args:
        team (str): Team name (e.g., "Tigers", "Eagles") - must be properly capitalized
        age_group (str): Age group in lowercase format u## (e.g., "u10", "u16")
        requested_shirt_number (int): Shirt number to check (1-49)
        
    Returns:
        dict: Result with all existing shirt numbers for AI to analyze availability
    """
    
    try:
        # Validate inputs
        team = kwargs.get('team', '').strip()
        age_group = kwargs.get('age_group', '').strip()
        requested_shirt_number = kwargs.get('requested_shirt_number')
        
        if not team:
            return {
                "success": False,
                "message": "Team name is required and must be properly capitalized (e.g., 'Tigers', 'Eagles')"
            }
        
        if not age_group or not age_group.lower().startswith('u'):
            return {
                "success": False,
                "message": "Age group is required and must be in format u## (e.g., 'u10', 'u16')"
            }
        
        # Normalize age_group to lowercase format
        age_group = age_group.lower()
        
        if not isinstance(requested_shirt_number, int) or not (1 <= requested_shirt_number <= 49):
            return {
                "success": False,
                "message": "Requested shirt number must be an integer between 1 and 49"
            }
        
        # Check Airtable API key
        if not AIRTABLE_API_KEY:
            return {
                "success": False,
                "message": "Airtable API key not configured"
            }
        
        # Query database for records matching team and age_group
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Build filter formula for Airtable
        filter_formula = f"AND({{team}} = '{team}', {{age_group}} = '{age_group}')"
        
        # Get all matching records, only fields we need
        records = table.all(
            formula=filter_formula,
            fields=['shirt_number', 'player_first_name', 'player_last_name', 'team', 'age_group']
        )
        
        # Extract all player records with shirt numbers for AI analysis
        players = []
        
        for record in records:
            fields = record.get('fields', {})
            player_data = {
                "player_name": f"{fields.get('player_first_name', '')} {fields.get('player_last_name', '')}".strip(),
                "shirt_number": fields.get('shirt_number'),
                "team": fields.get('team'),
                "age_group": fields.get('age_group')
            }
            players.append(player_data)
        
        result = {
            "success": True,
            "requested_number": requested_shirt_number,
            "team": team,
            "age_group": age_group,
            "players": players,
            "total_players_found": len(records),
            "message": f"Found {len(records)} players in {team} {age_group.upper()}. AI should analyze shirt_number field to determine availability of number {requested_shirt_number}."
        }
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get shirt number data: {str(e)}",
            "error_details": str(e)
        }


# Generate OpenAI function schema
def generate_shirt_number_check_schema():
    """Generate OpenAI function schema for shirt number availability checking."""
    return {
        "type": "function",
        "name": "check_shirt_number_availability",
        "description": """
        Get all existing shirt numbers for a specific team and age group.
        
        This function searches the registrations_2526 database for existing players
        in the same team and age group and returns all their shirt_number data.
        
        The AI should then analyze the returned 'players' array to determine:
        1. If the requested shirt number is already taken (check shirt_number field)
        2. Which player has that number if taken
        3. What alternative numbers are available (1-49 range)
        
        Use this function when a user requests a specific shirt number during registration.
        Extract the team and age_group from the conversation history - this information
        was injected when the registration code was validated at the start of the process.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "team": {
                    "type": "string",
                    "description": "Team name with proper capitalization (e.g., 'Tigers', 'Eagles', 'Leopards') - extract from conversation history"
                },
                "age_group": {
                    "type": "string", 
                    "pattern": "^u\\d{1,2}$",
                    "description": "Age group in lowercase format u## (e.g., 'u10', 'u16') - extract from conversation history and convert to lowercase"
                },
                "requested_shirt_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 49,
                    "description": "The shirt number the player wants (1-49)"
                }
            },
            "required": ["team", "age_group", "requested_shirt_number"]
        }
    }


# The tool definition for the registration agent
CHECK_SHIRT_NUMBER_AVAILABILITY_TOOL = generate_shirt_number_check_schema() 