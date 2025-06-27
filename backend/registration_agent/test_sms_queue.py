#!/usr/bin/env python3
"""
Test SMS Metrics Queue System

Simple test to verify SQLite queue and background processor work correctly.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registration_tools.sms_metrics_queue import (
    SMSMetricsQueue, 
    SMSMetricsProcessor, 
    queue_sms_metrics
)


async def test_sms_queue():
    """Test the SMS metrics queue system"""
    
    print("🧪 Testing SMS Metrics Queue System")
    print("=" * 50)
    
    # Test 1: Queue metrics
    print("\n1. Testing metric queuing...")
    
    test_metrics = {
        'sms_sent_at': datetime.utcnow().isoformat() + 'Z',
        'sms_delivery_status': 'sent',
        'sms_delivery_error': '',
        'twilio_message_sid': 'SM_test_123456',
        'formatted_phone': '+447835065013',
        'child_name': 'Test Child'
    }
    
    billing_request_id = "BRQ_TEST_12345"
    
    success = queue_sms_metrics(billing_request_id, test_metrics)
    if success:
        print("✅ Successfully queued SMS metrics")
    else:
        print("❌ Failed to queue SMS metrics")
        return
    
    # Test 2: Check queue contents
    print("\n2. Testing queue retrieval...")
    
    queue = SMSMetricsQueue()
    pending = queue.get_pending_metrics()
    
    print(f"📊 Found {len(pending)} pending metrics in queue")
    
    if pending:
        for record in pending:
            record_id, billing_id, metrics_json, retry_count = record
            print(f"   - Record ID: {record_id}")
            print(f"   - Billing ID: {billing_id}")
            print(f"   - Retry count: {retry_count}")
    
    # Test 3: Process metrics (mock processor)
    print("\n3. Testing background processor (mock mode)...")
    
    # Create processor but don't start full processing (would need Airtable)
    processor = SMSMetricsProcessor(queue)
    
    print("📝 Created SMS metrics processor")
    print("   Note: Skipping actual Airtable processing in test mode")
    
    # Test 4: Mark as processed
    if pending:
        record_id = pending[0][0]
        print(f"\n4. Testing mark as processed for record {record_id}...")
        
        success = queue.mark_processed(record_id)
        if success:
            print("✅ Successfully marked record as processed")
        else:
            print("❌ Failed to mark record as processed")
        
        # Check queue again
        pending_after = queue.get_pending_metrics()
        print(f"📊 Pending metrics after processing: {len(pending_after)}")
    
    # Test 5: Cleanup
    print("\n5. Testing cleanup...")
    
    cleanup_count = queue.cleanup_old_records(days=0)  # Clean up everything
    print(f"🧹 Cleaned up {cleanup_count} records")
    
    print("\n✅ SMS Queue System Test Completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_sms_queue()) 