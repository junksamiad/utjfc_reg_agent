# Registration Resume After Disconnection

**Feature ID**: `registration-resume-after-disconnection`  
**Status**: Implemented - Ready for Deployment  
**Priority**: High  
**Estimated Effort**: 1-2 days  
**Dependencies**: Existing registration workflow, Airtable database, check_if_kit_needed function  

---

## Overview

Allow users who accidentally disconnect during registration (especially at the payment SMS step) to resume their registration by re-entering their registration code. The system will detect existing registrations and route them to either kit selection or photo upload based on their previous season participation and kit requirements.

## Business Requirements

### Problem Statement
Currently, up to 50% of parents disconnect from the chat during the payment SMS step (routine 30) due to:
- **Mobile UI Issues**: Accidentally swiping up and closing the browser tab
- **User Confusion**: Not understanding they need to return to the chat after checking SMS
- **No Resume Option**: Users must start the entire 35-step registration process from the beginning
- **Data Loss**: All previously entered information is lost, requiring complete re-entry
- **Registration Abandonment**: Users become frustrated and don't complete registration

### Success Criteria
- **Reduced Abandonment**: Decrease 50% disconnection rate at payment SMS step
- **Seamless Resume**: Users can re-enter registration code and skip directly to kit selection or photo upload
- **Data Preservation**: No need to re-enter previously collected information
- **Smart Routing**: System routes to kit selection or photo upload based on previous season participation and kit requirements
- **No Workflow Disruption**: Existing registration instructions remain unchanged
- **Improved Completion**: Higher registration completion rates

### User Stories
- **As a parent who accidentally closed the chat tab after receiving payment SMS**, I want to re-enter my registration code and skip to the remaining steps
- **As a mobile user**, I want to be able to return to my registration without losing all my progress
- **As a parent checking SMS**, I want to easily return to the chat without starting over
- **As a club administrator**, I want fewer incomplete registrations due to accidental disconnections

---

## Technical Changes Required

### Code Locations Updated

#### Backend Registration Routines
- **File**: `backend/registration_agent/registration_routines.py`
  - **Routine 2**: Modified step 5 to check for existing records
  - **Added steps 6-8**: New logic for returning users based on previous season status

#### New Tool Creation
- **File**: `backend/registration_agent/tools/registration_tools/check_if_record_exists_in_db.py` (NEW)
  - Core function to search existing registrations by player and parent names
  - Returns existing record or indicates no match found
- **File**: `backend/registration_agent/tools/registration_tools/check_if_record_exists_in_db_tool.py` (NEW)
  - OpenAI tool definition and handler wrapper

#### Tool Registry Updates
- **File**: `backend/registration_agent/tools/registration_tools/__init__.py`
  - Added new tool to the registration tools export list
- **File**: `backend/registration_agent/registration_agents.py`
  - Added new tool to the registration agent's available tools
- **File**: `backend/registration_agent/agents_reg.py`
  - Added new tool to both tool definitions and function handlers

### Database Considerations
- **Existing Table**: `registrations_2526` (no schema changes needed)
- **Search Fields**: `player_full_name`, `parent_full_name` (exact matching only)
- **Resume Logic**: Based on `played_for_urmston_town_last_season` field + `check_if_kit_needed` function
- **Assumption**: Users accessing this feature have already completed payment setup and have existing records

### API Changes
- **No new endpoints required** - uses existing chat flow
- **Enhanced Logic**: Routine 2 now branches based on database lookup
- **Existing Tools**: Leverages current `check_if_kit_needed` function

### Frontend Changes
- **No changes required** - uses existing chat interface
- **Same User Flow**: User enters registration code as normal
- **Transparent Resume**: System handles routing automatically

---

## Implementation Notes

### ⚠️ CRITICAL REQUIREMENT: NO ROUTINE WORDING CHANGES
**IMPORTANT**: Do NOT change any existing routine wording beyond what is specified in this document. The current prompts work well and only the specific modifications outlined below should be implemented.

