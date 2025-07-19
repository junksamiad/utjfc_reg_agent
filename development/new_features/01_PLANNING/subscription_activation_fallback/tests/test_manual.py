#!/usr/bin/env python3
"""
Manual testing utility for Subscription Activation Fallback System

This script provides interactive testing capabilities for developers
to manually test the fallback system with real data.
"""

import sys
import os
import argparse
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend'))

def main():
    """Main entry point for manual testing"""
    parser = argparse.ArgumentParser(description='Manual testing for subscription fallback system')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--record-id', type=str, help='Test specific record ID')
    parser.add_argument('--show-records', action='store_true', help='Show incomplete records without processing')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    
    args = parser.parse_args()
    
    print("🔄 Subscription Activation Fallback - Manual Testing")
    print("=" * 60)
    
    try:
        # Import fallback processor
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        # Initialize processor
        processor = SubscriptionFallbackProcessor(dry_run=args.dry_run)
        
        if args.dry_run:
            print("⚠️  DRY RUN MODE: No actual changes will be made")
        else:
            print("🔴 LIVE MODE: Changes will be made to the database")
            
        print()
        
        # Find incomplete registrations
        print("🔍 Finding incomplete registrations...")
        incomplete_records = processor.find_incomplete_registrations()
        
        print(f"Found {len(incomplete_records)} incomplete registrations")
        
        if not incomplete_records:
            print("✅ No incomplete registrations found!")
            return
        
        # Show records if requested
        if args.show_records:
            show_incomplete_records(incomplete_records)
            return
        
        # Process specific record if requested
        if args.record_id:
            process_specific_record(processor, incomplete_records, args.record_id)
            return
        
        # Process all records
        process_all_records(processor, incomplete_records, args.batch_size)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def show_incomplete_records(records):
    """Display incomplete records in a formatted table"""
    print("\n📋 Incomplete Registrations:")
    print("-" * 80)
    
    for i, record in enumerate(records, 1):
        fields = record['fields']
        player_name = f"{fields.get('player_first_name', 'Unknown')} {fields.get('player_last_name', '')}"
        
        print(f"{i:2d}. {player_name:<25} | ID: {record['id']}")
        print(f"    Payment: {fields.get('signing_on_fee_paid', 'N'):<3} | "
              f"Mandate: {fields.get('mandate_authorised', 'N'):<3} | "
              f"Subscription: {fields.get('subscription_activated', 'N'):<3}")
        print(f"    Mandate ID: {fields.get('mandate_id', 'Missing')}")
        print(f"    Attempts: {fields.get('fallback_attempt_count', 0)}")
        
        if fields.get('fallback_last_error'):
            print(f"    Last Error: {fields.get('fallback_last_error')}")
        
        print()

def process_specific_record(processor, records, record_id):
    """Process a specific record by ID"""
    # Find the record
    target_record = None
    for record in records:
        if record['id'] == record_id:
            target_record = record
            break
    
    if not target_record:
        print(f"❌ Record {record_id} not found in incomplete registrations")
        return
    
    fields = target_record['fields']
    player_name = f"{fields.get('player_first_name', 'Unknown')} {fields.get('player_last_name', '')}"
    
    print(f"\n🎯 Processing specific record: {player_name} ({record_id})")
    print("-" * 60)
    
    # Show record details
    print(f"Player: {player_name}")
    print(f"Payment Status: {fields.get('signing_on_fee_paid', 'N')}")
    print(f"Mandate Status: {fields.get('mandate_authorised', 'N')}")
    print(f"Subscription Status: {fields.get('subscription_activated', 'N')}")
    print(f"Mandate ID: {fields.get('mandate_id', 'Missing')}")
    print(f"Previous Attempts: {fields.get('fallback_attempt_count', 0)}")
    
    if fields.get('fallback_last_error'):
        print(f"Last Error: {fields.get('fallback_last_error')}")
    
    print()
    
    # Process the record
    success = processor.process_record(target_record)
    
    if success:
        print(f"✅ Successfully processed {player_name}")
    else:
        print(f"❌ Failed to process {player_name}")

def process_all_records(processor, records, batch_size):
    """Process all incomplete records in batches"""
    print(f"\n🔄 Processing {len(records)} records in batches of {batch_size}")
    print("-" * 60)
    
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n📦 Processing batch {batch_num} ({len(batch)} records)...")
        
        for record in batch:
            fields = record['fields']
            player_name = f"{fields.get('player_first_name', 'Unknown')} {fields.get('player_last_name', '')}"
            
            print(f"  Processing: {player_name:<25} ", end="")
            
            results['processed'] += 1
            
            try:
                success = processor.process_record(record)
                
                if success:
                    print("✅ SUCCESS")
                    results['successful'] += 1
                else:
                    print("❌ FAILED")
                    results['failed'] += 1
                    
            except Exception as e:
                print(f"💥 ERROR: {str(e)}")
                results['failed'] += 1
                results['errors'].append(f"{player_name}: {str(e)}")
        
        # Show batch results
        print(f"  Batch {batch_num} complete: {len(batch)} processed")
        
        # Add delay between batches (except for last batch)
        if i + batch_size < len(records):
            print("  ⏳ Waiting 2 seconds before next batch...")
            import time
            time.sleep(2)
    
    # Show final results
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total Processed: {results['processed']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['successful'] / results['processed'] * 100):.1f}%")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")

def test_lambda_handler():
    """Test the Lambda handler locally"""
    print("\n🐍 Testing Lambda Handler")
    print("-" * 40)
    
    try:
        from scheduled_tasks.lambda_handler import lambda_handler
        
        # Test event
        event = {
            'dry_run': True
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = 'test-function'
                self.function_version = '1'
                self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
                self.memory_limit_in_mb = 128
                self.remaining_time_in_millis = lambda: 30000
        
        context = MockContext()
        
        # Execute handler
        result = lambda_handler(event, context)
        
        print(f"Status Code: {result['statusCode']}")
        print(f"Response Body: {result['body']}")
        
        if result['statusCode'] == 200:
            print("✅ Lambda handler test successful")
        else:
            print("❌ Lambda handler test failed")
            
    except Exception as e:
        print(f"❌ Lambda handler test error: {str(e)}")

if __name__ == '__main__':
    main()