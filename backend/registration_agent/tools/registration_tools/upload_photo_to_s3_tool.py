import boto3
import os
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add HEIC support and photo optimization
try:
    from PIL import Image
    from pillow_heif import register_heif_opener
    # Register HEIF opener with Pillow to handle HEIC files
    register_heif_opener()
    HEIC_SUPPORT = True
    print("✅ HEIC conversion support enabled")
except ImportError:
    HEIC_SUPPORT = False
    print("⚠️  HEIC conversion not available - install pillow-heif for HEIC support")

# Add photo optimization support
try:
    from ..photo_processing import optimize_player_photo
    PHOTO_OPTIMIZATION_SUPPORT = True
    print("✅ Photo optimization support enabled")
except ImportError as e:
    PHOTO_OPTIMIZATION_SUPPORT = False
    print(f"⚠️  Photo optimization not available: {e}")

load_dotenv()

# AWS S3 configuration
S3_BUCKET_NAME = "utjfc-player-photos"
AWS_REGION = "eu-north-1"

# Only set AWS profile for local development (not in production/EC2)
# In production, EC2 instances use IAM roles instead of profiles
# Check for common production environment indicators
is_production = (
    os.environ.get('AWS_EXECUTION_ENV') is not None or  # Lambda/ECS
    os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is not None or  # ECS/Fargate
    os.environ.get('AWS_INSTANCE_ID') is not None or  # EC2
    os.path.exists('/opt/elasticbeanstalk') or  # Elastic Beanstalk
    os.environ.get('EB_IS_COMMAND_LEADER') is not None  # Elastic Beanstalk
)

if not is_production and os.path.exists(os.path.expanduser('~/.aws/credentials')):
    # We're running locally and have AWS credentials, set the AWS profile
    os.environ['AWS_PROFILE'] = 'footballclub'
    print("🏠 Local environment detected - using 'footballclub' AWS profile")
else:
    # We're in production or don't have local credentials, use IAM role
    # Make sure AWS_PROFILE is NOT set to avoid the ProfileNotFound error
    if 'AWS_PROFILE' in os.environ:
        del os.environ['AWS_PROFILE']
    print("☁️  Production environment detected - using IAM role for AWS access")


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


def _convert_heic_to_jpeg(file_path: str) -> str:
    """
    Convert HEIC file to JPEG format for compatibility.
    
    Args:
        file_path: Path to the HEIC file
        
    Returns:
        str: Path to the converted JPEG file
    """
    if not HEIC_SUPPORT:
        raise ImportError("HEIC conversion not available - install pillow-heif: pip install pillow-heif")
    
    try:
        print(f"🔄 Converting HEIC file to JPEG: {file_path}")
        
        # Open HEIC file with Pillow (using pillow-heif)
        with Image.open(file_path) as img:
            print(f"   Original image mode: {img.mode}, size: {img.size}")
            
            # Convert to RGB (JPEG doesn't support RGBA)
            if img.mode in ('RGBA', 'LA', 'P'):
                print(f"   Converting from {img.mode} to RGB")
                img = img.convert('RGB')
            
            # Generate new filename with .jpg extension
            base_path = os.path.splitext(file_path)[0]
            jpeg_path = f"{base_path}_converted.jpg"
            
            # Save as JPEG with good quality
            img.save(jpeg_path, 'JPEG', quality=90, optimize=True)
            
            jpeg_size = os.path.getsize(jpeg_path)
            print(f"✅ HEIC converted to JPEG: {jpeg_path} ({jpeg_size:,} bytes)")
            return jpeg_path
            
    except Exception as e:
        print(f"❌ Failed to convert HEIC to JPEG: {e}")
        raise e


def _optimize_photo_for_fa_portal(file_path: str) -> tuple:
    """
    Optimize photo for FA portal compliance (4:5 ratio, optimal file size).
    
    Args:
        file_path: Path to the photo file
        
    Returns:
        tuple: (optimized_file_path, optimization_metadata, success)
    """
    if not PHOTO_OPTIMIZATION_SUPPORT:
        print("⚠️  Photo optimization not available, using original photo")
        return file_path, {"optimization_applied": False}, True
    
    try:
        print(f"🔄 Optimizing photo for FA portal compliance: {file_path}")
        
        # Read the image file
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        
        # Get filename for format detection
        filename = os.path.basename(file_path)
        
        # Optimize the photo
        optimized_bytes, metadata = optimize_player_photo(image_bytes, filename)
        
        # If optimization was applied, save the optimized version
        if metadata.get('optimization_applied', False):
            # Generate optimized filename
            base_path = os.path.splitext(file_path)[0]
            optimized_path = f"{base_path}_optimized.jpg"
            
            # Save optimized image
            with open(optimized_path, 'wb') as f:
                f.write(optimized_bytes)
            
            optimized_size = os.path.getsize(optimized_path)
            print(f"✅ Photo optimized: {optimized_path} ({optimized_size:,} bytes)")
            print(f"   📊 Optimization details: {metadata}")
            
            return optimized_path, metadata, True
        else:
            # Optimization wasn't applied (disabled or error), use original
            print(f"⚠️  Photo optimization skipped: {metadata}")
            return file_path, metadata, True
            
    except Exception as e:
        print(f"❌ Photo optimization failed: {e}")
        print("   Using original photo as fallback")
        return file_path, {"optimization_applied": False, "error": str(e)}, False


