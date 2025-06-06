# This file will be populated with the content of simple_test_backend/main.py
# The old simple_test_backend/main.py will be deleted by a subsequent operation. 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json

from urmston_town_agent.responses import chat_loop_1
from urmston_town_agent.chat_history import get_session_history, add_message_to_session_history, clear_session_history, DEFAULT_SESSION_ID
from urmston_town_agent.agents import Agent # Import the Agent class

# Import registration agent components
from registration_agent.routing_validation import validate_and_route_registration
from registration_agent.registration_agents import re_registration_agent, new_registration_agent
from registration_agent.responses_reg import chat_loop_new_registration_1, chat_loop_renew_registration_1

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

# Create default agent instances
local_agent = Agent(
    name="UTJFC Registration Assistant (Local)",
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

Always respond in the structured format with your final response in the agent_final_response field.
""",
    tools=["airtable_database_operation"],
    use_mcp=False  # Local function calling
)

# Create MCP agent instance
mcp_agent = Agent.create_mcp_agent(
    name="UTJFC Registration Assistant (MCP)",
    instructions="""You are a helpful assistant for Urmston Town Juniors Football Club (UTJFC). 

You help with player registrations, team information, and general club inquiries. You have access to the club's registration database via MCP server and can help parents and staff with:

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
"""
)

# Default to MCP agent (can be changed via environment variable)
import os
use_mcp_by_default = os.getenv("USE_MCP", "true").lower() == "true"
default_agent = mcp_agent if use_mcp_by_default else local_agent

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
    
    # Check for registration code and validate FIRST (before adding to history)
    validation_result = validate_and_route_registration(payload.user_message)
    
    if validation_result["valid"]:
        print(f"--- Session [{current_session_id}] Valid registration code detected ---")
        print(f"--- Validation result: {validation_result} ---")
        
        registration_code = validation_result["registration_code"]
        route_type = validation_result["route"]
        player_details = validation_result.get("player_details")
        
        if route_type == "re_registration":
            print(f"--- Routing to re-registration agent for {registration_code.get('player_name', 'player')} ---")
            if player_details:
                print(f"--- Player found in database: {player_details} ---")
            
            # Add the registration code to session history
            add_message_to_session_history(current_session_id, "user", payload.user_message)
            session_history = get_session_history(current_session_id)
            
            # Use re-registration flow
            ai_full_response_object = chat_loop_renew_registration_1(re_registration_agent, session_history)
            
            # Process the re-registration agent response
            print(f"--- Session [{current_session_id}] Re-registration AI Response Object: ---")
            print(ai_full_response_object)
            print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\n")

            print(f"--- Session [{current_session_id}] Attempting to parse re-registration structured response ---")

            assistant_role_to_store = "assistant" 
            assistant_content_to_send = "Error: Could not parse re-registration AI response for frontend."
            
            try:
                # Handle structured output from Responses API (same logic as universal bot)
                if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
                    try:
                        # Parse the structured JSON response
                        structured_response = json.loads(ai_full_response_object.output_text)
                        if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                            assistant_content_to_send = structured_response['agent_final_response']
                            print(f"--- Session [{current_session_id}] Extracted from re-registration structured output: {assistant_content_to_send} ---")
                        else:
                            # Fallback to raw output_text if not properly structured
                            assistant_content_to_send = ai_full_response_object.output_text
                            print(f"--- Session [{current_session_id}] Using raw output_text as fallback ---")
                    except json.JSONDecodeError as e:
                        print(f"--- Session [{current_session_id}] JSON decode error: {e}, using raw output_text ---")
                        assistant_content_to_send = ai_full_response_object.output_text
                        
                # Fallback to detailed parsing for Responses API (if output_text not available)
                elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                    if (len(ai_full_response_object.output) > 0 and 
                        hasattr(ai_full_response_object.output[0], 'type') and 
                        ai_full_response_object.output[0].type == 'message' and
                        hasattr(ai_full_response_object.output[0], 'content') and 
                        ai_full_response_object.output[0].content and 
                        len(ai_full_response_object.output[0].content) > 0 and
                        hasattr(ai_full_response_object.output[0].content[0], 'text')):
                        
                        try:
                            # Try to parse structured output from detailed format
                            text_content = ai_full_response_object.output[0].content[0].text
                            structured_response = json.loads(text_content)
                            if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                                assistant_content_to_send = structured_response['agent_final_response']
                            else:
                                assistant_content_to_send = text_content
                        except json.JSONDecodeError:
                            assistant_content_to_send = ai_full_response_object.output[0].content[0].text
                    else:
                        assistant_content_to_send = "Re-registration assistant is processing your request..."
                        
                # Handle error responses
                elif isinstance(ai_full_response_object, dict) and "error" in ai_full_response_object:
                    assistant_content_to_send = f"Error: {ai_full_response_object['error']}"
                else:
                    print(f"--- Session [{current_session_id}] Unexpected re-registration response format ---")
                    assistant_content_to_send = "Error: Unexpected response format from re-registration AI."
                    
            except Exception as e:
                print(f"--- Session [{current_session_id}] Error parsing re-registration AI response: {e} ---")
                assistant_content_to_send = f"Error parsing re-registration AI response: {str(e)}"
            
            print(f"--- Session [{current_session_id}] Final re-registration assistant content to send: {assistant_content_to_send} ---")
            
            # Add assistant response to session history
            add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
            
            return {"response": assistant_content_to_send}
            
        elif route_type == "new_registration":
            print(f"--- Routing to new registration agent for team {registration_code['team']} {registration_code['age_group']} ---")
            
            # Add the registration code to session history
            add_message_to_session_history(current_session_id, "user", payload.user_message)
            session_history = get_session_history(current_session_id)
            
            # Use new registration flow
            ai_full_response_object = chat_loop_new_registration_1(new_registration_agent, session_history)
            
            # Process the registration agent response
            print(f"--- Session [{current_session_id}] Registration AI Response Object: ---")
            print(ai_full_response_object)
            print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\n")

            print(f"--- Session [{current_session_id}] Attempting to parse registration structured response ---")

            assistant_role_to_store = "assistant" 
            assistant_content_to_send = "Error: Could not parse registration AI response for frontend."
            
            try:
                # Handle structured output from Responses API (same logic as universal bot)
                if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
                    try:
                        # Parse the structured JSON response
                        structured_response = json.loads(ai_full_response_object.output_text)
                        if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                            assistant_content_to_send = structured_response['agent_final_response']
                            print(f"--- Session [{current_session_id}] Extracted from registration structured output: {assistant_content_to_send} ---")
                        else:
                            # Fallback to raw output_text if not properly structured
                            assistant_content_to_send = ai_full_response_object.output_text
                            print(f"--- Session [{current_session_id}] Using raw output_text as fallback ---")
                    except json.JSONDecodeError as e:
                        print(f"--- Session [{current_session_id}] JSON decode error: {e}, using raw output_text ---")
                        assistant_content_to_send = ai_full_response_object.output_text
                        
                # Fallback to detailed parsing for Responses API (if output_text not available)
                elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                    if (len(ai_full_response_object.output) > 0 and 
                        hasattr(ai_full_response_object.output[0], 'type') and 
                        ai_full_response_object.output[0].type == 'message' and
                        hasattr(ai_full_response_object.output[0], 'content') and 
                        ai_full_response_object.output[0].content and 
                        len(ai_full_response_object.output[0].content) > 0 and
                        hasattr(ai_full_response_object.output[0].content[0], 'text')):
                        
                        try:
                            # Try to parse structured output from detailed format
                            text_content = ai_full_response_object.output[0].content[0].text
                            structured_response = json.loads(text_content)
                            if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                                assistant_content_to_send = structured_response['agent_final_response']
                            else:
                                assistant_content_to_send = text_content
                        except json.JSONDecodeError:
                            assistant_content_to_send = ai_full_response_object.output[0].content[0].text
                    else:
                        assistant_content_to_send = "Registration assistant is processing your request..."
                        
                # Handle error responses
                elif isinstance(ai_full_response_object, dict) and "error" in ai_full_response_object:
                    assistant_content_to_send = f"Error: {ai_full_response_object['error']}"
                else:
                    print(f"--- Session [{current_session_id}] Unexpected registration response format ---")
                    assistant_content_to_send = "Error: Unexpected response format from registration AI."
                    
            except Exception as e:
                print(f"--- Session [{current_session_id}] Error parsing registration AI response: {e} ---")
                assistant_content_to_send = f"Error parsing registration AI response: {str(e)}"
            
            print(f"--- Session [{current_session_id}] Final registration assistant content to send: {assistant_content_to_send} ---")
            
            # Add assistant response to session history
            add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
            
            return {"response": assistant_content_to_send}
    
    # If not a registration code (or validation failed), continue with universal bot
    # Add user message to session history
    add_message_to_session_history(current_session_id, "user", payload.user_message)
    
    # Get current session history for context
    session_history = get_session_history(current_session_id)
    
    print(f"--- Session [{current_session_id}] Current session history length: {len(session_history)} ---")
    print(f"--- Session [{current_session_id}] Continuing with universal bot ---")
    
    # Get AI response using the agent
    ai_full_response_object = chat_loop_1(default_agent, session_history)
    
    print(f"--- Session [{current_session_id}] Full AI Response Object: ---")
    print(ai_full_response_object)
    print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\n")

    print(f"--- Session [{current_session_id}] Attempting to parse structured response ---")

    assistant_role_to_store = "assistant" 
    assistant_content_to_send = "Error: Could not parse AI response for frontend."
    
    try:
        # Handle structured output from Responses API
        if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
            try:
                # Parse the structured JSON response
                structured_response = json.loads(ai_full_response_object.output_text)
                if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                    assistant_content_to_send = structured_response['agent_final_response']
                    print(f"--- Session [{current_session_id}] Extracted from structured output: {assistant_content_to_send} ---")
                else:
                    # Fallback to raw output_text if not properly structured
                    assistant_content_to_send = ai_full_response_object.output_text
                    print(f"--- Session [{current_session_id}] Using raw output_text as fallback ---")
            except json.JSONDecodeError as e:
                print(f"--- Session [{current_session_id}] JSON decode error: {e}, using raw output_text ---")
                assistant_content_to_send = ai_full_response_object.output_text
                
        # Fallback to detailed parsing for Responses API (if output_text not available)
        elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
            if (len(ai_full_response_object.output) > 0 and 
                hasattr(ai_full_response_object.output[0], 'type') and 
                ai_full_response_object.output[0].type == 'message' and
                hasattr(ai_full_response_object.output[0], 'content') and 
                ai_full_response_object.output[0].content and 
                len(ai_full_response_object.output[0].content) > 0 and
                hasattr(ai_full_response_object.output[0].content[0], 'text')):
                
                try:
                    # Try to parse structured output from detailed format
                    text_content = ai_full_response_object.output[0].content[0].text
                    structured_response = json.loads(text_content)
                    if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                        assistant_content_to_send = structured_response['agent_final_response']
                    else:
                        assistant_content_to_send = text_content
                except json.JSONDecodeError:
                    assistant_content_to_send = ai_full_response_object.output[0].content[0].text
            else:
                assistant_content_to_send = "Assistant is processing your request..."
                
        # Handle error responses
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

@app.get("/agent/status")
async def get_agent_status():
    """Get current agent configuration and status"""
    return {
        "current_agent": {
            "name": default_agent.name,
            "model": default_agent.model,
            "use_mcp": default_agent.use_mcp,
            "mcp_server_url": default_agent.mcp_server_url if default_agent.use_mcp else None,
            "tools": default_agent.tools
        },
        "available_modes": {
            "local": {
                "name": local_agent.name,
                "description": "Uses local function calling (backend tools directly)"
            },
            "mcp": {
                "name": mcp_agent.name,
                "description": "Uses remote MCP server for tool execution",
                "server_url": mcp_agent.mcp_server_url
            }
        }
    }

class AgentModeRequest(BaseModel):
    mode: str  # "local" or "mcp"

@app.post("/agent/mode")
async def switch_agent_mode(request: AgentModeRequest):
    """Switch between local function calling and MCP mode"""
    global default_agent
    
    if request.mode == "local":
        default_agent = local_agent
        return {
            "message": "Switched to local function calling mode",
            "agent": {
                "name": default_agent.name,
                "use_mcp": default_agent.use_mcp
            }
        }
    elif request.mode == "mcp":
        default_agent = mcp_agent
        return {
            "message": "Switched to MCP server mode",
            "agent": {
                "name": default_agent.name,
                "use_mcp": default_agent.use_mcp,
                "mcp_server_url": default_agent.mcp_server_url
            }
        }
    else:
        return {"error": "Invalid mode. Use 'local' or 'mcp'"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 