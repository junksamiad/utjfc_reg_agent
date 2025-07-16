from typing import Dict, Any
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')


def check_if_record_exists_in_db(**kwargs) -> Dict[str, Any]:
    """
    Search for existing registration record by player and parent names.
    
    This function searches the registrations_2526 table for existing records
    matching the provided player and parent names exactly. This is used to
    detect when a user who disconnected during registration is trying to resume.
    
    Args:
        player_full_name (str): Child's full name - MUST be properly capitalized
        parent_full_name (str): Parent's full name - MUST be properly capitalized
        
    Returns:
        dict: {
            "success": bool,
            "record_found": bool,
            "record": dict or None,
            "message": str
        }
    """
    
    try:
        # Extract and validate inputs
        player_full_name = kwargs.get('player_full_name', '').strip()
        parent_full_name = kwargs.get('parent_full_name', '').strip()
        
        if not player_full_name:
            return {
                "success": False,
                "record_found": False,
                "record": None,
                "message": "Player full name is required and must be properly capitalized"
            }
        
        if not parent_full_name:
            return {
                "success": False,
                "record_found": False,
                "record": None,
                "message": "Parent full name is required and must be properly capitalized"
            }
        
        # Check Airtable API key
        if not AIRTABLE_API_KEY:
            return {
                "success": False,
                "record_found": False,
                "record": None,
                "message": "Airtable API key not configured"
            }
        
        print(f"🔍 Searching for existing registration record...")
        print(f"   Player: '{player_full_name}'")
        print(f"   Parent: '{parent_full_name}'")
        
        # Query database for exact name matches using computed fields
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Build filter formula for exact matching on computed full name fields
        # These are computed fields that combine first + last names
        filter_formula = f"AND({{player_full_name}} = '{player_full_name}', {{parent_full_name}} = '{parent_full_name}')"
        
        print(f"   Filter: {filter_formula}")
        
        # Get matching records - limit to 1 since names should be unique per registration
        records = table.all(
            formula=filter_formula,
            max_records=1  # We only expect one match per unique name combination
        )
        
        if records:
            # Record found - extract the record data
            record = records[0]
            record_fields = record.get('fields', {})
            
            print(f"   ✅ Found matching record: {record['id']}")
            print(f"   Player: {record_fields.get('player_full_name', 'N/A')}")
            print(f"   Parent: {record_fields.get('parent_full_name', 'N/A')}")
            print(f"   Team: {record_fields.get('team', 'N/A')}")
            print(f"   Age Group: {record_fields.get('age_group', 'N/A')}")
            print(f"   Played Last Season: {record_fields.get('played_for_urmston_town_last_season', 'N/A')}")
            
            return {
                "success": True,
                "record_found": True,
                "record": record_fields,  # Return the full record fields
                "record_id": record['id'],  # Include the Airtable record ID
                "message": f"Found existing registration for {player_full_name} (parent: {parent_full_name})"
            }
        else:
            # No record found - this is a new user
            print(f"   ❌ No matching record found - this appears to be a new registration")
            
            return {
                "success": True,
                "record_found": False,
                "record": None,
                "message": f"No existing registration found for {player_full_name} - proceeding with new registration"
            }
            
    except Exception as e:
        print(f"❌ Error searching for existing record: {e}")
        return {
            "success": False,
            "record_found": False,
            "record": None,
            "message": f"Failed to search for existing registration: {str(e)}",
            "error_details": str(e)
        }