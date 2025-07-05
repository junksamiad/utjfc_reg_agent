#!/usr/bin/env python3
"""
Simple script to clean up test photos from S3 bucket
Usage: python3 cleanup_test_photos.py [filename_pattern]
"""

import subprocess
import sys

S3_BUCKET = "utjfc-player-photos"
AWS_PROFILE = "footballclub"

def list_and_delete_photos(pattern=None):
    """List and optionally delete photos matching pattern"""
    
    print("🔍 Listing photos in S3 bucket...")
    
    # List all files
    cmd = [
        "aws", "--profile", AWS_PROFILE,
        "s3", "ls", f"s3://{S3_BUCKET}/",
        "--no-cli-pager"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to list S3 bucket: {result.stderr}")
        return
        
    files = [line.split()[-1] for line in result.stdout.strip().split('\n') if line.strip()]
    
    if not files:
        print("ℹ️ No files found in bucket")
        return
        
    print(f"Found {len(files)} files:")
    for i, filename in enumerate(files, 1):
        print(f"  {i}. {filename}")
    
    # If pattern provided, filter files
    if pattern:
        matching_files = [f for f in files if pattern.lower() in f.lower()]
        if not matching_files:
            print(f"ℹ️ No files matching pattern '{pattern}'")
            return
        files = matching_files
        print(f"\nFiles matching '{pattern}':")
        for i, filename in enumerate(files, 1):
            print(f"  {i}. {filename}")
    
    # Ask for confirmation
    if len(files) == 1:
        confirm = input(f"\n🗑️ Delete {files[0]}? (y/N): ")
    else:
        confirm = input(f"\n🗑️ Delete {len(files)} files? (y/N): ")
    
    if confirm.lower() != 'y':
        print("ℹ️ Cancelled")
        return
    
    # Delete files
    deleted = 0
    for filename in files:
        delete_cmd = [
            "aws", "--profile", AWS_PROFILE,
            "s3", "rm", f"s3://{S3_BUCKET}/{filename}",
            "--no-cli-pager"
        ]
        
        delete_result = subprocess.run(delete_cmd, capture_output=True, text=True)
        if delete_result.returncode == 0:
            print(f"✅ Deleted: {filename}")
            deleted += 1
        else:
            print(f"❌ Failed to delete {filename}: {delete_result.stderr}")
    
    print(f"\n🎉 Deleted {deleted}/{len(files)} files")

def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else None
    
    if pattern:
        print(f"🔍 Looking for files matching: {pattern}")
    else:
        print("🔍 Listing all files (use 'python3 cleanup_test_photos.py <pattern>' to filter)")
    
    list_and_delete_photos(pattern)

if __name__ == "__main__":
    main()