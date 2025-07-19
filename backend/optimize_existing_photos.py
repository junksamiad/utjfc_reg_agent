#!/usr/bin/env python3
"""
Standalone script to optimize existing photos in S3 bucket.

This script applies the same photo optimization (4:5 aspect ratio resize and file size optimization)
that the new photo upload feature applies, but to existing photos already in the S3 bucket.

Usage:
    # Test on one photo first
    python optimize_existing_photos.py --test sebhayton_leopards_u9.jpg
    
    # Process all photos
    python optimize_existing_photos.py --all
    
    # Process specific photos
    python optimize_existing_photos.py maxstanmore_phoenix_u15.jpg archiedisora_dragons_u9.jpeg
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict, Any
import boto3
from dotenv import load_dotenv

# Add the registration_agent tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'registration_agent', 'tools'))

# Import the FIXED photo optimization function
try:
    from photo_processing.photo_optimizer_fixed import optimize_player_photo
    PHOTO_OPTIMIZATION_AVAILABLE = True
    print("✅ FIXED Photo optimization module loaded successfully")
except ImportError as e:
    PHOTO_OPTIMIZATION_AVAILABLE = False
    print(f"❌ Failed to load FIXED photo optimization module: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# AWS S3 configuration
S3_BUCKET_NAME = "utjfc-player-photos"
AWS_REGION = "eu-north-1"

# AWS Profile setup (same logic as in upload_photo_to_s3_tool.py)
is_production = (
    os.environ.get('AWS_EXECUTION_ENV') is not None or
    os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is not None or
    os.environ.get('AWS_INSTANCE_ID') is not None or
    os.path.exists('/opt/elasticbeanstalk') or
    os.environ.get('EB_IS_COMMAND_LEADER') is not None
)

if not is_production and os.path.exists(os.path.expanduser('~/.aws/credentials')):
    os.environ['AWS_PROFILE'] = 'footballclub'
    print("🏠 Local environment detected - using 'footballclub' AWS profile")
else:
    if 'AWS_PROFILE' in os.environ:
        del os.environ['AWS_PROFILE']
    print("☁️  Production environment detected - using IAM role for AWS access")


def get_s3_client():
    """Initialize and return S3 client."""
    return boto3.client('s3', region_name=AWS_REGION)


def list_bucket_photos() -> List[str]:
    """List all photos in the S3 bucket."""
    print(f"📋 Listing photos in bucket: {S3_BUCKET_NAME}")
    
    s3_client = get_s3_client()
    
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        
        if 'Contents' not in response:
            print("📭 No photos found in bucket")
            return []
        
        photos = []
        for obj in response['Contents']:
            filename = obj['Key']
            size_mb = obj['Size'] / (1024 * 1024)
            
            # Skip already optimized photos
            if '_optimized' in filename:
                print(f"   ⏭️  Skipping already optimized: {filename}")
                continue
                
            photos.append(filename)
            print(f"   📷 {filename} ({size_mb:.1f}MB)")
        
        print(f"📊 Found {len(photos)} photos to potentially optimize")
        return photos
        
    except Exception as e:
        print(f"❌ Failed to list bucket contents: {e}")
        return []


def download_photo(filename: str, temp_dir: str) -> str:
    """Download a photo from S3 to temporary directory."""
    print(f"⬇️  Downloading {filename} from S3...")
    
    s3_client = get_s3_client()
    local_path = os.path.join(temp_dir, filename)
    
    try:
        s3_client.download_file(S3_BUCKET_NAME, filename, local_path)
        file_size = os.path.getsize(local_path)
        print(f"   ✅ Downloaded to {local_path} ({file_size:,} bytes)")
        return local_path
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return None


def optimize_photo(local_path: str) -> Tuple[str, Dict[str, Any], bool]:
    """Apply photo optimization to downloaded file."""
    print(f"🔄 Optimizing photo: {local_path}")
    
    try:
        # Read the image file
        with open(local_path, 'rb') as f:
            image_bytes = f.read()
        
        # Get filename for format detection
        filename = os.path.basename(local_path)
        
        # Apply the same optimization as the upload feature
        optimized_bytes, metadata = optimize_player_photo(image_bytes, filename)
        
        if metadata.get('optimization_applied', False):
            # Save optimized version
            base_path = os.path.splitext(local_path)[0]
            optimized_path = f"{base_path}_optimized.jpg"
            
            with open(optimized_path, 'wb') as f:
                f.write(optimized_bytes)
            
            print(f"   ✅ Optimization applied: {optimized_path}")
            print(f"   📊 Details: {metadata}")
            return optimized_path, metadata, True
        else:
            print(f"   ⚠️  Optimization skipped: {metadata}")
            return local_path, metadata, False
            
    except Exception as e:
        print(f"   ❌ Optimization failed: {e}")
        return None, {"optimization_applied": False, "error": str(e)}, False


def upload_optimized_photo(local_path: str, original_filename: str, metadata: Dict[str, Any]) -> bool:
    """Upload optimized photo back to S3 with new filename."""
    # Generate new filename with _optimized suffix
    base_name = os.path.splitext(original_filename)[0]
    optimized_filename = f"{base_name}_optimized.jpg"
    
    print(f"⬆️  Uploading optimized photo as: {optimized_filename}")
    
    s3_client = get_s3_client()
    
    try:
        # Upload with metadata about the optimization
        s3_client.upload_file(
            local_path,
            S3_BUCKET_NAME,
            optimized_filename,
            ExtraArgs={
                'ContentType': 'image/jpeg',
                'Metadata': {
                    'original_filename': original_filename,
                    'optimization_applied': str(metadata.get('optimization_applied', False)),
                    'original_dimensions': metadata.get('original_dimensions', 'unknown'),
                    'final_dimensions': metadata.get('final_dimensions', 'unknown'),
                    'size_reduction_percent': str(metadata.get('size_reduction_percent', 0)),
                    'processing_timestamp': str(metadata.get('processing_timestamp', 'unknown'))
                }
            }
        )
        
        # Get file size
        file_size = os.path.getsize(local_path)
        print(f"   ✅ Upload successful: {optimized_filename} ({file_size:,} bytes)")
        return True
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False


def process_single_photo(filename: str, temp_dir: str) -> bool:
    """Process a single photo through the optimization pipeline."""
    print(f"\n🎯 Processing: {filename}")
    print("=" * 50)
    
    # Step 1: Download
    local_path = download_photo(filename, temp_dir)
    if not local_path:
        return False
    
    # Step 2: Optimize
    optimized_path, metadata, optimization_applied = optimize_photo(local_path)
    if not optimized_path:
        return False
    
    # Step 3: Upload optimized version
    if optimization_applied:
        success = upload_optimized_photo(optimized_path, filename, metadata)
        if success:
            print(f"✅ Successfully processed {filename}")
            return True
        else:
            print(f"❌ Failed to upload optimized version of {filename}")
            return False
    else:
        print(f"⚠️  No optimization needed for {filename}")
        return True


def main():
    parser = argparse.ArgumentParser(description='Optimize existing photos in S3 bucket')
    parser.add_argument('--test', metavar='FILENAME', help='Test optimization on a single photo')
    parser.add_argument('--all', action='store_true', help='Process all photos in bucket')
    parser.add_argument('photos', nargs='*', help='Specific photo filenames to process')
    
    args = parser.parse_args()
    
    print("🚀 UTJFC Photo Optimization Script")
    print("=" * 40)
    
    # Validate photo optimization is available
    if not PHOTO_OPTIMIZATION_AVAILABLE:
        print("❌ Photo optimization not available - exiting")
        return 1
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Determine which photos to process
        photos_to_process = []
        
        if args.test:
            # Test mode - single photo
            photos_to_process = [args.test]
            print(f"🧪 Test mode: processing {args.test}")
            
        elif args.all:
            # Process all photos
            all_photos = list_bucket_photos()
            photos_to_process = all_photos
            print(f"🌍 Processing all {len(photos_to_process)} photos")
            
        elif args.photos:
            # Process specific photos
            photos_to_process = args.photos
            print(f"🎯 Processing {len(photos_to_process)} specified photos")
            
        else:
            # No photos specified
            print("❌ No photos specified. Use --test, --all, or specify photo filenames")
            parser.print_help()
            return 1
        
        # Process each photo
        success_count = 0
        failure_count = 0
        
        for filename in photos_to_process:
            try:
                success = process_single_photo(filename, temp_dir)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            except KeyboardInterrupt:
                print("\n⚠️  Process interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error processing {filename}: {e}")
                failure_count += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 PROCESSING SUMMARY")
        print("=" * 50)
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failure_count}")
        print(f"📷 Total processed: {success_count + failure_count}")
        
        if args.test and success_count > 0:
            print("\n🎉 Test successful! You can now run with --all to process all photos")
        
        return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)