### Architecture Considerations
- **Minimal Changes**: Leverage existing registration flow with small modifications
- **Database Integration**: Use existing Airtable connection and search capabilities
- **Name Matching**: Ensure proper capitalization matching as used in database storage
- **Existing Tools**: Reuse current `check_if_kit_needed` function without modification

### New Function Requirements: `check_if_record_exists_in_db`

#### Function Specifications
```python
def check_if_record_exists_in_db(**kwargs) -> Dict[str, Any]:
    """
    Search for existing registration record by player and parent names.
    
    This function searches the registrations_2526 table for existing records
    matching the provided player and parent names exactly.
    
    Args:
        player_full_name (str): Child's full name - MUST be properly capitalized
        parent_full_name (str): Parent's full name - MUST be properly capitalized
        
    Returns:
        dict: {
            "success": bool,
            "record_found": bool,
            "record": dict or None,
            "message": str
        }
    """
```

### Routing Logic Implementation
**Exact modifications to Routine 2 (Step 5 only):**

**Current Step 5:**
```
5) if valid, set routine_number = 3 and ask for their child's date of birth.
```

**New Step 5:**
```
5) if valid, call function check_if_record_exists_in_db which will see if this is a returning user or not. If they are not a returning user (ie a record match IS NOT returned) then set routine_number = 3 and ask for their child's date of birth.
```

**New Steps 6-8:**
```
6) in the returned record, check the value of the field 'played_for_urmston_town_last_season'. If the value is 'N', set routine_number = 32, then ask them to choose a kit size for their child. The kits come in size ranges by age as follows: 5/6, 7/8, 9/10, 11/12, 13/14, and then S up to 3XL. Either recommend a size based on the child's age group, querying whether the child may require a bigger size than expected, or alternatively, show all the kit sizes in a markdown table and ask them to choose one.

7) If the 'played_for_urmston_town_last_season' value is 'Y', then call the function check_if_kit_needed to see whether their team is due a new kit. If the result returned = 'N', then set routine = 34 and explain that next they need to upload a passport-style photo for ID purposes by clicking the + symbol in the chat window and uploading a file.

8) If the result returned from the check_if_kit_needed function = 'Y', then, set routine_number = 32, then ask them to choose a kit size for their child. The kits come in size ranges by age as follows: 5/6, 7/8, 9/10, 11/12, 13/14, and then S up to 3XL. Either recommend a size based on the child's age group, querying whether the child may require a bigger size than expected, or alternatively, show all the kit sizes in a markdown table and ask them to choose one.
```

### Security Considerations
- **Data Validation**: Ensure proper input validation for name matching
- **Database Access**: Use existing Airtable security patterns
- **Name Capitalization**: Maintain consistency with database storage format

---

## Testing Strategy

### Unit Testing
- **Database Search Function**: Test `check_if_record_exists_in_db` with various name combinations
- **Name Normalization**: Test capitalization and formatting consistency
- **Routing Logic**: Test routine 2 branching based on different scenarios
- **Kit Decision Logic**: Test integration with existing `check_if_kit_needed` function

### Integration Testing
- **End-to-End Resume**: Test complete flow from registration code re-entry to correct routine
- **Database Matching**: Test name matching accuracy with real database records
- **Kit Routing**: Test both kit-needed and no-kit-needed paths
- **Cross-Agent Communication**: Test data sharing between orchestrator and registration agents

### Manual Testing
1. **Basic Resume**: Enter registration code, provide names, verify correct routing
2. **Kit Path Testing**: Test both "Y" and "N" values for `played_for_urmston_town_last_season`
3. **Name Variations**: Test with different name capitalizations and formats
4. **No Match Scenario**: Test when no existing record is found (new user path)
5. **Routine Progression**: Verify correct routine numbers are set for each path
6. **Kit Size Selection**: Test routine 32 kit size selection interface

### Edge Cases
- **No Record Found**: User enters registration code but no existing record exists (proceed to routine 3)
- **Database Unavailable**: Handle Airtable API failures gracefully (fallback to routine 3)
- **Mixed Case Names**: Test name matching with various capitalizations
- **Kit Function Failures**: Handle `check_if_kit_needed` function failures gracefully

