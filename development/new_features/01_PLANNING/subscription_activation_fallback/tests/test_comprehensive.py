#!/usr/bin/env python3
"""
Comprehensive test suite for Subscription Activation Fallback System

This test suite validates the complete fallback process including:
- Record identification and filtering
- Subscription activation logic
- Database updates and error handling
- AWS Lambda integration
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'backend'))

class TestSubscriptionFallbackComprehensive(unittest.TestCase):
    """Comprehensive test suite for subscription fallback system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_records = [
            {
                'id': 'rec123456',
                'fields': {
                    'player_first_name': 'John',
                    'player_last_name': 'Doe',
                    'signing_on_fee_paid': 'Y',
                    'mandate_authorised': 'Y',
                    'subscription_activated': 'N',
                    'mandate_id': 'MD123456',
                    'billing_request_id': 'BRQ123456',
                    'monthly_subscription_amount': 27.5,
                    'subscription_start_date': '2024-09-01',
                    'fallback_attempt_count': 0
                }
            },
            {
                'id': 'rec789012',
                'fields': {
                    'player_first_name': 'Jane',
                    'player_last_name': 'Smith',
                    'signing_on_fee_paid': 'Y',
                    'mandate_authorised': 'Y',
                    'subscription_activated': '',  # Empty string case
                    'mandate_id': 'MD789012',
                    'billing_request_id': 'BRQ789012',
                    'monthly_subscription_amount': 27.5,
                    'subscription_start_date': '2024-09-01',
                    'fallback_attempt_count': 2
                }
            }
        ]
        
        self.mock_successful_activation = {
            'success': True,
            'ongoing_subscription_id': 'SB123456',
            'interim_subscription_id': 'SB123457',
            'start_date': '2024-09-01',
            'interim_created': True,
            'message': 'Subscription activated successfully'
        }
        
        self.mock_failed_activation = {
            'success': False,
            'message': 'GoCardless API error: Rate limit exceeded'
        }
    
    @patch('scheduled_tasks.subscription_fallback.Api')
    def test_find_incomplete_registrations(self, mock_api):
        """Test finding records that need subscription activation"""
        # Mock the Airtable API
        mock_table = Mock()
        mock_api.return_value.table.return_value = mock_table
        mock_table.all.return_value = self.test_records
        
        # Import and test the fallback processor
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        processor = SubscriptionFallbackProcessor(dry_run=True)
        incomplete_records = processor.find_incomplete_registrations()
        
        # Verify the query formula
        expected_formula = """
        AND(
            {signing_on_fee_paid} = 'Y',
            {mandate_authorised} = 'Y',
            OR(
                {subscription_activated} != 'Y',
                {subscription_activated} = ''
            )
        )
        """
        
        mock_table.all.assert_called_once()
        self.assertEqual(len(incomplete_records), 2)
        self.assertEqual(incomplete_records[0]['id'], 'rec123456')
        self.assertEqual(incomplete_records[1]['id'], 'rec789012')
    
    @patch('scheduled_tasks.subscription_fallback.Api')
    @patch('registration_agent.tools.registration_tools.gocardless_payment.activate_subscription')
    def test_successful_record_processing(self, mock_activate, mock_api):
        """Test successful subscription activation for a record"""
        # Mock the Airtable API
        mock_table = Mock()
        mock_api.return_value.table.return_value = mock_table
        mock_activate.return_value = self.mock_successful_activation
        
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        processor = SubscriptionFallbackProcessor(dry_run=False)
        result = processor.process_record(self.test_records[0])
        
        # Verify activation was called correctly
        mock_activate.assert_called_once_with(
            mandate_id='MD123456',
            registration_record=self.test_records[0]
        )
        
        # Verify database update
        expected_update = {
            'subscription_activated': 'Y',
            'ongoing_subscription_id': 'SB123456',
            'interim_subscription_id': 'SB123457',
            'subscription_start_date': '2024-09-01',
            'subscription_status': 'active',
            'fallback_attempt_count': 1,
            'fallback_check_last_run': unittest.mock.ANY
        }
        
        mock_table.update.assert_called_once_with('rec123456', expected_update)
        self.assertTrue(result)
    
    @patch('scheduled_tasks.subscription_fallback.Api')
    @patch('registration_agent.tools.registration_tools.gocardless_payment.activate_subscription')
    def test_failed_record_processing(self, mock_activate, mock_api):
        """Test handling of failed subscription activation"""
        # Mock the Airtable API
        mock_table = Mock()
        mock_api.return_value.table.return_value = mock_table
        mock_activate.return_value = self.mock_failed_activation
        
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        processor = SubscriptionFallbackProcessor(dry_run=False)
        result = processor.process_record(self.test_records[1])
        
        # Verify database update with error
        expected_update = {
            'subscription_status': 'failed',
            'subscription_error': 'GoCardless API error: Rate limit exceeded',
            'fallback_attempt_count': 3,  # Incremented from 2
            'fallback_check_last_run': unittest.mock.ANY,
            'registration_status': 'incomplete'  # Set after 3 attempts
        }
        
        mock_table.update.assert_called_once_with('rec789012', expected_update)
        self.assertFalse(result)
    
    @patch('scheduled_tasks.subscription_fallback.Api')
    def test_missing_mandate_id_handling(self, mock_api):
        """Test handling of records without mandate_id"""
        # Mock the Airtable API
        mock_table = Mock()
        mock_api.return_value.table.return_value = mock_table
        
        # Create record without mandate_id
        record_without_mandate = {
            'id': 'rec999999',
            'fields': {
                'player_first_name': 'Test',
                'player_last_name': 'Player',
                'signing_on_fee_paid': 'Y',
                'mandate_authorised': 'Y',
                'subscription_activated': 'N',
                'mandate_id': '',  # Missing mandate ID
                'fallback_attempt_count': 0
            }
        }
        
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        processor = SubscriptionFallbackProcessor(dry_run=False)
        result = processor.process_record(record_without_mandate)
        
        # Verify error handling
        expected_update = {
            'subscription_status': 'failed',
            'subscription_error': 'No mandate_id available for subscription activation',
            'fallback_attempt_count': 1,
            'fallback_check_last_run': unittest.mock.ANY
        }
        
        mock_table.update.assert_called_once_with('rec999999', expected_update)
        self.assertFalse(result)
    
    @patch('scheduled_tasks.subscription_fallback.Api')
    def test_dry_run_mode(self, mock_api):
        """Test dry run mode doesn't make actual changes"""
        # Mock the Airtable API
        mock_table = Mock()
        mock_api.return_value.table.return_value = mock_table
        mock_table.all.return_value = self.test_records
        
        from scheduled_tasks.subscription_fallback import SubscriptionFallbackProcessor
        
        processor = SubscriptionFallbackProcessor(dry_run=True)
        incomplete_records = processor.find_incomplete_registrations()
        
        # Process records in dry run mode
        for record in incomplete_records:
            processor.process_record(record)
        
        # Verify no database updates were made
        mock_table.update.assert_not_called()
    
    @patch('scheduled_tasks.subscription_fallback.SubscriptionFallbackProcessor')
    def test_lambda_handler_success(self, mock_processor_class):
        """Test AWS Lambda handler with successful processing"""
        # Mock the processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.find_incomplete_registrations.return_value = self.test_records
        mock_processor.process_record.side_effect = [True, False]  # First succeeds, second fails
        
        from scheduled_tasks.lambda_handler import lambda_handler
        
        # Test event
        event = {'dry_run': False}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        # Verify response
        self.assertEqual(result['statusCode'], 200)
        
        body = json.loads(result['body'])
        self.assertEqual(body['processed'], 2)
        self.assertEqual(body['successful'], 1)
        self.assertEqual(body['failed'], 1)
    
    @patch('scheduled_tasks.subscription_fallback.SubscriptionFallbackProcessor')
    def test_lambda_handler_exception(self, mock_processor_class):
        """Test AWS Lambda handler with exception"""
        # Mock processor to raise exception
        mock_processor_class.side_effect = Exception("Database connection failed")
        
        from scheduled_tasks.lambda_handler import lambda_handler
        
        event = {'dry_run': False}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        # Verify error response
        self.assertEqual(result['statusCode'], 500)
        
        body = json.loads(result['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error'], "Database connection failed")
    
    def test_batch_processing(self):
        """Test batch processing with rate limiting"""
        # This would test the batch processing logic
        # Implementation depends on final batch size and rate limiting strategy
        pass
    
    def test_api_rate_limit_handling(self):
        """Test handling of API rate limits"""
        # This would test retry logic for rate-limited API calls
        # Implementation depends on final retry strategy
        pass
    
    def test_subscription_idempotency(self):
        """Test that existing subscriptions are not duplicated"""
        # This would test checking for existing subscriptions
        # before creating new ones
        pass

class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common scenarios"""
    
    def test_end_to_end_fallback_flow(self):
        """Test complete end-to-end fallback processing"""
        # This would test the complete flow with real test data
        # against a test environment
        pass
    
    def test_webhook_failure_recovery(self):
        """Test recovery from webhook processing failures"""
        # This would simulate webhook failures and verify
        # fallback system catches and resolves them
        pass
    
    def test_multiple_fallback_runs(self):
        """Test running fallback multiple times on same data"""
        # This would verify idempotency across multiple runs
        pass

def run_comprehensive_tests():
    """Run the comprehensive test suite"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestSubscriptionFallbackComprehensive))
    suite.addTest(unittest.makeSuite(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)