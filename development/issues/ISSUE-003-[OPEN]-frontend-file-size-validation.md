# ISSUE-003: Frontend File Size Validation Not Working

**Status**: OPEN  
**Priority**: Medium  
**Component**: Frontend - Photo Upload  
**Assigned**: Unassigned  
**Created**: 2025-07-16  

## Problem Description

The frontend file size validation for photo uploads is not working correctly. Users can upload files larger than the 10MB limit, which then get rejected by the backend infrastructure with a "413 Request Entity Too Large" error.

## Current Behavior

1. User selects a large file (e.g., 19MB)
2. Frontend validation should show alert: "File size must be less than 10MB"
3. **BUG**: Validation is bypassed and file reaches backend
4. Backend/infrastructure rejects with 413 error
5. User sees confusing error instead of helpful validation message

## Expected Behavior

1. User selects a large file (e.g., 19MB)
2. Frontend validation immediately shows: "File size must be less than 10MB"
3. Upload is prevented from starting
4. User can select a smaller file and try again

## Technical Details

### Frontend Validation Code
Location: `frontend/web/src/app/chat/_components/chat-input.tsx:63-67`

```typescript
const maxSize = 10 * 1024 * 1024; // 10MB
if (file.size > maxSize) {
    alert('File size must be less than 10MB');
    return;
}
```

### Test Case
- **File**: stefan.jpg (19MB)
- **Expected**: Frontend validation alert
- **Actual**: File reaches backend, 413 error returned

## Root Cause Investigation Needed

1. **File.size property**: Verify if `file.size` is being read correctly
2. **Alert visibility**: Check if alert is shown but user misses it
3. **Validation bypass**: Investigate if there's a code path that skips validation
4. **Browser compatibility**: Test across different browsers

## Proposed Solution

1. **Improve validation feedback**:
   - Replace `alert()` with better UI feedback
   - Add file size display before upload
   - Show validation errors in chat interface

2. **Add debugging**:
   - Log file size to console during validation
   - Add visual feedback for validation state

3. **Enhanced UX**:
   - Show file size in MB when selected
   - Add progress indicator that shows size validation
   - Better error messaging

## Implementation Plan

### Phase 1: Fix Current Validation
- [ ] Debug why 19MB file bypassed validation
- [ ] Add console logging to track validation flow
- [ ] Ensure validation always triggers for large files

### Phase 2: Improve User Experience  
- [ ] Replace alert() with in-chat error messages
- [ ] Add file size display in UI
- [ ] Show validation status before upload starts

### Phase 3: Testing
- [ ] Test with files at various sizes (5MB, 10MB, 15MB, 20MB)
- [ ] Cross-browser testing
- [ ] Mobile device testing

## Test Cases

| File Size | Expected Behavior | Status |
|-----------|------------------|---------|
| 5MB | Upload succeeds | ✅ Working |
| 10MB | Upload succeeds | ✅ Working |
| 15MB | Frontend validation blocks | ❌ Broken |
| 20MB | Frontend validation blocks | ❌ Broken |

## Infrastructure Notes

- Backend/infrastructure correctly rejects large files with 413 error
- 10MB limit is appropriate for photo uploads
- Frontend validation is the correct place to handle this
- No backend changes needed

## Dependencies

- No external dependencies
- Frontend-only changes required
- No deployment needed (frontend static files)

## Definition of Done

- [ ] Files >10MB are blocked at frontend with clear error message
- [ ] No large files reach backend (no more 413 errors)
- [ ] User-friendly validation feedback in chat interface
- [ ] Cross-browser compatibility verified
- [ ] Mobile compatibility verified

## Related Issues

- Related to photo upload functionality
- May impact registration flow UX
- Consider for mobile optimization

---

**Notes**: This issue was discovered during testing of the restart chat feature deployment. The photo upload functionality works correctly for appropriately sized files, but the frontend validation needs to be more robust.