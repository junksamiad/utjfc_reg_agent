# Admin Agent Handoff System

**Feature ID**: `admin-agent-handoff`  
**Status**: Planning  
**Priority**: High  
**Estimated Effort**: 3-4 days  
**Dependencies**: 
- Universal agent (urmston_town_agent)
- Airtable admin password table
- SMS system (Twilio)
- GoCardless integration
- Existing CRUD tools
**Implementation Date**: TBD  
**Implemented By**: TBD  
**Branch**: TBD  

---

## Overview

Create a secure admin access system that allows authorized club administrators to access powerful backend functions through the chat interface. When a user types "admin" in the universal agent, the system will hand off to a specialized admin_agent that requires password authentication before granting access to administrative functions.

## Current Universal Agent Instructions

**Location**: `backend/server.py` lines 384-404

**Current Instructions**:
```
You are a helpful assistant for Urmston Town Juniors Football Club (UTJFC). 

You help with player registrations, team information, and general club inquiries. You have access to the club's registration database and can help parents and staff with:

- Looking up player registrations
- Checking registration status  
- Finding player information
- Creating new player registrations
- Updating existing registrations
- Answering questions about teams and seasons
- General club information

To perform any CRUD function on any of the club databases, call the airtable_database_operation, passing in any relevant request data to the tool call. 

Current season: 2025-26 (season code: 2526)
Previous season: 2024-25 (season code: 2425)

Default to current season (2526) unless user specifies otherwise.

Always respond in the structured format with your final response in the agent_final_response field.
```

## Business Requirements

### Problem Statement
- Club administrators need secure access to backend functions through the chat interface
- Current system has no admin access control
- Administrators need to perform tasks like sending SMS, managing payments, and database operations
- Must prevent unauthorized access to sensitive functions

### Success Criteria
- User types "admin" and gets handed off to admin agent
- Admin agent requires password authentication
- Password verified against Airtable admin table
- Authenticated admins can access powerful tools
- Session maintains admin context after authentication

### User Stories
1. **As a club administrator**, I want to access admin functions through the chat interface
2. **As an administrator**, I want my access to be password-protected for security
3. **As an admin**, I want to send SMS messages, manage payments, and perform database operations
4. **As the system**, I need to prevent unauthorized users from accessing admin functions

## Technical Changes Required

### Code Locations to Update

#### 1. Universal Agent Instructions Update
- **Location**: `backend/server.py` lines 384-404
- **Add**: Detection logic for "admin" keyword
- **Response**: Trigger handoff to admin agent

#### 2. Create Admin Agent Directory
- **Location**: `/backend/urmston_town_agent/admin_agent/`
- **Contents**:
  - `__init__.py`
  - `admin_agent.py` - Admin agent definition
  - `admin_tools.py` - Admin-specific tool definitions
  - `admin_responses.py` - Response handling for admin flow

#### 3. Admin Agent Implementation
```python
admin_agent = Agent(
    name="UTJFC Admin Assistant",
    model="gpt-4.1",
    instructions="""You are the administrative assistant for UTJFC staff.
    
    IMPORTANT: You must first verify the user's password before granting access to any admin functions.
    
    Once authenticated, you can help administrators with:
    - Sending SMS messages to players/parents
    - Managing GoCardless payments and mandates
    - Performing database CRUD operations
    - Generating reports
    - Managing team rosters
    - Handling special registration cases
    
    Always maintain security and audit trail of admin actions.
    """,
    tools=["check_admin_password", "send_sms", "gocardless_operations", "airtable_admin_crud", ...],
    use_mcp=False
)
```

#### 4. Admin Handoff Logic
- **Location**: `backend/server.py` in universal agent response handling
- **Add**: Check if response contains admin trigger
- **Action**: Override response and set `last_agent: "admin"`

#### 5. Admin Authentication Flow
```
Step 1: User types "admin"
Step 2: Universal agent detects keyword
Step 3: Response overridden to "Please provide the administrator password to access Urmston Town Administrator functions"
Step 4: Set last_agent: "admin"
Step 5: Admin agent receives password attempt
Step 6: Verify against Airtable admin_passwords table
Step 7: If correct, grant access; if wrong, deny and return to universal agent
```

### Database Considerations
- **New Table**: admin_passwords or admin_users in Airtable
- **Fields**: username, password_hash, permissions, last_login
- **Security**: Store hashed passwords, not plain text
- **Audit Trail**: Log all admin actions with timestamp and user

### API Changes
- No new endpoints required
- Uses existing chat endpoint with `last_agent: "admin"`
- Session maintains admin authentication state