def upload_photo_to_s3(**kwargs) -> Dict[str, Any]:
    """
    Upload a player photo to S3 and return the URL.
    
    This function:
    1. Extracts the file path from session history (UPLOADED_FILE_PATH message)
    2. Converts HEIC files to JPEG if needed
    3. Validates the photo upload data using Pydantic
    4. Generates a unique filename for the photo
    5. Uploads the photo to S3
    6. Returns the S3 URL for storage in the database
    
    Args:
        **kwargs: Photo upload data including record_id, player names
    
    Returns:
        dict: Result with success status, S3 URL, and upload details
    """
    
    print("🚀 Starting photo upload process...")
    print(f"📋 Received kwargs: {kwargs}")
    
    try:
        # Step 1: Get the uploaded file path from session history
        print("🔍 Step 1: Looking for uploaded file path in session history...")
        file_path = None
        
        # Import session history function here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from urmston_town_agent.chat_history import get_session_history
            
            # Get current session ID from environment or default
            session_id = os.environ.get('CURRENT_SESSION_ID', 'default_session_id')
            print(f"   Using session ID: {session_id}")
            
            session_history = get_session_history(session_id)
            print(f"   Session history length: {len(session_history)}")
            
            # Look for the UPLOADED_FILE_PATH message in session history
            for i, message in enumerate(reversed(session_history)):  # Search from most recent
                if (message.get('role') == 'system' and 
                    message.get('content', '').startswith('UPLOADED_FILE_PATH:')):
                    file_path = message['content'].replace('UPLOADED_FILE_PATH:', '').strip()
                    print(f"   ✅ Found file path at message -{i}: {file_path}")
                    break
                    
        except Exception as e:
            print(f"   ⚠️  Warning: Could not get file path from session history: {e}")
        
        if not file_path:
            print("❌ No uploaded file found in session history")
            return {
                "success": False,
                "message": "No uploaded file found in session history",
                "s3_url": None
            }
        
        # Step 2: Validate the AI-provided data using Pydantic
        print("🔍 Step 2: Validating AI-provided data...")
        print(f"   Raw player_full_name: '{kwargs.get('player_full_name', 'NOT_PROVIDED')}'")
        print(f"   Raw team: '{kwargs.get('team', 'NOT_PROVIDED')}'")
        print(f"   Raw age_group: '{kwargs.get('age_group', 'NOT_PROVIDED')}'")
        print(f"   Raw record_id: '{kwargs.get('record_id', 'NOT_PROVIDED')}'")
        
        # Check for placeholder text that indicates AI didn't extract properly
        player_name = kwargs.get('player_full_name', '')
        if '[' in player_name and ']' in player_name:
            print(f"❌ ERROR: AI passed placeholder text instead of actual player name: {player_name}")
            return {
                "success": False,
                "message": f"AI failed to extract player name from conversation history. Got placeholder: {player_name}",
                "s3_url": None,
                "debug_info": {
                    "issue": "AI_PLACEHOLDER_TEXT",
                    "received_name": player_name,
                    "suggestion": "AI should extract actual player name from conversation history"
                }
            }
        
        validated_data = PhotoUploadData(**kwargs)
        print(f"   ✅ Data validation successful")
        print(f"   Validated player_full_name: '{validated_data.player_full_name}'")
        
        # Step 3: Check if file exists
        print("🔍 Step 3: Checking if file exists...")
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return {
                "success": False,
                "message": f"File not found: {file_path}",
                "s3_url": None
            }
        
        file_size = os.path.getsize(file_path)
        print(f"   ✅ File exists: {file_path} ({file_size:,} bytes)")
        
        # Step 4: Handle HEIC conversion if needed
        print("🔍 Step 4: Checking file format and converting if needed...")
        original_extension = os.path.splitext(file_path)[1].lower()
        print(f"   Original file extension: {original_extension}")
        
        if original_extension == '.heic':
            print("   🔄 HEIC file detected - converting to JPEG...")
            try:
                file_path = _convert_heic_to_jpeg(file_path)
                print(f"   ✅ Conversion successful: {file_path}")
            except Exception as e:
                print(f"   ❌ HEIC conversion failed: {e}")
                return {
                    "success": False,
                    "message": f"Failed to convert HEIC file: {str(e)}",
                    "s3_url": None
                }
        
        # Step 4.5: Optimize photo for FA portal compliance
        print("🔍 Step 4.5: Optimizing photo for FA portal compliance...")
        optimization_metadata = {}
        try:
            optimized_path, optimization_metadata, optimization_success = _optimize_photo_for_fa_portal(file_path)
            if optimization_success and optimized_path != file_path:
                # Use optimized photo for upload
                file_path = optimized_path
                print(f"   ✅ Using optimized photo: {file_path}")
            else:
                print(f"   ⚠️  Using original photo: {file_path}")
        except Exception as e:
            print(f"   ❌ Photo optimization failed: {e}")
            print("   Continuing with original photo")
            optimization_metadata = {"optimization_applied": False, "error": str(e)}
        
        # Step 5: Generate filename using player_full_name+team+age_group.ext format
        print("🔍 Step 5: Generating S3 filename...")
        file_extension = os.path.splitext(file_path)[1].lower()
        print(f"   Final file extension: {file_extension}")
        
        # Clean names for filename (remove spaces, special chars, keep only alphanumeric)
        clean_name = "".join(c for c in validated_data.player_full_name if c.isalnum()).lower()
        clean_team = "".join(c for c in validated_data.team if c.isalnum()).lower()
        clean_age_group = "".join(c for c in validated_data.age_group if c.isalnum()).lower()
        
        filename = f"{clean_name}_{clean_team}_{clean_age_group}{file_extension}"
        print(f"   Generated filename: {filename}")
        print(f"   Clean name parts: '{clean_name}' + '{clean_team}' + '{clean_age_group}'")
        
        # Step 6: Initialize S3 client (uses AWS profile set in environment)
        print("🔍 Step 6: Initializing S3 client...")
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        print(f"   S3 bucket: {S3_BUCKET_NAME}")
        print(f"   S3 region: {AWS_REGION}")
        
        # Step 7: Upload file to S3
        print("🔍 Step 7: Uploading to S3...")
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
                        'upload_timestamp': datetime.now().isoformat(),
                        'original_extension': original_extension,
                        'optimization_applied': str(optimization_metadata.get('optimization_applied', False)),
                        'optimization_details': str(optimization_metadata)
                    }
                }
            )
            print("   ✅ S3 upload successful")
        except Exception as e:
            print(f"   ❌ S3 upload failed: {e}")
            return {
                "success": False,
                "message": f"Failed to upload to S3: {str(e)}",
                "s3_url": None
            }
        
        # Step 8: Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        print(f"   Generated S3 URL: {s3_url}")
        
        # Step 9: Clean up local files
        print("🔍 Step 9: Cleaning up local files...")
        files_to_clean = [file_path]
        
        # If we converted HEIC, also clean up the original
        if original_extension == '.heic' and '_converted.jpg' in file_path:
            original_heic = file_path.replace('_converted.jpg', '.heic')
            if os.path.exists(original_heic):
                files_to_clean.append(original_heic)
        
        # If we optimized the photo, clean up the pre-optimization version
        if optimization_metadata.get('optimization_applied', False) and '_optimized.jpg' in file_path:
            pre_optimized = file_path.replace('_optimized.jpg', '_converted.jpg' if original_extension == '.heic' else os.path.splitext(file_path.replace('_optimized', ''))[1])
            if os.path.exists(pre_optimized) and pre_optimized not in files_to_clean:
                files_to_clean.append(pre_optimized)
        
        for cleanup_file in files_to_clean:
            try:
                os.remove(cleanup_file)
                print(f"   ✅ Cleaned up: {cleanup_file}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not delete {cleanup_file}: {e}")
        
        print("🎉 Photo upload completed successfully!")
        return {
            "success": True,
            "message": f"Photo uploaded successfully for {validated_data.player_full_name}",
            "s3_url": s3_url,
            "filename": filename,
            "player_name": validated_data.player_full_name,
            "team": validated_data.team,
            "age_group": validated_data.age_group,
            "record_id": validated_data.record_id,
            "debug_info": {
                "original_extension": original_extension,
                "final_extension": file_extension,
                "heic_converted": original_extension == '.heic',
                "file_size_bytes": file_size,
                "photo_optimization": optimization_metadata
            }
        }
        
    except Exception as e:
        print(f"❌ Photo upload failed with exception: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Failed to upload photo: {str(e)}",
            "s3_url": None,
            "debug_info": {
                "exception_type": type(e).__name__,
                "exception_message": str(e)
            }
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