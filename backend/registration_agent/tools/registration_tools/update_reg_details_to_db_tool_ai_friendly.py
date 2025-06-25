from typing import Dict, Any
from .registration_data_models import RegistrationDataContract
from .pydantic_to_openai_schema import pydantic_to_openai_schema
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')


def update_reg_details_to_db_ai_friendly(**kwargs) -> Dict[str, Any]:
    """
    AI-friendly version where the AI extracts all individual fields from conversation.
    
    The AI sees all individual fields with descriptions and provides each piece of data
    directly, just like the old OpenAI function calling approach you prefer.
    
    This function:
    1. Receives all individual fields from the AI
    2. Validates them using our Pydantic model
    3. Writes to database with clean error handling
    
    Returns:
        dict: Result with success status, record ID, and registration summary
    """
    
    try:
        # Step 1: Validate all the AI-provided data using Pydantic
        # The AI has intelligently extracted each field from the conversation
        validated_data = RegistrationDataContract(**kwargs)
        
        # Step 2: Prepare data for Airtable
        airtable_data = _prepare_airtable_data(validated_data)
        
        # Step 3: Write to database
        if not AIRTABLE_API_KEY:
            return {
                "success": False,
                "message": "Airtable API key not configured",
                "record_id": None
            }
        
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        record = table.create(airtable_data)
        
        return {
            "success": True,
            "message": f"Registration data saved successfully for {validated_data.player_first_name} {validated_data.player_last_name}",
            "record_id": record["id"],
            "player_name": f"{validated_data.player_first_name} {validated_data.player_last_name}",
            "team": validated_data.team,
            "age_group": validated_data.age_group,
            "registration_status": validated_data.registration_status,
            "billing_request_id": validated_data.billing_request_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to save registration data: {str(e)}",
            "record_id": None,
            "validation_errors": getattr(e, 'errors', None) if hasattr(e, 'errors') else None
        }


def _prepare_airtable_data(validated_data: RegistrationDataContract) -> Dict[str, Any]:
    """
    Convert validated Pydantic model to Airtable-compatible dictionary.
    Excludes computed/formula fields that Airtable automatically calculates.
    Properly handles NULL vs empty string values for database optimization.
    """
    # Convert Pydantic model to dict, excluding unset fields
    data = validated_data.dict(exclude_unset=True)
    
    # Add timestamp for when data was written to DB
    data["initial_db_write_timestamp"] = datetime.now().isoformat()
    
    # Exclude computed/formula fields that Airtable automatically generates
    # These are fields that combine other fields or are auto-calculated
    computed_fields = {
        'player_full_name',  # Computed from player_first_name + player_last_name
        'parent_full_name',  # Computed from parent_first_name + parent_last_name
        # Note: removed original_registration_code as requested
    }
    
    # Clean data for Airtable:
    # 1. Remove None values (they become NULL in Airtable - good for indexing)
    # 2. Remove computed fields
    # 3. Convert empty strings to None for optional fields (better database practice)
    airtable_data = {}
    
    for k, v in data.items():
        # Skip computed fields
        if k in computed_fields:
            continue
            
        # Handle None values - exclude them (Airtable will store as NULL)
        if v is None:
            continue
            
        # Handle empty strings for optional fields - convert to None/NULL for better indexing
        if isinstance(v, str) and v.strip() == "":
            # For optional fields, empty strings should be NULL
            optional_fields = {
                'description_of_player_medical_issues', 'previous_team_name',
                'player_telephone', 'player_email',
                'player_post_code', 'player_house_number', 'player_full_address',
                'player_address_line_1', 'player_town', 'player_city'
            }
            if k in optional_fields:
                continue  # Skip empty optional fields (they'll be NULL in DB)
            
        airtable_data[k] = v
    
    return airtable_data


# Generate the AI-friendly OpenAI function schema
def generate_ai_friendly_registration_schema():
    """
    Generate the detailed OpenAI schema that shows the AI all individual fields
    with their descriptions - just like the old function calling approach.
    """
    return pydantic_to_openai_schema(
        pydantic_model=RegistrationDataContract,
        function_name="update_reg_details_to_db",
        function_description="""
        Save complete registration data to the registrations_2526 database.
        
        Use your AI intelligence to extract each piece of information from the conversation 
        history and provide it in the exact format specified for each field below.
        
        You should be able to find all this information from the conversation as the user
        has been asked for each piece during routines 1-29. Look through the conversation
        carefully and extract each field using your understanding of the context.
        
        For conditional fields (like medical_description, previous_team_name, player_telephone),
        only provide them if the conditions are met based on the conversation.
        
        Call this function AFTER create_payment_token succeeds in routine 29.
        """
    )


# The tool definition that the AI will see - all individual fields with descriptions!
UPDATE_REG_DETAILS_TO_DB_AI_FRIENDLY_TOOL = generate_ai_friendly_registration_schema() 