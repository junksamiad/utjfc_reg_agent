# Extend Kit Number Range (1-49)

**Feature ID**: `extend-kit-number-range`  
**Status**: Implemented  
**Priority**: Low  
**Estimated Effort**: 2-3 hours  
**Dependencies**: None  
**Implementation Date**: 2025-07-15  
**Implemented By**: Claude Code  
**Branch**: `feature/extend-kit-number`  

---

## Overview

Extend the shirt number selection range from the current limit of 1-25 to 1-49 to provide more kit number options for players during the registration process.

## Business Requirements

### Problem Statement
Currently, players can only select shirt numbers between 1-25 during registration. This limitation may cause issues when:
- Teams have more than 25 players
- Players want higher numbers for personal preference
- Squad numbers need to accommodate larger team sizes

### Success Criteria
- Players can select any shirt number from 1-49 during registration
- Existing validation logic continues to prevent duplicate numbers within teams
- No breaking changes to existing registrations with numbers 1-25

---

## Technical Changes Required

### Code Locations to Update

#### 1. Registration Tools Validation
**File**: `backend/registration_agent/tools/registration_tools/check_shirt_number_availability_tool.py`
- Update maximum number validation from 25 to 49

#### 2. Agent Instructions/Routines
**File**: `backend/registration_agent/registration_routines.py`
- Update user-facing text that mentions "1-25" to "1-49"

#### 3. Tool Schema Definitions
**Files to check**:
- Any Pydantic models with shirt number validation
- OpenAI function schemas that define shirt number parameters
- Database field validation (if any constraints exist)

### Database Considerations
- **Airtable Field**: `shirt_number` field should already support integers up to 49
- **Validation**: Existing availability checking logic should work unchanged
- **Data Migration**: No migration needed (existing numbers 1-25 remain valid)

---

## Implementation Notes

### Frontend Considerations
- Check if frontend has any hardcoded validation for 1-25 range
- Update any user interface text that mentions the number range

### Validation Logic
- Ensure duplicate checking still works correctly for the expanded range
- Maintain existing goalkeeper number logic (typically numbers 1 and 12)

### Testing Required
- Test shirt number selection with numbers 26-49
- Verify duplicate detection works across full range
- Confirm existing registrations with numbers 1-25 are unaffected

---

## Risk Assessment

**Risk Level**: Very Low

**Potential Issues**:
- None identified - this is a simple range extension
- Existing duplicate checking logic should handle larger numbers
- No database schema changes required

**Mitigation**:
- Test thoroughly with numbers 26-49 before production deployment
- Verify no hardcoded limits exist elsewhere in the system

---

## Testing Strategy

### Manual Testing
1. Start a new registration
2. Reach shirt number selection step
3. Verify user can select numbers 1-49
4. Test duplicate detection with numbers >25
5. Complete registration with number >25

### Edge Cases
- Select number 49 (maximum)
- Select number 26 (first new number)
- Try to select number already taken in range 26-49

---

## Deployment

### Changes Required
1. Update validation constraints from 25 to 49
2. Update user-facing text/instructions
3. Deploy and test

### Rollback Plan
- Simple: revert validation back to 25 if issues arise
- No data corruption risk as this only expands allowed values

---

## Future Considerations

- Monitor usage patterns to see if numbers >25 are actually used
- Consider if upper limit of 49 is sufficient long-term
- Could potentially expand further to 99 if needed in future

---

## Implementation Details

### Implementation Summary
Successfully extended the shirt number range from 1-25 to 1-49 across all relevant backend components. The implementation was completed on 2025-07-15 on branch `feature/extend-kit-number`.

### Files Modified (4 files)

#### 1. `backend/registration_agent/tools/registration_tools/check_shirt_number_availability_tool.py`
- Updated function parameter validation to accept 1-49 range
- Modified error messages to reflect new range
- Updated OpenAI function schema maximum value
- Changed AI instruction text for alternative number suggestions

#### 2. `backend/registration_agent/registration_routines.py`
- Updated Routine 32: Changed user-facing instruction text from "1 to 25" to "1 to 49"
- Updated Routine 33: Modified validation messages in multiple places to reflect new range

#### 3. `backend/registration_agent/tools/registration_tools/registration_data_models.py`
- Updated Pydantic model for `shirt_number` field to accept values up to 49
- Modified field description to indicate new range

#### 4. `backend/registration_agent/tools/registration_tools/update_kit_details_to_db_tool.py`
- Updated Pydantic model validation for shirt numbers
- Modified OpenAI function schema to accept up to 49
- Updated goalkeeper logic comments to reflect extended range

### Testing Recommendations
1. Test shirt number selection with values 26-49
2. Verify duplicate detection works for extended range
3. Confirm goalkeeper logic still works (numbers 1 and 12)
4. Test edge cases: number 26 (first new), number 49 (maximum)
5. Verify existing registrations with numbers 1-25 unaffected

### Notes
- No database changes required - Airtable already supports the extended range
- No frontend changes needed - no hardcoded validation found
- All validation is server-side ensuring consistency
- Implementation maintains backward compatibility