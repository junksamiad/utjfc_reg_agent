import boto3
import os
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# AWS S3 configuration
S3_BUCKET_NAME = "utjfc-player-photos"
AWS_REGION = "eu-north-1"

# Ensure AWS profile is set for S3 operations
os.environ['AWS_PROFILE'] = 'footballclub'


class PhotoUploadData(BaseModel):
    """
    Pydantic model for photo upload data.
    """
    
    record_id: str = Field(
        ...,
        description="The Airtable record ID from the registration - extract this from conversation history"
    )
    
    player_full_name: str = Field(
        ...,
        description="Player's full name - extract from conversation history for file naming"
    )
    
    team: str = Field(
        ...,
        description="Team name - extract from conversation history for file naming"
    )
    
    age_group: str = Field(
        ...,
        description="Age group (e.g., u9, u10) - extract from conversation history for file naming"
    )


def upload_photo_to_s3(**kwargs) -> Dict[str, Any]:
    """
    Upload a player photo to S3 and return the URL.
    
    This function:
    1. Extracts the file path from session history (UPLOADED_FILE_PATH message)
    2. Validates the photo upload data using Pydantic
    3. Generates a unique filename for the photo
    4. Uploads the photo to S3
    5. Returns the S3 URL for storage in the database
    
    Args:
        **kwargs: Photo upload data including record_id, player names
    
    Returns:
        dict: Result with success status, S3 URL, and upload details
    """
    
    try:
        # Step 1: Get the uploaded file path from session history
        # This is set by the upload endpoint as a system message: UPLOADED_FILE_PATH: /path/to/file
        file_path = None
        
        # Import session history function here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from urmston_town_agent.chat_history import get_session_history
            
            # Get current session ID from environment or default
            session_id = os.environ.get('CURRENT_SESSION_ID', 'default_session_id')
            session_history = get_session_history(session_id)
            
            # Look for the UPLOADED_FILE_PATH message in session history
            for message in reversed(session_history):  # Search from most recent
                if (message.get('role') == 'system' and 
                    message.get('content', '').startswith('UPLOADED_FILE_PATH:')):
                    file_path = message['content'].replace('UPLOADED_FILE_PATH:', '').strip()
                    break
                    
        except Exception as e:
            print(f"Warning: Could not get file path from session history: {e}")
        
        if not file_path:
            return {
                "success": False,
                "message": "No uploaded file found in session history",
                "s3_url": None
            }
        
        # Step 2: Validate the AI-provided data using Pydantic
        validated_data = PhotoUploadData(**kwargs)
        
        # Step 3: Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File not found: {file_path}",
                "s3_url": None
            }
        
        # Step 4: Generate filename using player_full_name+team+age_group.ext format
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Clean names for filename (remove spaces, special chars, keep only alphanumeric)
        clean_name = "".join(c for c in validated_data.player_full_name if c.isalnum()).lower()
        clean_team = "".join(c for c in validated_data.team if c.isalnum()).lower()
        clean_age_group = "".join(c for c in validated_data.age_group if c.isalnum()).lower()
        
        filename = f"{clean_name}_{clean_team}_{clean_age_group}{file_extension}"
        
        # Step 5: Initialize S3 client (uses AWS profile set in environment)
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Step 6: Upload file to S3
        try:
            s3_client.upload_file(
                file_path,
                S3_BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': _get_content_type(file_extension),
                    'Metadata': {
                        'record_id': validated_data.record_id,
                        'player_name': validated_data.player_full_name,
                        'team': validated_data.team,
                        'age_group': validated_data.age_group,
                        'upload_timestamp': datetime.now().isoformat()
                    }
                }
            )
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to upload to S3: {str(e)}",
                "s3_url": None
            }
        
        # Step 7: Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        
        # Step 8: Clean up local file
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not delete local file {file_path}: {e}")
        
        return {
            "success": True,
            "message": f"Photo uploaded successfully for {validated_data.player_full_name}",
            "s3_url": s3_url,
            "filename": filename,
            "player_name": validated_data.player_full_name,
            "team": validated_data.team,
            "age_group": validated_data.age_group,
            "record_id": validated_data.record_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to upload photo: {str(e)}",
            "s3_url": None
        }


def _get_content_type(file_extension: str) -> str:
    """Get the appropriate content type for the file extension."""
    content_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.heic': 'image/heic'
    }
    return content_types.get(file_extension, 'application/octet-stream')


def generate_upload_photo_schema():
    """
    Generate the OpenAI function schema for the photo upload tool.
    """
    return {
        "type": "function",
        "name": "upload_photo_to_s3",
        "description": """
        Upload a player's photo to S3 storage for their registration record.
        
        Call this function after a photo has been uploaded by the user.
        Extract the record_id from the conversation history - it was returned by the 
        update_reg_details_to_db tool call in routine 29.
        
        The photo will be stored with a unique filename and the S3 URL will be returned
        for saving to the registration database.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "The Airtable record ID from the registration - extract this from conversation history (format: rec...)"
                },
                "player_full_name": {
                    "type": "string",
                    "description": "Player's full name - extract from conversation history for file naming"
                },
                "team": {
                    "type": "string",
                    "description": "Team name - extract from conversation history for file naming"
                },
                "age_group": {
                    "type": "string",
                    "description": "Age group (e.g., u9, u10) - extract from conversation history for file naming"
                }
            },
            "required": [
                "record_id",
                "player_full_name", 
                "team",
                "age_group"
            ]
        }
    }


# The tool definition that the AI will see
UPLOAD_PHOTO_TO_S3_TOOL = generate_upload_photo_schema() 