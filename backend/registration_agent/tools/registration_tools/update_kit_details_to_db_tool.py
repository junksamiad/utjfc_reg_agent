from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')


class KitDetailsData(BaseModel):
    """
    Pydantic model for kit details that need to be saved to the database.
    """
    
    new_kit_required: Literal["Y", "N"] = Field(
        default="Y",
        description="Whether player requires a new kit this season - defaults to 'Y' since they're going through kit selection"
    )
    
    kit_type_required: Literal["Goalkeeper", "Outfield"] = Field(
        ...,
        description="Type of kit required. Set to 'Goalkeeper' if shirt_number is 1, otherwise set to 'Outfield' for all other shirt numbers"
    )
    
    kit_size: Literal["5/6", "7/8", "9/10", "11/12", "13/14", "S", "M", "L", "XL", "2XL", "3XL"] = Field(
        ...,
        description="Kit size selected by player/parent - should be extracted from conversation history where they chose their kit size"
    )
    
    shirt_number: int = Field(
        ...,
        ge=1,
        le=20,
        description="Shirt number chosen by player (1-20) - should be extracted from conversation history where they chose their shirt number"
    )
    
    # Record ID to update (extracted from initial registration)
    record_id: str = Field(
        ...,
        description="The Airtable record ID returned from the initial update_reg_details_to_db call in routine 29 - extract this from the tool result in conversation history"
    )


def update_kit_details_to_db(**kwargs) -> Dict[str, Any]:
    """
    Update kit details for an existing registration record.
    
    This function:
    1. Validates the kit details provided by the AI
    2. Finds the existing registration record using player name, team, and age group
    3. Updates only the kit-related fields
    4. Returns success status and confirmation details
    
    Returns:
        dict: Result with success status, record ID, and kit details summary
    """
    
    print("🎽 Starting kit details update process...")
    print(f"📋 Received kwargs: {kwargs}")
    
    try:
        # Step 1: Validate all the AI-provided kit data using Pydantic
        print("🔍 Step 1: Validating kit details...")
        print(f"   Raw kit_size: '{kwargs.get('kit_size', 'NOT_PROVIDED')}'")
        print(f"   Raw shirt_number: '{kwargs.get('shirt_number', 'NOT_PROVIDED')}'")
        print(f"   Raw kit_type_required: '{kwargs.get('kit_type_required', 'NOT_PROVIDED')}'")
        print(f"   Raw record_id: '{kwargs.get('record_id', 'NOT_PROVIDED')}'")
        
        validated_data = KitDetailsData(**kwargs)
        print(f"   ✅ Kit data validation successful")
        print(f"   Validated kit_size: {validated_data.kit_size}")
        print(f"   Validated shirt_number: {validated_data.shirt_number}")
        print(f"   Validated kit_type_required: {validated_data.kit_type_required}")
        
        # Step 2: Check database connection
        print("🔍 Step 2: Checking database connection...")
        if not AIRTABLE_API_KEY:
            print("❌ Airtable API key not configured")
            return {
                "success": False,
                "message": "Airtable API key not configured",
                "record_id": None
            }
        
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        print(f"   ✅ Connected to Airtable: {BASE_ID}/{TABLE_ID}")
        
        # Step 3: Get the specific record using the provided record_id
        print("🔍 Step 3: Retrieving record from database...")
        print(f"   Looking for record ID: {validated_data.record_id}")
        try:
            record = table.get(validated_data.record_id)
            record_id = validated_data.record_id
            print(f"   ✅ Record found: {record['id']}")
            
            # Log some key existing fields for context
            existing_fields = record.get("fields", {})
            player_name = existing_fields.get("player_full_name", "Unknown")
            team = existing_fields.get("team", "Unknown")
            print(f"   Player: {player_name}, Team: {team}")
            
        except Exception as e:
            print(f"❌ Record lookup failed: {e}")
            return {
                "success": False,
                "message": f"Record ID {validated_data.record_id} not found in database: {str(e)}",
                "record_id": validated_data.record_id,
                "debug_info": {
                    "record_id": validated_data.record_id,
                    "error_type": type(e).__name__
                }
            }
        
        # Step 4: Update the record with kit details
        print("🔍 Step 4: Updating kit details in database...")
        
        # Prepare kit data for update
        kit_update_data = {
            "new_kit_required": validated_data.new_kit_required,
            "kit_type_required": validated_data.kit_type_required,
            "kit_size": validated_data.kit_size,
            "shirt_number": str(validated_data.shirt_number)  # Convert to string for Airtable
        }
        print(f"   Update data: {kit_update_data}")
        
        # Update the record
        try:
            updated_record = table.update(record_id, kit_update_data)
            print(f"   ✅ Kit details updated successfully")
        except Exception as e:
            print(f"❌ Database update failed: {e}")
            return {
                "success": False,
                "message": f"Failed to update kit details: {str(e)}",
                "record_id": record_id,
                "debug_info": {
                    "update_data": kit_update_data,
                    "error_type": type(e).__name__
                }
            }
        
        # Get player info from the updated record for response
        updated_fields = updated_record.get("fields", {})
        player_name = updated_fields.get("player_full_name", "Player")
        
        print(f"🎉 Kit details update completed for {player_name}!")
        return {
            "success": True,
            "message": f"Kit details saved successfully for {player_name}",
            "record_id": record_id,
            "player_name": player_name,
            "team": updated_fields.get("team", "Unknown"),
            "age_group": updated_fields.get("age_group", "Unknown"),
            "kit_size": validated_data.kit_size,
            "shirt_number": validated_data.shirt_number,
            "kit_type": validated_data.kit_type_required
        }
        
    except ValidationError as e:
        print(f"❌ Kit data validation failed: {e}")
        return {
            "success": False,
            "message": f"Kit details validation failed: {str(e)}",
            "record_id": None,
            "validation_errors": e.errors()
        }
    except Exception as e:
        print(f"❌ Kit details update failed with exception: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Failed to update kit details: {str(e)}",
            "record_id": None,
            "debug_info": {
                "exception_type": type(e).__name__,
                "exception_message": str(e)
            }
        }


