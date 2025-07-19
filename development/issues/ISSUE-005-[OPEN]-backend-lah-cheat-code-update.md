# ISSUE-005: Update 'lah' Cheat Code Registration Code

**Priority**: Medium  
**Type**: Configuration  
**Component**: Backend - Testing/Development Tools  
**Created**: 2025-01-17  
**Status**: Open  

## Executive Summary

The 'lah' cheat code used for testing purposes currently hardcodes a registration code with 'u9' age group, but needs to be updated to 'u10' to reflect the correct testing scenario.

## Current Implementation

The 'lah' cheat code functionality:
- Injects pre-filled test data into chat conversation history
- Currently uses registration code: `200-leopards-u9-2526`
- Provides quick way to test registration flows without manual data entry

## Problems Identified

1. **Incorrect Age Group**: The hardcoded registration code uses 'u9' instead of 'u10'
2. **Testing Accuracy**: Tests may not reflect correct age-based routing and validation
3. **Potential Confusion**: Developers testing with 'lah' code get wrong age group

## Proposed Solution

1. **Locate Cheat Code Implementation**:
   ```bash
   # Search for the 'lah' cheat code
   grep -r "lah" backend/
   grep -r "200-leopards-u9-2526" backend/
   ```

2. **Update Registration Code**:
   ```python
   # Change from:
   registration_code = "200-leopards-u9-2526"
   
   # To:
   registration_code = "200-leopards-u10-2526"
   ```

3. **Verify All References**:
   - Check if code appears in multiple locations
   - Update all instances consistently
   - Ensure no hardcoded age-based logic depends on u9

## Implementation Checklist

- [ ] Search for 'lah' cheat code implementation in backend
- [ ] Locate all instances of `200-leopards-u9-2526`
- [ ] Update to `200-leopards-u10-2526`
- [ ] Test 'lah' cheat code functionality
- [ ] Verify age-based routing works correctly with u10
- [ ] Check for any dependent test scripts
- [ ] Update any documentation referencing the old code

## Testing Instructions

1. Start the backend server:
   ```bash
   cd backend
   uvicorn server:app --reload --port 8000
   ```

2. Test the 'lah' cheat code:
   - Open chat interface
   - Enter 'lah'
   - Verify injected data includes `200-leopards-u10-2526`
   - Confirm registration flow proceeds with u10 age group

3. Expected outcomes:
   - Cheat code injects correct u10 registration code
   - Age-based validation accepts u10 players
   - Kit sizing and other age-dependent features work correctly

## Additional Context

- The 'lah' cheat code is a development/testing feature
- May be located in:
  - Backend routing logic
  - Test utilities
  - Development helper functions
- Ensure change doesn't affect production code
- Consider documenting other available cheat codes if found