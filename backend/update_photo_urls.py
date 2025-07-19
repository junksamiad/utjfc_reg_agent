#!/usr/bin/env python3
"""
Script to update id_image_link URLs from original photos to optimized versions.

This script:
1. Queries all records in registrations_2526 with photo URLs
2. Updates URLs to point to optimized versions (_optimized.jpg)
3. Handles file extension changes from various formats to .jpg
"""

import os
import sys
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the registration_agent tools to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'registration_agent', 'tools', 'airtable'))

# Import Airtable tools
try:
    from airtable_agent import execute_airtable_request
    AIRTABLE_AVAILABLE = True
    print("✅ Airtable tools loaded successfully")
except ImportError as e:
    AIRTABLE_AVAILABLE = False
    print(f"❌ Failed to load Airtable tools: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

def get_records_with_photos() -> List[Dict[str, Any]]:
    """Get all records that have photo URLs in id_image_link field."""
    print("🔍 Querying records with photo URLs...")
    
    query = "Show all records that have a URL in the id_image_link field - return record ID, player name, team, age group, and id_image_link"
    
    try:
        result = execute_airtable_request("2526", query)
        print(f"   📊 Query result: {result}")
        
        if result.get('success') and result.get('data'):
            records = result['data']
            print(f"   ✅ Found {len(records)} records with photos")
            return records
        else:
            print(f"   ⚠️  No records found or query failed: {result}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error querying records: {e}")
        return []

def convert_url_to_optimized(original_url: str) -> str:
    """Convert original photo URL to optimized version."""
    if not original_url or 'utjfc-player-photos' not in original_url:
        return original_url
    
    # Extract filename from URL
    # Example: https://utjfc-player-photos.s3.eu-north-1.amazonaws.com/jensoncoburn_lions_u10.jpeg
    filename_match = re.search(r'/([^/]+\.(jpg|jpeg|png|webp|heic))$', original_url, re.IGNORECASE)
    
    if not filename_match:
        print(f"   ⚠️  Could not extract filename from URL: {original_url}")
        return original_url
    
    original_filename = filename_match.group(1)
    
    # Remove extension and add _optimized.jpg
    base_filename = re.sub(r'\.(jpg|jpeg|png|webp|heic)$', '', original_filename, flags=re.IGNORECASE)
    optimized_filename = f"{base_filename}_optimized.jpg"
    
    # Replace in URL
    optimized_url = original_url.replace(original_filename, optimized_filename)
    
    print(f"   🔄 Converting: {original_filename} → {optimized_filename}")
    return optimized_url

def update_record_photo_url(record_id: str, player_name: str, new_url: str) -> bool:
    """Update a single record's photo URL."""
    print(f"📝 Updating {player_name} (ID: {record_id})")
    
    query = f"Update record {record_id} to set id_image_link to '{new_url}'"
    
    try:
        result = execute_airtable_request("2526", query)
        
        if result.get('success'):
            print(f"   ✅ Successfully updated {player_name}")
            return True
        else:
            print(f"   ❌ Failed to update {player_name}: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error updating {player_name}: {e}")
        return False

def main():
    print("🚀 UTJFC Photo URL Update Script")
    print("=" * 40)
    
    # Validate Airtable is available
    if not AIRTABLE_AVAILABLE:
        print("❌ Airtable tools not available - exiting")
        return 1
    
    # Step 1: Get all records with photos
    records = get_records_with_photos()
    
    if not records:
        print("📭 No records with photos found")
        return 0
    
    print(f"\n📋 Found {len(records)} records to update")
    print("=" * 50)
    
    # Step 2: Process each record
    success_count = 0
    failure_count = 0
    
    for i, record in enumerate(records, 1):
        try:
            # Extract record details
            record_id = record.get('record_id') or record.get('id')
            player_name = record.get('player_name') or record.get('name', 'Unknown')
            current_url = record.get('id_image_link', '')
            
            if not record_id:
                print(f"❌ Record {i}: Missing record ID")
                failure_count += 1
                continue
            
            if not current_url:
                print(f"⏭️  Record {i}: {player_name} - No photo URL")
                continue
            
            print(f"\n🎯 Record {i}/{len(records)}: {player_name}")
            print(f"   Current URL: {current_url}")
            
            # Convert URL to optimized version
            optimized_url = convert_url_to_optimized(current_url)
            
            if optimized_url == current_url:
                print(f"   ⏭️  No change needed (already optimized or invalid URL)")
                continue
            
            print(f"   New URL: {optimized_url}")
            
            # Update the record
            success = update_record_photo_url(record_id, player_name, optimized_url)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                
        except KeyboardInterrupt:
            print("\n⚠️  Process interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error processing record {i}: {e}")
            failure_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 UPDATE SUMMARY")
    print("=" * 50)
    print(f"✅ Successful updates: {success_count}")
    print(f"❌ Failed updates: {failure_count}")
    print(f"📷 Total processed: {success_count + failure_count}")
    
    if success_count > 0:
        print(f"\n🎉 Successfully updated {success_count} photo URLs to optimized versions!")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)