def generate_update_kit_details_schema():
    """
    Generate the OpenAI function schema for the kit details update tool.
    """
    return {
        "type": "function",
        "name": "update_kit_details_to_db",
        "description": """
        Update kit details for an existing registration record in the database.
        
        Call this function after the shirt number has been confirmed as available.
        Extract the record_id from the conversation history - it was returned by the 
        update_reg_details_to_db tool call in routine 29.
        
        IMPORTANT: Set kit_type_required based on shirt_number:
        - If shirt_number is 1, set kit_type_required to 'Goalkeeper'
        - If shirt_number is any other number (2-20), set kit_type_required to 'Outfield'
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "new_kit_required": {
                    "type": "string",
                    "enum": ["Y", "N"],
                    "description": "Whether player requires a new kit this season - defaults to 'Y' since they're going through kit selection"
                },
                "kit_type_required": {
                    "type": "string", 
                    "enum": ["Goalkeeper", "Outfield"],
                    "description": "Type of kit required. Set to 'Goalkeeper' if shirt_number is 1, otherwise set to 'Outfield' for all other shirt numbers (2-20)"
                },
                "kit_size": {
                    "type": "string",
                    "enum": ["5/6", "7/8", "9/10", "11/12", "13/14", "S", "M", "L", "XL", "2XL", "3XL"],
                    "description": "Kit size selected by player/parent - extract from conversation history where they chose their kit size"
                },
                "shirt_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Shirt number chosen by player (1-20) - extract from conversation history where they chose their shirt number and it was confirmed as available"
                },
                "record_id": {
                    "type": "string",
                    "description": "The Airtable record ID returned from the initial update_reg_details_to_db call in routine 29 - extract this from the tool result in conversation history (format: rec...)"
                }
            },
            "required": [
                "kit_type_required", 
                "kit_size", 
                "shirt_number",
                "record_id"
            ]
        }
    }


# The tool definition that the AI will see
UPDATE_KIT_DETAILS_TO_DB_TOOL = generate_update_kit_details_schema() 