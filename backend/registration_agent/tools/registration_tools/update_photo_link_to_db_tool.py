#!/usr/bin/env python3
"""
Tool to update photo link in the registrations database.

This tool updates the id_image_link field in Airtable after successful S3 upload.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from pyairtable import Api
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

class PhotoLinkData(BaseModel):
    """Data model for updating photo link in database"""
    record_id: str = Field(..., description="The Airtable record ID to update")
    id_image_link: str = Field(..., description="The S3 URL of the uploaded photo")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Complete conversation history with speaker identification")

def update_photo_link_to_db(**kwargs) -> Dict[str, Any]:
    """
    Update the id_image_link field in the registrations database.
    
    Args:
        **kwargs: Contains record_id and id_image_link
        
    Returns:
        Dict containing success status and details
    """
    try:
        # Validate the input data
        data = PhotoLinkData(**kwargs)
        # Check database connection
        if not AIRTABLE_API_KEY:
            return {
                "success": False,
                "error": "Airtable API key not configured"
            }
        
        # Get the Airtable table
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Verify the record exists
        try:
            existing_record = table.get(data.record_id)
            if not existing_record:
                return {
                    "success": False,
                    "error": f"Record with ID {data.record_id} not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid record ID {data.record_id}: {str(e)}"
            }
        
        # Update the record with the photo link and conversation history
        update_data = {
            "id_image_link": data.id_image_link
        }
        
        # Add conversation history if provided
        if data.conversation_history:
            # Convert conversation history to JSON string
            conversation_json = json.dumps(data.conversation_history, indent=2)
            update_data["conversation_history"] = conversation_json
        
        updated_record = table.update(data.record_id, update_data)
        
        # Extract relevant fields for response
        fields = updated_record.get('fields', {})
        
        return {
            "success": True,
            "record_id": data.record_id,
            "message": "Photo link successfully saved to database",
            "updated_fields": {
                "id_image_link": fields.get('id_image_link'),
                "id_photo_provided": fields.get('id_photo_provided', 'Not computed yet')
            },
            "player_info": {
                "player_first_name": fields.get('player_first_name'),
                "player_last_name": fields.get('player_last_name'),
                "team": fields.get('team'),
                "age_group": fields.get('age_group')
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update photo link: {str(e)}"
        }

# OpenAI function schema for the AI agent
UPDATE_PHOTO_LINK_SCHEMA = {
    "type": "function",
    "name": "update_photo_link_to_db",
    "description": "Update the id_image_link field in the database after successful photo upload to S3",
    "parameters": {
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The Airtable record ID to update (obtained from previous registration steps)"
            },
            "id_image_link": {
                "type": "string",
                "description": "The complete S3 URL of the uploaded photo (e.g., https://s3.eu-north-1.amazonaws.com/utjfc-player-photos/filename.jpg)"
            },
            "conversation_history": {
                "type": "array",
                "description": "Complete conversation history with role and content for each message",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            }
        },
        "required": ["record_id", "id_image_link"]
    }
}

if __name__ == "__main__":
    # Test the function
    test_data = PhotoLinkData(
        record_id="rec_test123",
        id_image_link="https://s3.eu-north-1.amazonaws.com/utjfc-player-photos/test_photo.jpg"
    )
    
    result = update_photo_link_to_db(test_data)
    print("Test result:", result) 