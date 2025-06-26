# UTJFC Registration System - Conversation History Architecture

## Overview

The UTJFC registration system maintains a complete conversation history for each user session, which is ultimately saved to the database for audit and review purposes. This document explains how the conversation history system works.

## Chat History Systems

### ⚠️ CRITICAL: Two Chat History Files Exist

There are **two separate chat history files** in the codebase:

1. **`urmston_town_agent/chat_history.py`** - ✅ **ACTIVE/MAIN SYSTEM**
2. **`registration_agent/chat_history_reg.py`** - ❌ **DUPLICATE/UNUSED**

### Active System Details

**File**: `urmston_town_agent/chat_history.py`

**Used by**:
- `server.py` - Main server application
- All session management
- Conversation history storage and retrieval

**Functions**:
- `get_session_history(session_id)` - Retrieve conversation for a session
- `add_message_to_session_history(session_id, role, content)` - Add message to session
- `clear_session_history(session_id)` - Clear session conversation

## How Conversation History is Built

### 1. Session Creation
When a user starts a chat, a unique session ID is generated:
```python
current_session_id = payload.session_id or f"session-{int(time.time() * 1000)}-{generate_random_string()}"
```

### 2. Message Storage Flow

**Every user message and AI response** is stored using:
```python
from urmston_town_agent.chat_history import add_message_to_session_history

# User messages
add_message_to_session_history(session_id, "user", user_message)

# AI responses
add_message_to_session_history(session_id, "assistant", ai_response)

# System messages (tool results, etc.)
add_message_to_session_history(session_id, "system", tool_result)
```

### 3. Registration Flow History

During registration, the conversation includes:

**Routine 1-28**: Complete registration conversation
- Parent details collection
- Child details collection  
- Address validation
- Medical information
- Payment setup

**Routine 29**: Payment token creation and database write
- Tool calls are logged to session history
- Results are stored as system messages

**Routine 30-35**: Kit selection and photo upload
- Kit size selection
- Shirt number validation
- Photo upload and validation

### 4. "lah" Cheat Code

The testing cheat code `"lah"` pre-populates a complete conversation history:

```python
if payload.user_message.strip().lower() == "lah":
    # Inject registration code
    inject_structured_registration_data(current_session_id, "200-leopards-u9-2526")
    
    # Add registration code to history
    add_message_to_session_history(current_session_id, "system", "REGISTRATION_CODE: 200-leopards-u9-2526")
    
    # Pre-populate 28 routines of conversation
    conversation_history = [
        ("assistant", "Can I take your first and last name..."),
        ("user", "Lee Hayton"),
        # ... complete conversation simulation
    ]
    
    # Add all to session history
    for role, message in conversation_history:
        add_message_to_session_history(current_session_id, role, message)
```

## Database Storage of Conversation History

### When It's Saved

Conversation history is saved to the database **only during photo upload** in routine 34, specifically when the `update_photo_link_to_db` tool is called.

### How It's Captured

In `responses_reg.py`, when `update_photo_link_to_db` is called:

```python
if function_name == "update_photo_link_to_db":
    # Get complete conversation history from session
    from urmston_town_agent.chat_history import get_session_history
    complete_session_history = get_session_history(session_id)
    
    # Convert to database format
    conversation_history = []
    for msg in complete_session_history:
        conversation_history.append({
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", "")
        })
    
    # Add to function arguments
    function_args["conversation_history"] = conversation_history
```

### Database Field

**Table**: `registrations_2526`
**Field**: `conversation_history` (Long Text field)
**Format**: JSON string containing array of message objects

```json
[
  {
    "role": "user",
    "content": "lah"
  },
  {
    "role": "assistant", 
    "content": "What's your preferred day of the month for the monthly subscription payment..."
  },
  {
    "role": "user",
    "content": "10"
  }
]
```

## Tool Call Logging

### System Messages for Tool Calls

When tools are executed, their results are logged to session history:

```python
# Tool result logging
tool_result_message = f"🔧 Tool Call: {function_name}\nResult: {json.dumps(function_result, indent=2)}"
add_message_to_session_history(session_id, "system", tool_result_message)
```

### Examples in Conversation History

Tool calls appear in the conversation as:
- **Tool execution**: `"🔧 Tool Call: create_payment_token"`
- **Tool results**: `"🔧 Tool Call: create_payment_token\nResult: {success: true, billing_request_id: 'BRQ123...'}"`

## Key Implementation Details

### Session History Format

Each session maintains an array of message objects:
```python
{
    "role": "user|assistant|system",
    "content": "message content"
}
```

### Memory Management

- **Maximum history**: 40 turns (80 messages total)
- **Cleanup**: Oldest messages removed when limit exceeded
- **Session persistence**: Maintained in memory during server runtime

### File Organization

```
backend/
├── urmston_town_agent/
│   └── chat_history.py          # ✅ ACTIVE - Main chat history system
├── registration_agent/
│   ├── chat_history_reg.py      # ❌ UNUSED - Duplicate file
│   └── responses_reg.py         # Uses urmston_town_agent.chat_history
└── server.py                    # Uses urmston_town_agent.chat_history
```

## Troubleshooting

### Common Issues

1. **Empty conversation history in database**
   - Check import path: Must use `urmston_town_agent.chat_history`
   - Verify session_id consistency across calls

2. **Missing registration code**
   - Ensure "lah" cheat properly injects the code
   - Verify `inject_structured_registration_data` uses correct chat history

3. **Tool results not appearing**
   - Check tool result logging in `responses_reg.py`
   - Verify `add_message_to_session_history` calls after tool execution

### Debugging Commands

```python
# Check session history
from urmston_town_agent.chat_history import get_session_history
history = get_session_history("session-id-here")
print(f"Session has {len(history)} messages")

# View conversation
for i, msg in enumerate(history):
    print(f"{i+1}. {msg['role']}: {msg['content'][:100]}...")
```

## Future Improvements

- Consider database persistence of session history during conversation (not just at end)
- Add conversation search/filtering capabilities
- Implement conversation archiving for completed registrations
- Add conversation replay functionality for customer service 