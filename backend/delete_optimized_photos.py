#!/usr/bin/env python3
"""
Script to delete all _optimized photos from S3 bucket before re-processing with fixed algorithm.
"""

import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS S3 configuration
S3_BUCKET_NAME = "utjfc-player-photos"
AWS_REGION = "eu-north-1"

# AWS Profile setup
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

def main():
    print("🗑️  UTJFC Delete Optimized Photos Script")
    print("=" * 45)
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    # List all optimized photos
    print(f"📋 Listing optimized photos in bucket: {S3_BUCKET_NAME}")
    
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        
        if 'Contents' not in response:
            print("📭 No files found in bucket")
            return
        
        optimized_photos = []
        for obj in response['Contents']:
            filename = obj['Key']
            if '_optimized' in filename:
                optimized_photos.append(filename)
        
        if not optimized_photos:
            print("📭 No optimized photos found")
            return
        
        print(f"   Found {len(optimized_photos)} optimized photos to delete:")
        for photo in optimized_photos:
            print(f"   📷 {photo}")
        
        # Confirm deletion
        print(f"\n❓ Delete all {len(optimized_photos)} optimized photos?")
        print("   (This will clear the bucket for fresh optimization with fixed algorithm)")
        
        # Auto-confirm since this was requested
        print("✅ Proceeding with deletion...")
        
        # Delete each photo
        success_count = 0
        failure_count = 0
        
        for photo in optimized_photos:
            try:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=photo)
                print(f"   ✅ Deleted: {photo}")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Failed to delete {photo}: {e}")
                failure_count += 1
        
        # Summary
        print("\n" + "=" * 45)
        print("📊 DELETION SUMMARY")
        print("=" * 45)
        print(f"✅ Successfully deleted: {success_count}")
        print(f"❌ Failed to delete: {failure_count}")
        print(f"🗑️  Total processed: {success_count + failure_count}")
        
        if success_count > 0:
            print(f"\n🎉 Successfully cleared {success_count} optimized photos!")
            print("   Ready for fresh optimization with fixed algorithm.")
        
    except Exception as e:
        print(f"❌ Error accessing S3 bucket: {e}")

if __name__ == "__main__":
    main()