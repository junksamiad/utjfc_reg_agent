# This file will be populated with the content of simple_test_backend/main.py
# The old simple_test_backend/main.py will be deleted by a subsequent operation. 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from responses import chat_loop_1
from chat_history import get_session_history, add_message_to_session_history, clear_session_history, DEFAULT_SESSION_ID
from agents import Agent # Import the Agent class

app = FastAPI()

# Pydantic model for the chat request
class UserPayload(BaseModel): 
    user_message: str

# Permissive CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Create default agent instance
default_agent = Agent(
    name="UTJFC Registration Assistant",
    model="gpt-4.1",
    instructions="""You are a helpful assistant for Urmston Town Juniors Football Club (UTJFC). 

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
""",
    tools=["airtable_database_operation"]
)

@app.on_event("startup")
async def startup_event():
    # Optional: Prime the default session with a system prompt if you have one.
    # from chat_history import prime_default_session_with_system_prompt
    # prime_default_session_with_system_prompt("You are a helpful AI assistant.")
    print(f"Server started. Default session ID for chat history is: {DEFAULT_SESSION_ID}")
    print(f"Using Agent: {default_agent.name} with model {default_agent.model}")

@app.get("/")
async def read_root():
    return {"message": "Hello from the Refactored Simple Test Backend with History and Agents!"}

@app.post("/chat")
async def chat_endpoint(payload: UserPayload):
    current_session_id = DEFAULT_SESSION_ID
    
    print(f"--- Session [{current_session_id}] Received user message: {payload.user_message} ---")
    
    # Add user message to session history
    add_message_to_session_history(current_session_id, "user", payload.user_message)
    
    # Get current session history for context
    session_history = get_session_history(current_session_id)
    
    print(f"--- Session [{current_session_id}] Current session history length: {len(session_history)} ---")
    
    # Get AI response using the agent
    ai_full_response_object = chat_loop_1(default_agent, session_history)
    
    print(f"--- Session [{current_session_id}] Full AI Response Object: ---")
    print(ai_full_response_object)
    print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\\n")

    print(f"--- Session [{current_session_id}] Attempting to parse the above AI response object ---") # Added log line

    assistant_role_to_store = "assistant" 
    assistant_content_to_send = "Error: Could not parse AI response for frontend."
    
    try:
        # Handle Responses API format first (new format)
        if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
            assistant_content_to_send = ai_full_response_object.output_text
        elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
            # Fallback to detailed parsing for Responses API
            if (len(ai_full_response_object.output) > 0 and 
                hasattr(ai_full_response_object.output[0], 'type') and 
                ai_full_response_object.output[0].type == 'message' and
                hasattr(ai_full_response_object.output[0], 'content') and 
                ai_full_response_object.output[0].content and 
                len(ai_full_response_object.output[0].content) > 0 and
                hasattr(ai_full_response_object.output[0].content[0], 'text')):
                assistant_content_to_send = ai_full_response_object.output[0].content[0].text
            else:
                assistant_content_to_send = "Assistant is processing your request..."
        # Handle legacy Chat Completions API format (fallback)
        elif hasattr(ai_full_response_object, 'choices') and ai_full_response_object.choices:
            message = ai_full_response_object.choices[0].message
            if hasattr(message, 'content') and message.content:
                assistant_content_to_send = message.content
            else:
                assistant_content_to_send = "Assistant is processing your request..."
        elif isinstance(ai_full_response_object, dict) and "error" in ai_full_response_object:
            assistant_content_to_send = f"Error: {ai_full_response_object['error']}"
        else:
            print(f"--- Session [{current_session_id}] Unexpected response format ---")
            print(f"--- Response object attributes: {dir(ai_full_response_object)} ---")
            assistant_content_to_send = "Error: Unexpected response format from AI."
            
    except Exception as e:
        print(f"--- Session [{current_session_id}] Error parsing AI response: {e} ---")
        assistant_content_to_send = f"Error parsing AI response: {str(e)}"
    
    print(f"--- Session [{current_session_id}] Final assistant content to send: {assistant_content_to_send} ---")
    
    # Add assistant response to session history
    add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
    
    return {"response": assistant_content_to_send}

@app.post("/clear")
async def clear_chat_history():
    current_session_id = DEFAULT_SESSION_ID
    clear_session_history(current_session_id)
    print(f"--- Session [{current_session_id}] Chat history cleared ---")
    return {"message": "Chat history cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 