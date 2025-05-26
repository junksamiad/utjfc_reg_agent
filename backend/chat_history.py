# backend/chat_history.py

_global_chat_histories = {}  # Underscore indicates it's intended for internal use by this module

DEFAULT_SESSION_ID = "global_session" # Simple default for now, good for single-user testing
MAX_HISTORY_LENGTH = 20 # Optional: Limit the number of turns to keep in history (total messages / 2)

def get_session_history(session_id: str = None) -> list:
    """
    Retrieves the chat history for a given session_id.
    If no session_id is provided, uses a default global session.
    Initializes an empty history if it's a new session.
    """
    if session_id is None:
        session_id = DEFAULT_SESSION_ID
    
    return _global_chat_histories.setdefault(session_id, [])

def add_message_to_session_history(session_id: str = None, role: str = None, content: str = None):
    """
    Adds a message to the chat history for a given session_id.
    Optionally trims the history if it exceeds MAX_HISTORY_LENGTH.
    """
    if session_id is None:
        session_id = DEFAULT_SESSION_ID
    
    if role and content:
        history = get_session_history(session_id) # Ensures session is initialized
        history.append({"role": role, "content": content})
        
        # Optional: Trim history to keep it from growing indefinitely
        # Each "turn" is a user message and an assistant message, so MAX_HISTORY_LENGTH * 2 messages total.
        # We remove from the beginning (oldest messages).
        # Be careful not to remove a system prompt if you add one at history[0]
        if MAX_HISTORY_LENGTH > 0:
            while len(history) > MAX_HISTORY_LENGTH * 2: # Assuming each turn = 2 messages
                history.pop(0) # Remove the oldest message
                # If you have a persistent system prompt at history[0], you might do history.pop(1)
    else:
        print(f"Warning: Role ({role}) or content ({content}) missing for session {session_id}, not adding to history.")

def clear_session_history(session_id: str = None):
    """
    Clears the chat history for a given session_id.
    If no session_id is provided, clears the default global session.
    """
    if session_id is None:
        session_id = DEFAULT_SESSION_ID

    if session_id in _global_chat_histories:
        _global_chat_histories[session_id] = [] # Clear the list
        print(f"History cleared for session_id: {session_id}")
    else:
        print(f"No history found to clear for session_id: {session_id}")

# Example of how to add a system prompt if desired (call this once at server startup for default session)
# def prime_default_session_with_system_prompt(prompt: str):
#     add_message_to_session_history(session_id=DEFAULT_SESSION_ID, role="system", content=prompt) 