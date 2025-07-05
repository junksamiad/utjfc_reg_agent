# UTJFC Photo Upload Test Scripts

## 🧪 Main Test Script

**`test_photo_upload.py`** - Comprehensive test for routine 34 (photo upload step)

### Usage:
```bash
cd /Users/leehayton/Cursor\ Projects/utjfc_reg_agent

# Standard test (API + timer logic simulation)
python3 test_photo_upload.py

# With browser UI validation (experimental)
python3 test_photo_upload.py --browser
```

### What it tests:
- ✅ Async upload endpoint (`/upload-async`)
- ✅ Immediate response with processing flag
- ✅ Polling workflow (`/upload-status/{session_id}`)
- ✅ Timer logic simulation (validates timing/duration)
- ✅ Final success response
- ✅ S3 photo upload verification
- ✅ Automatic cleanup of test photos
- 🧪 Browser UI validation (experimental)

### Expected Output:
```
=== UTJFC Photo Upload Test Suite ===
✅ Verify test image exists PASSED
✅ Test async upload endpoint PASSED  
✅ Test polling workflow PASSED
✅ Test frontend timer logic PASSED
✅ Verify S3 upload PASSED
🎉 ALL TESTS PASSED! Async photo upload is working correctly.
Results: 17/17 tests passed

📊 Timer Logic Validation:
- Timer starts: 0.9s after upload
- Timer duration: 9.4 seconds total
- Timer shows: 0.0s → 3.1s → 6.2s → 9.3s → stops
✅ Timer duration is reasonable for user to see
```

### ⏱️ **Timer Behavior (Frontend UI)**:
When you test in the browser, you should see:
1. **Immediate response**: "📸 Photo received! Processing your registration..." with typing animation
2. **Timer appears**: Shows elapsed time (X.Xs) immediately after typing completes
3. **Timer continues**: Keeps running throughout entire polling phase (13+ seconds)
4. **Processing indicator**: Shows "Processing..." alongside timer
5. **Timer stops**: When final success message appears

---

## 🧹 Cleanup Script

**`cleanup_test_photos.py`** - Manual cleanup of photos from S3

### Usage:
```bash
# List all photos
python3 cleanup_test_photos.py

# Delete photos matching pattern
python3 cleanup_test_photos.py test
python3 cleanup_test_photos.py "specific_filename"
```

### Safety Features:
- Shows all files before deletion
- Requires confirmation (y/N)
- Only deletes files matching your pattern
- Safe interactive deletion process

---

## 📁 Test Files

- **`test_photo.jpg`** - Test image for upload testing (1.9MB)
- **S3 Bucket**: `utjfc-player-photos`
- **AWS Profile**: `footballclub`

---

## 🔧 Configuration

Both scripts use these settings:
- **API Base**: `https://d1ahgtos8kkd8y.cloudfront.net/api`
- **Test Routine**: 34 (photo upload step)
- **Polling**: Every 3 seconds, max 2 minutes
- **AWS Profile**: `footballclub`

---

## 🎯 Test Validation

The test script validates:

1. **Frontend UI Response**:
   - Immediate "📸 Photo received!" message
   - Processing flag set to `true`
   - Timer shows elapsed time during polling

2. **Backend Processing**:
   - Async upload endpoint works
   - Background AI processing completes
   - Photo uploaded to S3 successfully

3. **Polling Workflow**:
   - Status endpoint responds correctly
   - Progress tracking works
   - Final success message delivered

4. **No Timeout Errors**:
   - Complete workflow finishes in ~10-15 seconds
   - No 504 Gateway Timeout errors
   - Seamless user experience

---

## 🚀 Quick Test Run

```bash
# Run the full test
./test_photo_upload.py

# If you see any test failures, check:
# 1. Backend is running (v1.6.8-fix)
# 2. Frontend is deployed with timer fixes
# 3. AWS CLI is configured with 'footballclub' profile
```

---

**Result**: No more manual testing needed! 🎉