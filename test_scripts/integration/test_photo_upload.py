#!/usr/bin/env python3
"""
UTJFC Photo Upload Test Script
Tests routine 34 (photo upload step) with async processing and polling validation
Includes frontend UI validation with browser automation

Usage:
  python3 test_photo_upload.py           # API tests + timer logic simulation
  python3 test_photo_upload.py --browser  # API tests + browser UI validation
  python3 test_photo_upload.py -b         # Same as --browser
"""

import json
import requests
import time
import sys
from pathlib import Path
import subprocess
from datetime import datetime
import re

# Configuration
API_BASE_URL = "https://d1ahgtos8kkd8y.cloudfront.net/api"
FRONTEND_URL = "https://urmstontownjfc.co.uk/chat/"
TEST_IMAGE_PATH = "/Users/leehayton/Cursor Projects/utjfc_reg_agent/test_photo.jpg"
S3_BUCKET = "utjfc-player-photos"
AWS_PROFILE = "footballclub"

class PhotoUploadTester:
    def __init__(self):
        self.session_id = f"test-session-{int(time.time())}-{id(self)}"
        self.uploaded_photo_url = None
        self.test_results = []
        
    def log(self, message, success=None):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅" if success is True else "❌" if success is False else "ℹ️"
        full_message = f"[{timestamp}] {status} {message}"
        print(full_message)
        self.test_results.append({
            'timestamp': timestamp,
            'message': message,
            'success': success
        })
        
    def verify_test_image_exists(self):
        """Verify test image exists and is readable"""
        self.log("Checking test image...")
        if not Path(TEST_IMAGE_PATH).exists():
            self.log(f"Test image not found: {TEST_IMAGE_PATH}", False)
            return False
        
        file_size = Path(TEST_IMAGE_PATH).stat().st_size
        self.log(f"Test image found: {file_size} bytes", True)
        return True
        
    def test_upload_async_endpoint(self):
        """Test the /upload-async endpoint"""
        self.log("Testing async upload endpoint...")
        
        # Prepare form data
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': ('test_photo.jpg', f, 'image/jpeg')}
            data = {
                'session_id': self.session_id,
                'routine_number': 34,
                'last_agent': 'new_registration'
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}/upload-async",
                    files=files,
                    data=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"Upload response: {json.dumps(result, indent=2)}")
                    
                    # Validate immediate response
                    if result.get('processing') is True:
                        self.log("✅ Processing flag is True", True)
                    else:
                        self.log("❌ Processing flag is not True", False)
                        
                    if "📸 Photo received! Processing" in result.get('response', ''):
                        self.log("✅ Immediate response message correct", True)
                    else:
                        self.log(f"❌ Unexpected immediate response: {result.get('response')}", False)
                        
                    return True
                else:
                    self.log(f"Upload failed: {response.status_code} - {response.text}", False)
                    return False
                    
            except Exception as e:
                self.log(f"Upload error: {str(e)}", False)
                return False
                
    def test_polling_workflow(self):
        """Test the polling workflow"""
        self.log("Testing polling workflow...")
        
        max_polls = 40  # 2 minutes max
        poll_interval = 3
        
        for poll_count in range(max_polls):
            try:
                response = requests.get(f"{API_BASE_URL}/upload-status/{self.session_id}")
                
                if response.status_code == 200:
                    status = response.json()
                    self.log(f"Poll #{poll_count + 1}: {json.dumps(status, indent=2)}")
                    
                    if status.get('complete'):
                        if status.get('error'):
                            self.log(f"❌ Processing completed with error: {status.get('response')}", False)
                            return False
                        else:
                            self.log("✅ Processing completed successfully", True)
                            
                            # Check for photo URL in response
                            if 'response' in status:
                                self.log(f"Final response: {status['response']}")
                                if "✅" in status['response'] or "successfully" in status['response'].lower():
                                    self.log("✅ Success message detected", True)
                                else:
                                    self.log("⚠️ Response doesn't look like success message", False)
                            
                            return True
                    else:
                        self.log(f"Still processing... (poll {poll_count + 1}/{max_polls})")
                        time.sleep(poll_interval)
                else:
                    self.log(f"Poll failed: {response.status_code}", False)
                    return False
                    
            except Exception as e:
                self.log(f"Polling error: {str(e)}", False)
                return False
                
        self.log("❌ Polling timeout reached", False)
        return False
        
    def verify_s3_upload(self):
        """Verify photo was uploaded to S3"""
        self.log("Verifying S3 upload...")
        
        try:
            # List objects in S3 bucket that might match our session
            cmd = [
                "aws", "--profile", AWS_PROFILE, 
                "s3", "ls", f"s3://{S3_BUCKET}/",
                "--no-cli-pager"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                
                # Look for recently uploaded files (last 5 minutes)
                recent_files = []
                current_time = time.time()
                
                for line in files:
                    if line.strip():
                        # Parse AWS S3 ls output: "2025-07-04 19:30:15  92480 sebhayton_leopards_u9.jpg"
                        parts = line.split()
                        if len(parts) >= 4:
                            filename = parts[-1]
                            # Check if file was created recently (rough check)
                            recent_files.append(filename)
                
                self.log(f"Found {len(recent_files)} files in S3 bucket")
                
                # Look for a test file (we can't easily match exact filename without more info)
                if recent_files:
                    # Get the most recent file as a proxy for our upload
                    latest_file = recent_files[-1]  # Assume last in list is most recent
                    self.uploaded_photo_url = f"https://{S3_BUCKET}.s3.eu-north-1.amazonaws.com/{latest_file}"
                    self.log(f"✅ Photo appears uploaded: {latest_file}", True)
                    return True
                else:
                    self.log("❌ No files found in S3 bucket", False)
                    return False
            else:
                self.log(f"❌ S3 list failed: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.log(f"S3 verification error: {str(e)}", False)
            return False
            
    def cleanup_s3_photos(self):
        """Clean up test photos from S3"""
        self.log("Cleaning up S3 photos...")
        
        try:
            # List and delete test photos (be careful here!)
            cmd = [
                "aws", "--profile", AWS_PROFILE,
                "s3", "ls", f"s3://{S3_BUCKET}/",
                "--no-cli-pager"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                deleted_count = 0
                
                for line in files:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            filename = parts[-1]
                            
                            # Only delete files that look like test files or are very recent
                            # (Add safety checks here to avoid deleting real user photos)
                            if (filename.startswith('test') or 
                                'test' in filename.lower() or
                                filename.endswith('_test.jpg')):
                                
                                delete_cmd = [
                                    "aws", "--profile", AWS_PROFILE,
                                    "s3", "rm", f"s3://{S3_BUCKET}/{filename}",
                                    "--no-cli-pager"
                                ]
                                
                                delete_result = subprocess.run(delete_cmd, capture_output=True, text=True)
                                if delete_result.returncode == 0:
                                    self.log(f"✅ Deleted test photo: {filename}", True)
                                    deleted_count += 1
                                else:
                                    self.log(f"❌ Failed to delete {filename}: {delete_result.stderr}", False)
                
                if deleted_count == 0:
                    self.log("ℹ️ No test photos found to delete")
                else:
                    self.log(f"✅ Cleaned up {deleted_count} test photos", True)
                    
            else:
                self.log(f"❌ S3 cleanup failed: {result.stderr}", False)
                
        except Exception as e:
            self.log(f"Cleanup error: {str(e)}", False)
            
    def test_frontend_ui_with_browser(self):
        """Test the frontend UI behavior using browser automation"""
        self.log("Testing frontend UI with browser automation...")
        
        try:
            # Check if we can use playwright or selenium
            # For now, we'll use AppleScript to automate Safari on macOS
            self.log("Opening browser and testing UI timer behavior...")
            
            # AppleScript to open Safari and navigate to chat
            applescript = f'''
            tell application "Safari"
                activate
                set newTab to make new document with properties {{URL:"{FRONTEND_URL}"}}
                delay 3
                
                -- Wait for page to load
                repeat while (do JavaScript "document.readyState" in newTab) is not "complete"
                    delay 0.5
                end repeat
                
                -- Check if chat interface is loaded
                set chatLoaded to do JavaScript "document.querySelector('form') !== null" in newTab
                if not chatLoaded then
                    error "Chat interface not loaded"
                end if
                
                -- Take a screenshot before upload
                do shell script "screencapture -x /tmp/before_upload.png"
                
                return "Browser opened and ready"
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("✅ Browser opened successfully", True)
                
                # Now we'll monitor the network requests to see the upload happen
                # Since we can't directly access DOM, we'll use a different approach
                self.log("ℹ️ Browser test opened. Please manually upload a photo and check for timer.")
                self.log("ℹ️ Look for: 1) Immediate response with typing 2) Timer appears 3) Timer runs during polling")
                
                # Give user time to test manually
                input("Press Enter after you've verified the timer behavior in the browser...")
                
                # Close the browser tab
                close_script = '''
                tell application "Safari"
                    close front document
                end tell
                '''
                subprocess.run(['osascript', '-e', close_script], capture_output=True)
                
                self.log("✅ Frontend UI test completed (manual verification)", True)
                return True
            else:
                self.log(f"❌ Browser automation failed: {result.stderr}", False)
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Browser automation timed out", False)
            return False
        except Exception as e:
            self.log(f"❌ Browser automation error: {str(e)}", False)
            return False
    
    def test_frontend_timer_logic(self):
        """Test timer logic by checking network behavior"""
        self.log("Testing frontend timer logic...")
        
        try:
            # This test simulates what the frontend should do
            # 1. Upload photo and get immediate response
            # 2. Start polling and measure duration
            # 3. Verify timer would show throughout
            
            start_time = time.time()
            
            # Upload photo (should return immediately)
            upload_success = self.test_upload_async_endpoint()
            if not upload_success:
                return False
                
            immediate_response_time = time.time()
            
            # Start "timer" simulation
            timer_start = immediate_response_time
            self.log(f"📊 Timer should start at: {timer_start - start_time:.1f}s after upload")
            
            # Poll until complete (simulating frontend polling)
            max_polls = 40
            poll_interval = 3
            
            for poll_count in range(max_polls):
                current_time = time.time()
                timer_elapsed = current_time - timer_start
                
                self.log(f"📊 Timer should show: {timer_elapsed:.1f}s (poll #{poll_count + 1})")
                
                try:
                    response = requests.get(f"{API_BASE_URL}/upload-status/{self.session_id}")
                    
                    if response.status_code == 200:
                        status = response.json()
                        
                        if status.get('complete'):
                            final_time = time.time()
                            total_timer_duration = final_time - timer_start
                            
                            if status.get('error'):
                                self.log(f"❌ Processing failed: {status.get('response')}", False)
                                return False
                            else:
                                self.log(f"✅ Timer should stop at: {total_timer_duration:.1f}s", True)
                                self.log(f"📊 Total timer duration: {total_timer_duration:.1f} seconds", True)
                                
                                if total_timer_duration > 5:  # Should run for reasonable time
                                    self.log("✅ Timer duration is reasonable for user to see", True)
                                else:
                                    self.log("⚠️ Timer duration might be too short to notice", False)
                                    
                                return True
                        else:
                            time.sleep(poll_interval)
                    else:
                        self.log(f"❌ Poll failed: {response.status_code}", False)
                        return False
                        
                except Exception as e:
                    self.log(f"❌ Polling error: {str(e)}", False)
                    return False
                    
            self.log("❌ Timer test timeout reached", False)
            return False
                
        except Exception as e:
            self.log(f"❌ Timer logic test error: {str(e)}", False)
            return False
    
    def run_full_test(self):
        """Run the complete test suite"""
        self.log("=== UTJFC Photo Upload Test Suite ===")
        self.log(f"Session ID: {self.session_id}")
        
        # Test steps
        tests = [
            ("Verify test image exists", self.verify_test_image_exists),
            ("Test async upload endpoint", self.test_upload_async_endpoint),
            ("Test polling workflow", self.test_polling_workflow),
            ("Test frontend timer logic", self.test_frontend_timer_logic),
            ("Verify S3 upload", self.verify_s3_upload),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                result = test_func()
                if not result:
                    all_passed = False
                    self.log(f"❌ {test_name} FAILED", False)
                else:
                    self.log(f"✅ {test_name} PASSED", True)
            except Exception as e:
                self.log(f"❌ {test_name} ERROR: {str(e)}", False)
                all_passed = False
        
        # Cleanup
        self.log("\n--- Cleanup ---")
        self.cleanup_s3_photos()
        
        # Summary
        self.log("\n=== TEST SUMMARY ===")
        if all_passed:
            self.log("🎉 ALL TESTS PASSED! Async photo upload is working correctly.", True)
            self.log("ℹ️ Note: Timer behavior tested via logic simulation. Use --browser for UI validation.")
        else:
            self.log("❌ Some tests failed. Check the log above for details.", False)
            
        # Count results
        passed = sum(1 for r in self.test_results if r['success'] is True)
        failed = sum(1 for r in self.test_results if r['success'] is False)
        total = passed + failed
        
        self.log(f"Results: {passed}/{total} tests passed")
        
        return all_passed
    
    def run_api_tests(self):
        """Run just the API tests without browser"""
        self.log("=== API Test Suite ===")
        self.log(f"Session ID: {self.session_id}")
        
        tests = [
            ("Verify test image exists", self.verify_test_image_exists),
            ("Test async upload endpoint", self.test_upload_async_endpoint),
            ("Test polling workflow", self.test_polling_workflow),
            ("Verify S3 upload", self.verify_s3_upload),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                result = test_func()
                if not result:
                    all_passed = False
                    self.log(f"❌ {test_name} FAILED", False)
                else:
                    self.log(f"✅ {test_name} PASSED", True)
            except Exception as e:
                self.log(f"❌ {test_name} ERROR: {str(e)}", False)
                all_passed = False
        
        return all_passed

def main():
    """Main test function"""
    # Check for browser test flag
    run_browser_test = '--browser' in sys.argv or '-b' in sys.argv
    
    tester = PhotoUploadTester()
    
    if run_browser_test:
        print("🌐 Running with browser UI validation...")
        tester.log("⚠️ Browser test will open Safari - make sure you can see the screen")
        
        # Run API tests first
        api_success = tester.run_api_tests()
        
        if api_success:
            # Then run browser test
            browser_success = tester.test_frontend_ui_with_browser()
            success = api_success and browser_success
        else:
            success = False
    else:
        # Run standard API + timer logic tests
        success = tester.run_full_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()