import re
import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration for team_info table
TEAM_INFO_BASE_ID = "appBLxf3qmGIBc6ue"
TEAM_INFO_TABLE_ID = "tbl1ZCkcikNsLSw66"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def parse_registration_code(message: str):
    """
    Parse and validate registration code format.
    Returns None if not a valid registration code.
    
    Expected format: [PREFIX]-[TEAM]-[AGE_GROUP]-[SEASON][-PLAYER_NAME (only for re-registration)]
    - PREFIX: 100 (existing player) or 200 (new player)
    - TEAM: Team name (case-insensitive)
    - AGE_GROUP: U followed by number (case-insensitive)
    - SEASON: Must be 2526 (current season)
    - PLAYER_NAME: FirstName-Surname (required for 100 codes only)
    """
    # Regex pattern for registration codes (case-insensitive)
    pattern = r'^(100|200)-([A-Za-z0-9_]+)-([Uu]\d+)-(2526)(?:-([A-Za-z]+)-([A-Za-z]+))?$'
    
    match = re.match(pattern, message.strip(), re.IGNORECASE)
    if not match:
        return None
    
    prefix = match.group(1)
    team = match.group(2).lower()  # Normalize to lowercase
    age_group = match.group(3).lower()  # Normalize to lowercase (u9, u10, etc.)
    season = match.group(4)  # Must be 2526
    first_name = match.group(5).lower() if match.group(5) else None
    surname = match.group(6).lower() if match.group(6) else None
    
    # Validation: 100 codes must have player name, 200 codes must not
    if prefix == "100" and (not first_name or not surname):
        return None
    if prefix == "200" and (first_name or surname):
        return None
    
    # Season validation - only current season allowed
    if season != "2526":
        return None
    
    return {
        "prefix": prefix,
        "team": team,
        "age_group": age_group,
        "season": season,
        "player_name": f"{first_name} {surname}" if first_name and surname else None,
        "raw_code": message.strip()
    }

def validate_team_and_age_group(team: str, age_group: str) -> bool:
    """
    Validate that team exists for the specified age group in current season
    using the team_info table in Airtable.
    
    Args:
        team: Team name (normalized to lowercase)
        age_group: Age group (normalized to lowercase, e.g. 'u9', 'u10')
        
    Returns:
        bool: True if team/age group combination is valid, False otherwise
    """
    try:
        if not AIRTABLE_API_KEY:
            print("Error: AIRTABLE_API_KEY not found in environment variables")
            return False
        
        # Initialize Airtable client
        api = Api(AIRTABLE_API_KEY)
        table = api.table(TEAM_INFO_BASE_ID, TEAM_INFO_TABLE_ID)
        
        # Normalize team name for comparison (capitalize first letter)
        team_normalized = team.capitalize()
        
        # Normalize age group for comparison (ensure 'u' is lowercase and add 's' suffix for table format)
        age_group_normalized = age_group.lower() + 's'  # u10 -> u10s, u12 -> u12s
        
        print(f"Validating team: '{team_normalized}' for age group: '{age_group_normalized}'")
        
        # Query the team_info table
        # Using field names: short_team_name, age_group, current_season
        formula = f"AND({{short_team_name}} = '{team_normalized}', {{age_group}} = '{age_group_normalized}', {{current_season}} = '2526')"
        
        print(f"Airtable query formula: {formula}")
        
        # Execute the query
        records = table.all(formula=formula)
        
        print(f"Found {len(records)} matching records")
        
        # Return True if we found at least one matching record
        return len(records) > 0
        
    except Exception as e:
        print(f"Error validating team and age group: {e}")
        import traceback
        traceback.print_exc()
        return False

def lookup_player_details(player_name: str, team: str, age_group: str) -> dict:
    """
    Mock function to look up existing player details for re-registration.
    
    Args:
        player_name: Full player name from registration code
        team: Team name (normalized)
        age_group: Age group (normalized)
        
    Returns:
        dict: Player details if found, None if not found
        
    TODO: Replace with actual Airtable player lookup
    """
    print(f"Looking up player: '{player_name}' in team: '{team}' age group: '{age_group}'")
    
    # Mock data - always return Jack Grealish for now
    mock_player = {
        "player_name": "Jack Grealish",
        "team": "Tigers",
        "age_group": "u13s",
        "found": True,
        "player_id": "mock_player_123"  # Would be actual Airtable record ID
    }
    
    print(f"Mock player lookup result: {mock_player}")
    return mock_player

def validate_and_route_registration(message: str) -> dict:
    """
    Complete validation and routing flow for registration codes.
    
    Args:
        message: User input message
        
    Returns:
        dict: Validation result with routing information
    """
    # Step 1: Parse the registration code
    registration_code = parse_registration_code(message)
    if not registration_code:
        return {
            "valid": False,
            "error": "Invalid registration code format",
            "route": None
        }
    
    print(f"Parsed registration code: {registration_code}")
    
    # Step 2: Validate team and age group against Airtable
    is_valid_team = validate_team_and_age_group(
        registration_code["team"], 
        registration_code["age_group"]
    )
    
    if not is_valid_team:
        return {
            "valid": False,
            "error": "Invalid team/age group combination",
            "route": None
        }
    
    # Step 3: For re-registration codes (100), look up player details
    player_details = None
    if registration_code["prefix"] == "100":
        player_details = lookup_player_details(
            registration_code["player_name"],
            registration_code["team"],
            registration_code["age_group"]
        )
        
        # In a real implementation, we would check if player was found
        # For now, mock always returns a player
        if not player_details or not player_details.get("found"):
            return {
                "valid": False,
                "error": "Player not found in database",
                "route": None
            }
    
    # Step 4: Determine routing
    route = route_registration_request(registration_code)
    
    return {
        "valid": True,
        "route": route,
        "registration_code": registration_code,
        "player_details": player_details,
        "error": None
    }

def route_registration_request(registration_code: dict) -> str:
    """
    Determine which registration flow to use based on the code prefix.
    
    Args:
        registration_code: Parsed registration code dictionary
        
    Returns:
        str: "re_registration" for 100 codes, "new_registration" for 200 codes
    """
    if registration_code["prefix"] == "100":
        return "re_registration"
    elif registration_code["prefix"] == "200":
        return "new_registration"
    else:
        raise ValueError(f"Invalid registration prefix: {registration_code['prefix']}") 