### Frontend Changes
- No frontend changes required initially
- Could add visual indicator when in admin mode (future enhancement)

## Implementation Notes

### Architecture Considerations
1. **Handoff Mechanism**: Universal agent detects "admin" and triggers handoff
2. **Session State**: Maintain admin authentication in session
3. **Tool Access**: Admin agent has access to powerful tools not available to other agents
4. **Audit Trail**: Log all admin actions for security

### Security Considerations
- Password must be verified on every session (no persistence)
- Failed password attempts should be logged
- Consider rate limiting password attempts
- Admin tools should double-check authentication before executing
- Sensitive operations should require confirmation

### Performance Considerations
- Password check should be fast (indexed lookup)
- Admin tools may take longer (bulk operations)
- Consider async operations for large tasks

### Integration Points
1. **Airtable**: Admin password verification and CRUD operations
2. **Twilio**: Send SMS to players/parents
3. **GoCardless**: Payment management and reporting
4. **Session Management**: Maintain admin state
5. **Audit System**: Log all admin actions

## Testing Strategy

### Unit Testing
- Admin keyword detection in universal agent
- Password verification logic
- Admin tool access control
- Session state management

### Integration Testing
- Full handoff flow from universal to admin agent
- Password verification against Airtable
- Admin tool execution
- Return to universal agent on logout

### Manual Testing
1. Type "admin" in chat
2. Receive password prompt
3. Enter correct password
4. Access admin functions
5. Test various admin tools
6. Verify audit trail

### Edge Cases
- Multiple "admin" keywords in message
- Wrong password attempts
- Session timeout while authenticated
- Concurrent admin sessions

## Risk Assessment

### Risk Level: High (due to security implications)

### Potential Issues
1. Unauthorized access to sensitive functions
2. Password exposure in logs or history
3. Admin actions causing data corruption
4. Audit trail gaps

### Mitigation
1. Strong password requirements
2. Sanitize logs to remove passwords
3. Confirmation prompts for destructive operations
4. Comprehensive audit logging

### Rollback Plan
- Can disable by removing admin detection from universal agent
- Existing functionality unaffected
- Manual admin access remains available

## Deployment

### Changes Required
1. Update universal agent instructions
2. Deploy admin_agent module
3. Create admin_passwords table in Airtable
4. Configure admin tools and permissions
5. Test authentication flow

### Environment Variables
- May need ADMIN_TABLE_ID for Airtable
- Existing Twilio/GoCardless configs will be reused

### Migration Steps
1. Create admin_passwords table
2. Add initial admin users with hashed passwords
3. Deploy code with admin agent
4. Test with known admin credentials
5. Enable for production

### Verification Steps
1. Test admin keyword triggers handoff
2. Verify password check works
3. Test admin tools execute properly
4. Confirm audit trail captures actions
5. Verify logout/timeout behavior

## Future Considerations

### Extensibility
- Role-based permissions (super admin, team admin, etc.)
- Two-factor authentication
- Admin action approval workflows
- Scheduled admin tasks

### Maintenance
- Regular password rotation
- Audit log retention policy
- Performance monitoring for admin operations
- Access review process

### Related Features
- Coach portal with limited admin access
- Parent self-service for certain updates
- Automated admin notifications

## Implementation Approach

### Step 1: Update Universal Agent
Add to instructions: "If a user types 'admin' as their message, you must respond with exactly: 'ADMIN_HANDOFF_REQUESTED' in your response."

### Step 2: Create Admin Agent Module
```
/backend/urmston_town_agent/admin_agent/
├── __init__.py
├── admin_agent.py
├── admin_tools.py
└── admin_responses.py
```

### Step 3: Handoff Detection
In server.py, after universal agent response:
```python
if "ADMIN_HANDOFF_REQUESTED" in assistant_content_to_send:
    response_json = {
        "response": "Please provide the administrator password to access Urmston Town Administrator functions",
        "last_agent": "admin"
    }
    return response_json
```

### Step 4: Admin Route Handling
Add new route handling for `last_agent: "admin"` in server.py

### Step 5: Password Verification Tool
Create tool to check password against Airtable admin table

## Example Admin Flow
```
User: admin
Bot: Please provide the administrator password to access Urmston Town Administrator functions
User: MySecurePassword123
Bot: Welcome, Administrator. You now have access to admin functions. How can I help you today?
User: Send SMS to all U10 parents about tomorrow's match
Bot: I'll send an SMS to all U10 parents. What message would you like to send?
```