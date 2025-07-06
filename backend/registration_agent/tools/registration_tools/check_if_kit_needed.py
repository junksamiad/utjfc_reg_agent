# backend/registration_agent/tools/registration_tools/check_if_kit_needed.py
# Core function for checking if a returning player's team needs new kit this season

from typing import Dict, Any
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Airtable configuration for team_info table
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1ZCkcikNsLSw66"  # team_info table
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')


def check_if_kit_needed(team_name: str, age_group: str) -> Dict[str, Any]:
    """
    Check if a returning player's team needs new kit this season.
    
    Searches the team_info table for the specific team and age group combination
    and returns whether new kit is required for the current season.
    
    Args:
        team_name (str): Team name with proper capitalization (e.g., "Tigers", "Eagles")
        age_group (str): Age group in format u##s (e.g., "u10s", "u16s")
        
    Returns:
        dict: Result with kit requirement status:
            - success (bool): Whether the query was successful
            - kit_needed (str): 'Y' or 'N' indicating if new kit is required
            - team_name (str): The team name that was queried
            - age_group (str): The age group that was queried
            - message (str): Description of the result
    """
    
    try:
        # Validate inputs
        if not team_name or not team_name.strip():
            return {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name,
                "age_group": age_group,
                "message": "Team name is required and must be properly capitalized (e.g., 'Tigers', 'Eagles')"
            }
        
        if not age_group or not age_group.strip():
            return {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name,
                "age_group": age_group,
                "message": "Age group is required and must be in format u##s (e.g., 'u10s', 'u16s')"
            }
        
        # Normalize inputs
        team_name_clean = team_name.strip()
        age_group_clean = age_group.strip().lower()
        
        # Validate age group format (should be u##s)
        if not age_group_clean.startswith('u') or not age_group_clean.endswith('s'):
            return {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name_clean,
                "age_group": age_group_clean,
                "message": f"Age group must be in format u##s (e.g., 'u10s', 'u16s'), received: '{age_group_clean}'"
            }
        
        # Check Airtable API key
        if not AIRTABLE_API_KEY:
            return {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name_clean,
                "age_group": age_group_clean,
                "message": "Airtable API key not configured"
            }
        
        # Query team_info table
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Build filter formula for Airtable
        # Maps: team_name -> short_team_name, age_group -> age_group
        filter_formula = f"AND({{short_team_name}} = '{team_name_clean}', {{age_group}} = '{age_group_clean}')"
        
        print(f"🔍 Checking kit requirement for {team_name_clean} {age_group_clean}")
        print(f"📋 Airtable query: {filter_formula}")
        
        # Get matching records
        records = table.all(
            formula=filter_formula,
            fields=['short_team_name', 'age_group', 'need_new_kit_current_season']
        )
        
        print(f"📊 Found {len(records)} matching team/age group records")
        
        if len(records) == 0:
            return {
                "success": False,
                "kit_needed": "N",
                "team_name": team_name_clean,
                "age_group": age_group_clean,
                "message": f"No team found for {team_name_clean} {age_group_clean}. This combination may not exist in the current season."
            }
        
        # Extract kit requirement from first matching record
        record = records[0]
        fields = record.get('fields', {})
        kit_needed = fields.get('need_new_kit_current_season', 'N')
        
        # Validate kit_needed value
        if kit_needed not in ['Y', 'N']:
            kit_needed = 'N'  # Default to No if invalid value
        
        print(f"✅ Kit requirement result: {kit_needed} for {team_name_clean} {age_group_clean}")
        
        result = {
            "success": True,
            "kit_needed": kit_needed,
            "team_name": team_name_clean,
            "age_group": age_group_clean,
            "message": f"{'New kit required' if kit_needed == 'Y' else 'No new kit needed'} for {team_name_clean} {age_group_clean} this season"
        }
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to check kit requirement: {str(e)}"
        print(f"❌ Error checking kit requirement: {error_msg}")
        
        return {
            "success": False,
            "kit_needed": "N",
            "team_name": team_name,
            "age_group": age_group,
            "message": error_msg,
            "error_details": str(e)
        }