"""
SMS Metrics Queue - SQLite Implementation

Provides thread-safe queuing for SMS delivery metrics to avoid race conditions
with database writes. SMS metrics are cached locally and flushed to Airtable
in the background.
"""

import sqlite3
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_ID = "tbl1D7hdjVcyHbT8a"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# Queue database path
QUEUE_DB_PATH = Path(__file__).parent / "sms_metrics_queue.db"


class SMSMetricsQueue:
    """SQLite-based queue for SMS delivery metrics"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or QUEUE_DB_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sms_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    billing_request_id TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            ''')
            
            # Index for efficient querying
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_billing_request 
                ON sms_metrics(billing_request_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed 
                ON sms_metrics(processed, created_at)
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def add_sms_metrics(self, billing_request_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Add SMS metrics to the queue for later processing
        
        Args:
            billing_request_id: GoCardless billing request ID
            metrics: SMS delivery metrics dict
            
        Returns:
            bool: True if added successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                # Add timestamp to metrics
                metrics['queued_at'] = datetime.utcnow().isoformat() + 'Z'
                
                conn.execute('''
                    INSERT INTO sms_metrics (billing_request_id, metrics_json)
                    VALUES (?, ?)
                ''', (billing_request_id, json.dumps(metrics)))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Failed to queue SMS metrics: {e}")
            return False
    
    def get_pending_metrics(self, limit: int = 50) -> list:
        """
        Get unprocessed SMS metrics from the queue
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            list: List of pending metrics records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute('''
                    SELECT id, billing_request_id, metrics_json, retry_count
                    FROM sms_metrics 
                    WHERE processed = FALSE 
                    AND retry_count < 3
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (limit,))
                
                return cursor.fetchall()
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Failed to fetch pending metrics: {e}")
            return []
    
    def mark_processed(self, record_id: int) -> bool:
        """Mark a metrics record as successfully processed"""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute('''
                    UPDATE sms_metrics 
                    SET processed = TRUE, last_error = NULL
                    WHERE id = ?
                ''', (record_id,))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Failed to mark record as processed: {e}")
            return False
    
    def mark_retry(self, record_id: int, error_msg: str) -> bool:
        """Mark a metrics record for retry with error message"""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute('''
                    UPDATE sms_metrics 
                    SET retry_count = retry_count + 1, last_error = ?
                    WHERE id = ?
                ''', (error_msg, record_id))
                
                conn.commit()
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Failed to mark record for retry: {e}")
            return False
    
    def cleanup_old_records(self, days: int = 7) -> int:
        """
        Clean up processed records older than specified days
        
        Args:
            days: Number of days to keep processed records
            
        Returns:
            int: Number of records cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute('''
                    DELETE FROM sms_metrics 
                    WHERE processed = TRUE 
                    AND created_at < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"🧹 Cleaned up {deleted_count} old SMS metrics records")
                
                return deleted_count
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"❌ Failed to cleanup old records: {e}")
            return 0


class SMSMetricsProcessor:
    """Background processor for flushing SMS metrics to Airtable"""
    
    def __init__(self, queue: SMSMetricsQueue):
        self.queue = queue
        self.api = Api(AIRTABLE_API_KEY) if AIRTABLE_API_KEY else None
        self.table = self.api.table(BASE_ID, TABLE_ID) if self.api else None
        self.running = False
    
    async def start_processing(self, interval_seconds: int = 30):
        """
        Start the background processing loop
        
        Args:
            interval_seconds: How often to process the queue
        """
        if not self.table:
            print("⚠️ SMS metrics processor disabled - no Airtable API key")
            return
        
        self.running = True
        print(f"🚀 SMS metrics processor started (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                await self.process_batch()
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                print(f"❌ SMS metrics processor error: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    def stop_processing(self):
        """Stop the background processing loop"""
        self.running = False
        print("🛑 SMS metrics processor stopped")
    
    async def process_batch(self):
        """Process a batch of pending SMS metrics"""
        pending_records = self.queue.get_pending_metrics()
        
        if not pending_records:
            return  # Nothing to process
        
        print(f"📊 Processing {len(pending_records)} SMS metrics records")
        
        for record_id, billing_request_id, metrics_json, retry_count in pending_records:
            try:
                # Parse metrics
                metrics = json.loads(metrics_json)
                
                # Find Airtable record by billing_request_id
                airtable_record = await self.find_registration_record(billing_request_id)
                
                if airtable_record:
                    # Update the record with SMS metrics
                    await self.update_sms_fields(airtable_record['id'], metrics)
                    
                    # Mark as processed
                    self.queue.mark_processed(record_id)
                    print(f"✅ Updated SMS metrics for {billing_request_id}")
                    
                else:
                    # Record not found - might not be created yet
                    error_msg = f"Registration record not found for {billing_request_id}"
                    self.queue.mark_retry(record_id, error_msg)
                    print(f"⏳ Record not found, will retry: {billing_request_id}")
                
            except Exception as e:
                error_msg = f"Error processing {billing_request_id}: {str(e)}"
                self.queue.mark_retry(record_id, error_msg)
                print(f"❌ {error_msg}")
    
    async def find_registration_record(self, billing_request_id: str) -> Optional[Dict]:
        """Find registration record by billing_request_id"""
        try:
            # Search for record with matching billing_request_id
            records = self.table.all(formula=f"{{billing_request_id}} = '{billing_request_id}'")
            
            if records:
                return records[0]  # Return first match
            
            return None
            
        except Exception as e:
            print(f"❌ Error searching for record {billing_request_id}: {e}")
            return None
    
    async def update_sms_fields(self, record_id: str, metrics: Dict[str, Any]):
        """Update SMS fields in Airtable record"""
        try:
            update_data = {}
            
            # Map metrics to Airtable fields
            if 'sms_sent_at' in metrics:
                update_data['sms_sent_at'] = metrics['sms_sent_at']
            
            if 'sms_delivery_status' in metrics:
                update_data['sms_delivery_status'] = metrics['sms_delivery_status']
            
            if 'sms_delivery_error' in metrics:
                update_data['sms_delivery_error'] = metrics['sms_delivery_error']
            
            # Only update if we have data
            if update_data:
                self.table.update(record_id, update_data)
            
        except Exception as e:
            raise Exception(f"Failed to update Airtable record: {e}")


# Global instances
_sms_queue = None
_sms_processor = None


def get_sms_queue() -> SMSMetricsQueue:
    """Get the global SMS metrics queue instance"""
    global _sms_queue
    if _sms_queue is None:
        _sms_queue = SMSMetricsQueue()
    return _sms_queue


async def start_sms_processor(interval_seconds: int = 30):
    """Start the global SMS metrics processor"""
    global _sms_processor
    if _sms_processor is None:
        queue = get_sms_queue()
        _sms_processor = SMSMetricsProcessor(queue)
    
    await _sms_processor.start_processing(interval_seconds)


def stop_sms_processor():
    """Stop the global SMS metrics processor"""
    global _sms_processor
    if _sms_processor:
        _sms_processor.stop_processing()


# Convenience function for SMS tools
def queue_sms_metrics(billing_request_id: str, metrics: Dict[str, Any]) -> bool:
    """
    Queue SMS metrics for background processing
    
    Args:
        billing_request_id: GoCardless billing request ID
        metrics: SMS delivery metrics
        
    Returns:
        bool: True if queued successfully
    """
    queue = get_sms_queue()
    return queue.add_sms_metrics(billing_request_id, metrics) 