---

## Risk Assessment

**Risk Level**: Low

### Potential Issues
- **Name Matching Accuracy**: Risk of false negatives if name capitalization differs
- **Database Performance**: Additional database queries could slow routine 2
- **User Confusion**: Users might not understand why they're skipping to kit selection or photo upload
- **Function Dependencies**: Risk if `check_if_kit_needed` function fails or returns unexpected results

### Mitigation
- **Conservative Matching**: Use exact name matching to avoid false positives
- **Clear Messaging**: Provide clear explanation when user is detected as returning
- **Database Optimization**: Ensure queries are efficient and properly indexed
- **Testing Strategy**: Extensive testing with real names and data variations
- **Fallback Mechanism**: Always allow progression to routine 3 if lookup fails

### Rollback Plan
- **Simple Revert**: Remove steps 5-8 from routine 2, restore original step 5
- **Database Cleanup**: Remove new tool from registrations if needed
- **Agent Restoration**: Restore original agent tool lists
- **No Data Loss**: No existing data affected by rollback

---

## Deployment

### Changes Required
1. **Backend Tool Creation**: Deploy new `check_if_record_exists_in_db` function
2. **Routine Modification**: Update routine 2 with new logic steps
3. **Tool Registration**: Add new tool to agent configurations
4. **Testing**: Verify resume functionality works correctly

### Environment Variables
```bash
# No new environment variables required
# Uses existing Airtable configuration
```

### Migration Steps
1. Deploy new tool function to registration_tools directory
2. Update routine 2 logic in registration_routines.py
3. Add tool to agent configurations and __init__.py
4. Test functionality in staging environment
5. Deploy to production via standard deployment process

### Verification Steps
1. **Tool Registration**: Verify new tool appears in agent tool lists
2. **Routine Logic**: Test routine 2 branching with test registration codes
3. **Database Queries**: Confirm queries execute correctly and return expected results
4. **Resume Flow**: Test complete resume scenario from start to finish
5. **Performance Check**: Verify no significant performance impact

---

## Future Considerations

### Extensibility
- **Advanced Matching**: Implement fuzzy name matching for better accuracy
- **Progress Tracking**: Show users their completion percentage when resuming
- **Resume Tokens**: Generate unique resume tokens for better security
- **Multi-Session Support**: Allow users to have multiple active registrations

### Maintenance
- **Query Optimization**: Monitor database query performance and optimize as needed
- **Match Analytics**: Track accuracy of name matching and resume success rates
- **User Feedback**: Collect feedback on resume experience quality
- **Error Monitoring**: Monitor for resume failures and improve matching logic

### Related Features
- **Admin Resume Tools**: Admin interface to help users resume registrations
- **Progress Indicators**: Visual progress bar showing registration completion
- **Notification System**: Email/SMS notifications for incomplete registrations
- **Batch Resume**: Allow admins to help multiple users resume at once

---

## Implementation Details

### Implementation Summary
The restart chat feature has been successfully implemented with the following components:

**Files Created:**
1. `backend/registration_agent/tools/registration_tools/check_if_record_exists_in_db.py` - Core function logic
2. `backend/registration_agent/tools/registration_tools/check_if_record_exists_in_db_tool.py` - OpenAI tool definition and handler

**Files Modified:**
1. `backend/registration_agent/registration_routines.py` - Updated routine 2 with new steps 5-8
2. `backend/registration_agent/tools/registration_tools/__init__.py` - Added new tool imports
3. `backend/registration_agent/agents_reg.py` - Added tool to available tools and handlers
4. `backend/registration_agent/registration_agents.py` - Added tool to new_registration_agent

**Testing:**
- Comprehensive test suite created in `development/new_features/restart_chat_if_disconnected/tests/`
- All tests passing with real database records
- Ready for deployment

### Notes
- Implementation follows established codebase patterns
- Uses exact name matching for database lookups
- Maintains backward compatibility for new users
- No database schema changes required
- Minimal performance impact expected

---

*This feature has been implemented and is ready for deployment.*