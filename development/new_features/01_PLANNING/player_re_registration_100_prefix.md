# Player Re-Registration System (100-Prefix Codes)

**Feature ID**: `player-re-registration-100-prefix`  
**Status**: Planning  
**Priority**: High  
**Estimated Effort**: 2-3 days  
**Dependencies**: 
- Airtable players24_25 table (last season's data)
- Airtable registrations_2526 table (current season)
- Existing payment and kit functions from new registration flow
**Implementation Date**: TBD  
**Implemented By**: TBD  
**Branch**: TBD  

---

## Overview

Currently, the 100-prefix re-registration system has minimal implementation - it routes to a `re_registration_agent` that only spells the player's name backwards as a test. This feature will implement proper re-registration allowing parents to quickly re-register their children who played last season, by pulling their data from the players24_25 table and copying it to the new season after verification.

## Current System Behavior

### What Happens Now with 100-Prefix Codes:
1. **Code Format**: `100-[TEAM]-[AGE_GROUP]-[SEASON]-[FIRST_NAME]-[SURNAME]`
   - Example: `100-tigers-u13-2526-jack-grealish`
2. **Validation**: Code is validated in `routing_validation.py`
3. **Routing**: Routes to `re_registration_agent` (server.py line 1165)
4. **Current Agent Behavior**: 
   - Instructions: "spell the player's name backwards and tell the user you are the RE-REGISTRATION AGENT"
   - This is clearly a placeholder for testing

## Business Requirements

### Problem Statement
- Parents with children who played last season need a quick way to re-register
- The current 100-prefix system is not implemented properly
- Parents shouldn't have to re-enter all details for returning players
- Need to validate the parent has the right to re-register that child

### Success Criteria
- Parents can re-register children using codes like `100-dragons-u9-2526-john-smith`
- System finds the child's record in players24_25 table by name
- Parent passes security verification (DOB and postcode)
- All data is copied to registrations_2526 table
- Much faster than full registration (skip data entry for unchanged info)

### User Stories
1. **As a parent of a returning player**, I want to quickly re-register my child without re-entering all their details
2. **As a club administrator**, I want to ensure only the actual parent can re-register their child
3. **As a parent**, I want to verify and update only information that has changed

## Technical Changes Required

### Code Locations to Update

#### 1. Re-Registration Agent Instructions
- **Location**: `/backend/registration_agent/registration_agents.py` lines 4-10
- **Current**: Placeholder instructions about spelling name backwards
- **New**: Proper re-registration workflow instructions

#### 2. Create Re-Registration Routines
- **Location**: Add to `/backend/registration_agent/registration_routines.py`
- **Add**: New routines starting from routine_number 200+ for adult re-registration
- **Content**: Streamlined re-registration workflow

#### 3. Re-Registration Workflow (using existing routine structure)
```
Step 1: Lookup player in players24_25 table by name
Step 2: Security verification (ask for player DOB and postcode)
Step 3: Show all existing data and ask if anything needs updating
Step 4: Copy all data to registrations_2526 table
Step 5: Check if kit needed (use existing kit check function)
Step 6: Photo upload (use existing photo upload routine)
Step 7: Payment setup (use existing payment routines)
```

#### 4. Player Lookup Enhancement
- **Location**: `routing_validation.py` function `lookup_player_details` (lines 114-140)
- **Current**: Mock function that always returns Jack Grealish
- **New**: Query players24_25 table using playerFirstName1 and playerSurname1 fields

#### 5. New Airtable Function
- **Create**: Function to copy record from players24_25 to registrations_2526
- **Location**: New tool in registration tools
- **Purpose**: Transfer all player data to new season table after verification

### Database Considerations
- **Source Table**: players24_25 (last season's data)
- **Target Table**: registrations_2526 (current season)
- **Lookup Fields**: playerFirstName1 and playerSurname1
- **Security Fields**: player_dob and postcode for verification
- **Copy Operation**: Create new record in registrations_2526, don't update old table

### API Changes
- No new endpoints required
- Uses existing `last_agent: "re_registration"` routing
- Will use manual routine stepping as we build this feature

### Frontend Changes
- No frontend changes required
- System detects 100-prefix adult codes automatically

## Implementation Notes

### Architecture Considerations
1. **Identity Verification**: Ask two security questions (player DOB and postcode)
2. **Data Validation**: Show all existing data and ask if changes needed
3. **Efficient Flow**: Skip data entry by copying from last season
4. **Table Migration**: Copy from players24_25 to registrations_2526

### Security Considerations
- Two-factor verification (DOB AND postcode required)
- Don't show personal data until both security checks pass
- Log all re-registration attempts

### Performance Considerations
- Quick lookup of existing player data
- Minimal steps for returning players
- Pre-populate all existing information

### Integration Points
1. **Airtable**: Lookup and update existing records
2. **GoCardless**: New payment mandate for new season
3. **SMS**: Send payment link to confirmed number
4. **Photo Storage**: Check if photo update needed

## Testing Strategy

### Unit Testing
- Player lookup by name and team
- Identity verification logic
- Update only changed fields

### Integration Testing
- Full re-registration flow
- Payment setup for returning player
- Database update (not create)

### Manual Testing
1. Enter re-registration code (e.g., `100-dragons-u9-2526-john-smith`)
2. System finds John Smith in players24_25 table
3. Answer security questions (DOB and postcode)
4. Review and confirm existing data
5. Complete kit/photo/payment steps
6. Verify record created in registrations_2526

### Edge Cases
- Player not found in players24_25 table
- Wrong security answers (fail after 3 attempts?)
- Multiple players with same name (need team/age group match)
- Missing data in old record

## Risk Assessment

### Risk Level: Medium

### Potential Issues
1. Player impersonation (someone else using code)
2. Duplicate records if lookup fails
3. Lost data if update overwrites incorrectly
4. Payment mandate conflicts

### Mitigation
1. Identity verification step mandatory
2. Strict name + team matching
3. Show existing data before updates
4. Cancel old mandates before creating new

### Rollback Plan
- Can disable by routing 100-codes to error message
- Existing registration unaffected
- Manual re-registration fallback

## Deployment

### Changes Required
1. Update re-registration agent instructions
2. Add routines 200+ to registration_routines.py
3. Implement actual player lookup function
4. Test identity verification flow

### Environment Variables
- No new environment variables required
- Uses existing Airtable configuration

### Migration Steps
1. Deploy updated re-registration agent
2. Test with known adult player
3. Generate 100-prefix codes for adult teams
4. Enable for production use

### Verification Steps
1. Test player lookup works correctly
2. Complete adult re-registration flow
3. Verify only updates (not creates) record
4. Confirm payment setup works
5. Check old season data preserved

## Future Considerations

### Extensibility
- Family account linking (adult + children)
- Bulk re-registration for teams
- Auto-renewal options

### Maintenance
- Annual season code updates
- Handle players switching teams
- Archive old season data

### Related Features
- Youth player re-registration (100-prefix for under 18s)
- Coach/volunteer re-registration
- Transfer between clubs

## Implementation Approach

### Step 1: Fix Player Lookup
Replace mock function with actual Airtable query to players24_25:
```python
def lookup_player_details(player_name: str, team: str, age_group: str) -> dict:
    # Split name into first and last
    # Query players24_25 table for playerFirstName1 and playerSurname1
    # Return full player record if found
    # Return None if not found
```

### Step 2: Create Security Verification
- Ask for player DOB (must match player_dob field)
- Ask for postcode (must match postcode field)
- Both must match to proceed

### Step 3: Data Copy Function
Create new tool to copy all fields from players24_25 to registrations_2526

### Step 4: Reuse Existing Functions
- Kit check: Use existing check_if_kit_needed
- Photo upload: Use existing photo upload routine
- Payment: Use existing payment setup routines

## Example Re-Registration Code
```
100-dragons-u9-2526-john-smith
```

Where:
- `100` = Re-registration prefix (existing player)
- `dragons` = Team identifier
- `u9` = Age group
- `2526` = Season (2025-26)
- `john-smith` = Player's name from last season