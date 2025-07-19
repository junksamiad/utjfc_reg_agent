# ISSUE-004: Universal Agent Error on Non-Registration Code Input

**Priority**: High  
**Type**: Bug  
**Component**: Backend - Universal Agent (urmston_town_agent)  
**Created**: 2025-01-17  
**Status**: Open  

## Executive Summary

The Universal Agent displays an error message "Error: Universal Agent AI call failed unexpectedly" when users enter any text that is not a valid registration code. This prevents the agent from handling general queries about the football club, registration information, or other basic inquiries.

## Current Implementation

The Universal Agent is configured to:
1. Display welcome message: "Welcome to Urmston Town Juniors Football Club. What can I help you with today?"
2. Route valid registration codes (100-series, 200-series) to appropriate registration agents
3. Handle general queries through the orchestrator agent

Current error occurs in the routing/response handling when non-registration code input is provided.

## Problems Identified

1. **AI Call Failure**: The Universal Agent's AI response mechanism fails when processing general queries
2. **User Experience**: Users cannot get basic information about the club or registration process
3. **Missing Fallback**: No graceful error handling for general conversation flows
4. **Unclear Registration Process**: Users who don't have codes receive no guidance

## Proposed Solution

1. **Debug AI Integration**:
   - Check `backend/urmston_town_agent/responses.py` for AI call issues
   - Verify error handling in `chat_loop_1` function
   - Review retry logic and timeout settings

2. **Implement Basic Response Handling**:
   ```python
   # Add fallback response for registration queries
   if "register" in user_message.lower() or "join" in user_message.lower():
       return {
           "response": "To register your child with Urmston Town Juniors FC, you'll need a registration code from your team coach. Once you have the code, please enter it here to begin the registration process."
       }
   ```

3. **Fix AI Integration**:
   - Verify OpenAI API key is properly configured
   - Check MCP mode vs local mode settings
   - Ensure proper error handling wraps AI calls

4. **Add General Query Support**:
   - Club information responses
   - Training times and locations
   - Contact information
   - General FAQs

## Implementation Checklist

- [ ] Debug `urmston_town_agent/responses.py` AI call failure
- [ ] Add try/catch blocks with proper error messages
- [ ] Implement registration guidance response
- [ ] Test with various non-code inputs
- [ ] Add logging for debugging AI failures
- [ ] Verify environment variables are set correctly
- [ ] Test both MCP and local modes
- [ ] Add unit tests for general query handling

## Testing Instructions

1. Start the backend server:
   ```bash
   cd backend
   uvicorn server:app --reload --port 8000
   ```

2. Test scenarios:
   - Enter "hello" - should get friendly response
   - Enter "how do I register?" - should get registration guidance
   - Enter "what teams do you have?" - should get team information
   - Enter random text - should handle gracefully
   - Enter valid registration code - should route correctly

3. Expected outcomes:
   - No error messages for general queries
   - Clear guidance for registration questions
   - Proper routing for valid codes
   - Helpful responses for club information

## Additional Context

- The Universal Agent uses GPT-4.1 for MCP compatibility
- Error may be related to recent OpenAI Responses API migration
- Check `backend/server.py` for routing logic
- Review `USE_MCP` environment variable setting
- Related files:
  - `backend/urmston_town_agent/agents.py`
  - `backend/urmston_town_agent/responses.py`
  - `backend/server.py` (main routing)
  - `backend/.env` (configuration)