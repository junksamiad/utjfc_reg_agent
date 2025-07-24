# Adult Self-Registration System

**Feature ID**: `adult-self-registration`  
**Status**: Planning  
**Priority**: High  
**Estimated Effort**: 3-5 days  
**Dependencies**: 
- Current registration system (registration_agent)
- Airtable database with adult player support
- Payment processing (GoCardless)
- SMS notification system (Twilio)
**Implementation Date**: TBD  
**Implemented By**: TBD  
**Branch**: TBD  

---

## Overview

Currently, the UTJFC registration system is designed for parents registering their children. This feature will implement a parallel adult self-registration flow that allows adult players (18+) to register themselves for adult teams like the Mens Open team. The system will reuse much of the existing infrastructure while removing parent-child relationship logic and simplifying the workflow.

## Business Requirements

### Problem Statement
- Adult players currently cannot self-register through the chatbot
- The existing system assumes a parent-child relationship that doesn't apply to adult teams
- Adult registration requires different data collection (no parent info, direct contact details)
- Mens team and other adult teams need automated registration like youth teams

### Success Criteria
- Adult players can successfully register themselves using registration codes (e.g., `200-mens-open-2526`)
- Registration flow skips parent-related questions and goes directly to player information
- Adult players provide their own contact details and consent
- Payment setup works directly with the adult player
- System correctly identifies and routes adult registration codes

### User Stories
1. **As an adult player**, I want to register myself for the Mens team without being asked about parent/child relationships
2. **As a club administrator**, I want adult registrations to be processed the same way as youth registrations for consistency
3. **As an adult player**, I want to provide my own contact details and payment information directly

## Technical Changes Required

### Code Locations to Update

#### 1. Registration Code Detection in server.py
- **Current**: Lines 1210-1255 handle new registration routing
- **Location**: `server.py` around line 1210
- **Change**: Add detection for adult team codes (e.g., "mens") and route differently

#### 2. Initial Welcome Message 
- **Current**: Lines 1224-1241 contain hardcoded parent-focused message:
  - "I'm here to help you register your child..."
  - "Can I take your first and last name so I know how to refer to you?"
- **New**: Add conditional logic to show adult-focused message for adult teams:
  - "I'm here to help you register for the **Mens Open Age** team this season."
  - "Can I take your first and last name for your registration?"

#### 3. Add Adult Routines to registration_routines.py
- **Location**: `/backend/registration_agent/registration_routines.py`
- **Add**: New routines starting from routine_number 100
- **Content**: Adult-specific workflow steps

#### 4. Adult Registration Workflow (routines 100+)
```
Routine 100: Collect player name (self-registration)
Routine 101: Check if existing registration (with adult-specific resume logic)
Routine 102: Date of birth (validate 18+ years old)
Routine 103: Gender
Routine 104: Medical conditions
Routine 105: Previous season check
Routine 106: Mobile phone (player's own)
Routine 107: Email address (player's own)
Routine 108: Communication consent (direct from player)
Routine 109: Postcode
Routine 110: House number + address lookup
Routine 111: Manual address entry (if lookup fails)
Routine 112: Address confirmation
Routine 113: Summary confirmation
Routine 114: Payment setup (direct with player)
Routine 115: Kit selection
Routine 116: Photo upload (of themselves)
Routine 117: Completion message
```

#### 5. Routing Logic Updates
- **Location**: `server.py` line ~1210 in new_registration section
- **Add**: Check if team is adult team (e.g., "mens"), then:
  - Set different welcome message
  - Route to routine_number 100 instead of 1
- **Keep**: All within existing `registration_agent` module

#### 6. Response Handler Updates
- **Location**: `/backend/registration_agent/responses_reg.py`
- **Ensure**: Response handlers recognize routine numbers 100+ 
- **May need**: Updates to handle adult-specific routine transitions

### Database Considerations
- Airtable schema already supports adult players
- Ensure "Age group" field accepts values like "Mens Open"
- Parent-related fields will be left empty for adult registrations

### API Changes
- No new endpoints required
- Existing `/chat` endpoint will handle adult registration
- Same `last_agent: "new_registration"` but with routine_number 100+

### Frontend Changes
- No frontend changes required
- System will detect adult codes and route appropriately

