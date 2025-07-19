#!/usr/bin/env python3
"""
Direct script to update id_image_link URLs from original photos to optimized versions.
Uses direct Airtable API calls instead of the agent system.
"""

import os
import sys
import re
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"  # Use table ID instead of name

if not AIRTABLE_API_KEY:
    print("❌ AIRTABLE_API_KEY not found in environment variables")
    sys.exit(1)

def get_records_with_photos() -> List[Dict[str, Any]]:
    """Get all records that have photo URLs in id_image_link field."""
    print("🔍 Querying records with photo URLs...")
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_ID}"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Filter for records that have a value in id_image_link field
    params = {
        "filterByFormula": "NOT({id_image_link} = '')",
        "fields": ["id_image_link", "player_full_name", "team", "age_group"]
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get('records', [])
        
        print(f"   ✅ Found {len(records)} records with photos")
        
        # Format records for easier processing
        formatted_records = []
        for record in records:
            record_id = record['id']
            fields = record['fields']
            
            formatted_record = {
                'record_id': record_id,
                'player_name': fields.get('player_full_name', 'Unknown'),
                'team': fields.get('team', 'Unknown'),
                'age_group': fields.get('age_group', 'Unknown'),
                'id_image_link': fields.get('id_image_link', '')
            }
            formatted_records.append(formatted_record)
            
        return formatted_records
        
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
    
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_ID}/{record_id}"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "fields": {
            "id_image_link": new_url
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"   ✅ Successfully updated {player_name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to update {player_name}: {e}")
        return False

def main():
    print("🚀 UTJFC Photo URL Update Script (Direct API)")
    print("=" * 50)
    
    # Step 1: Get all records with photos
    records = get_records_with_photos()
    
    if not records:
        print("📭 No records with photos found")
        return 0
    
    print(f"\n📋 Found {len(records)} records to potentially update")
    print("=" * 60)
    
    # Show current records first
    print("\n📊 CURRENT RECORDS:")
    for i, record in enumerate(records, 1):
        player_name = record['player_name']
        current_url = record['id_image_link']
        print(f"{i:2d}. {player_name}: {current_url}")
    
    # Automatically proceed since this was requested
    print(f"\n✅ Proceeding to update these {len(records)} records to use optimized photo URLs...")
    
    print("\n" + "=" * 60)
    print("🔄 STARTING UPDATES")
    print("=" * 60)
    
    # Step 2: Process each record
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    for i, record in enumerate(records, 1):
        try:
            record_id = record['record_id']
            player_name = record['player_name']
            current_url = record['id_image_link']
            
            print(f"\n🎯 Record {i}/{len(records)}: {player_name}")
            print(f"   Current URL: {current_url}")
            
            # Convert URL to optimized version
            optimized_url = convert_url_to_optimized(current_url)
            
            if optimized_url == current_url:
                print(f"   ⏭️  No change needed (already optimized or invalid URL)")
                skipped_count += 1
                continue
            
            if '_optimized' in current_url:
                print(f"   ⏭️  Already using optimized URL")
                skipped_count += 1
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
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("=" * 60)
    print(f"✅ Successful updates: {success_count}")
    print(f"❌ Failed updates: {failure_count}")
    print(f"⏭️  Skipped (no change needed): {skipped_count}")
    print(f"📷 Total processed: {success_count + failure_count + skipped_count}")
    
    if success_count > 0:
        print(f"\n🎉 Successfully updated {success_count} photo URLs to optimized versions!")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)