## Implementation Notes

### Architecture Considerations
1. **Same Agent System**: Use existing registration_agent with new routines
2. **Routine Number Range**: Adult routines start at 100 to separate from youth flow
3. **Tool Sharing**: Adult routines can use all existing tools
4. **Session Management**: Use same session history system

### Security Considerations
- Age validation critical - must be 18+ (born 2007 or earlier for 2025 season)
- Direct consent from adult player (not parent)
- Payment authorization directly from player

### Performance Considerations
- Similar performance profile to existing registration
- Fewer steps should mean faster completion

### Integration Points
1. **Orchestrator Agent**: Detect adult registration codes
2. **Airtable**: Store adult player data
3. **GoCardless**: Direct debit setup
4. **Twilio**: SMS to adult player
5. **S3**: Photo upload

## Testing Strategy

### Unit Testing
- Adult code detection (`200-mens-open-2526`)
- Age validation (must be 18+)
- Workflow routing (skip parent steps)

### Integration Testing
- Full adult registration flow
- Payment setup for adult
- Photo upload
- Database storage

### Manual Testing
1. Enter adult registration code
2. Complete self-registration
3. Verify data in Airtable
4. Test payment link
5. Upload photo

### Edge Cases
- Player under 18 trying adult registration
- Existing player re-registering
- Invalid adult team codes
- Address lookup failures

## Risk Assessment

### Risk Level: Medium

### Potential Issues
1. Confusion between youth and adult registration flows
2. Age validation bypass attempts
3. Missing adult team configurations
4. Payment processing differences for adults

### Mitigation
1. Clear error messages for wrong registration type
2. Strict age validation at multiple points
3. Pre-configure all adult teams in system
4. Use same payment flow as youth

### Rollback Plan
- Feature can be disabled by removing adult code detection
- Existing youth registration unaffected
- Manual registration fallback available

## Deployment

### Changes Required
1. Deploy new `adults_registration_agent/` module
2. Update orchestrator agent instructions
3. Configure adult team codes in system
4. Test in staging environment

### Environment Variables
- No new environment variables required
- Use existing Airtable, GoCardless, Twilio configs

### Migration Steps
1. Add adult team entries to Airtable if not present
2. Deploy code with adult agent
3. Test with sample adult registration
4. Enable for production

### Verification Steps
1. Test adult code recognition
2. Complete full adult registration
3. Verify Airtable entry created
4. Confirm payment link sent
5. Check photo upload works

## Future Considerations

### Extensibility
- Support for other adult teams (Ladies, Vets)
- Age-group specific workflows (U21, U23)
- Different payment structures for adults

### Maintenance
- Keep adult workflow in sync with youth improvements
- Monitor for adult-specific issues
- Regular testing of age validation

### Related Features
- Family discount detection (adult with children)
- Coach registration workflow
- Volunteer registration system

## Implementation Approach

### Recommended Approach: Add Adult Routines
1. **Add routines 100-117** to existing `registration_routines.py`
2. **Modify server.py** to detect adult team codes and route to routine 100
3. **Create adult-specific welcome message** in server.py
4. **Test thoroughly** with `200-mens-open-2526` code

### Why This Approach?
- Minimal code changes required
- Leverages existing infrastructure
- Easy to maintain alongside youth registration
- Clear separation via routine number ranges

### Key Implementation Steps
1. **Detect Adult Team**: Check if team name is "mens" (or other adult teams)
2. **Set Initial Routine**: Start at routine 100 instead of routine 1
3. **Different Welcome**: Show adult-appropriate welcome message
4. **Age Validation**: Ensure player is 18+ in routine 102
5. **Direct Flow**: No parent/child relationship questions

### Key Differences from Youth Registration
1. **No parent information** - player registers themselves
2. **Direct contact details** - player's own phone/email
3. **Age validation** - must be 18+ years old
4. **Routine numbers** - 100+ instead of 1-35
5. **Welcome message** - addresses player directly, not parent

## Example Registration Code
```
200-mens-open-2526
```

Where:
- `200` = New registration prefix
- `mens` = Team identifier (adult team)
- `open` = Category (open age)
- `2526` = Season (2025-26)