# This file will be populated with the content of simple_test_backend/main.py
# The old simple_test_backend/main.py will be deleted by a subsequent operation. 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json

from urmston_town_agent.responses import chat_loop_1
from urmston_town_agent.chat_history import get_session_history, add_message_to_session_history, clear_session_history, DEFAULT_SESSION_ID
from urmston_town_agent.agents import Agent # Import the Agent class

# Import registration agent components
from registration_agent.routing_validation import validate_and_route_registration
from registration_agent.registration_agents import re_registration_agent, new_registration_agent
from registration_agent.registration_routines import RegistrationRoutines
from registration_agent.responses_reg import chat_loop_new_registration_1, chat_loop_renew_registration_1

app = FastAPI()

# Pydantic model for the chat request
class UserPayload(BaseModel):
    user_message: str
    session_id: Optional[str] = None  # Add optional session_id field
    routine_number: Optional[int] = None  # Add optional routine_number field for registration flow
    last_agent: Optional[str] = None  # Add optional last_agent field for flow continuation

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
    current_session_id = payload.session_id or DEFAULT_SESSION_ID
    
    # Add logging to track session ID usage
    if payload.session_id:
        print(f"--- Using FRONTEND session ID: {current_session_id} ---")
    else:
        print(f"--- Using DEFAULT session ID: {current_session_id} (no session_id provided) ---")
    
    print(f"--- Session [{current_session_id}] Received user message: {payload.user_message} ---")
    
    # Check if this is a routine-based new registration flow (user already in registration process)
    if payload.routine_number is not None:
        print(f"--- Session [{current_session_id}] Routine-based new registration flow detected, routine_number: {payload.routine_number} ---")
        
        # Add user message to session history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        session_history = get_session_history(current_session_id)
        
        # Get the routine message for this step
        routine_message = RegistrationRoutines.get_routine_message(payload.routine_number)
        if not routine_message:
            print(f"--- Session [{current_session_id}] Invalid routine_number: {payload.routine_number} ---")
            response_json = {
                "response": "Sorry, there was an error with the registration process. Please try again.",
                "last_agent": "new_registration",
                "routine_number": 1
            }
            print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
            return response_json
        
        print(f"--- Session [{current_session_id}] Using routine message: {routine_message} ---")
        
        # Get dynamic instructions by injecting routine message into existing agent
        dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_message)
        
        # Create a temporary agent with the same configuration but dynamic instructions
        from registration_agent.agents_reg import Agent
        dynamic_agent = Agent(
            name=new_registration_agent.name,
            model=new_registration_agent.model,
            instructions=dynamic_instructions,
            tools=new_registration_agent.tools,
            use_mcp=new_registration_agent.use_mcp
        )
        
        # Use new registration flow with dynamic agent
        ai_full_response_object = chat_loop_new_registration_1(dynamic_agent, session_history, current_session_id)
        
        # Process the response (same logic as other registration agents)
        print(f"--- Session [{current_session_id}] Routine-based Registration AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant" 
        assistant_content_to_send = "Error: Could not parse registration AI response for frontend."
        routine_number_from_agent = None
        
        try:
            # Parse structured response to get both message and routine_number
            if hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                if (len(ai_full_response_object.output) > 0 and 
                    hasattr(ai_full_response_object.output[0], 'content') and 
                    ai_full_response_object.output[0].content and 
                    len(ai_full_response_object.output[0].content) > 0 and
                    hasattr(ai_full_response_object.output[0].content[0], 'text')):
                    
                    try:
                        text_content = ai_full_response_object.output[0].content[0].text
                        structured_response = json.loads(text_content)
                        if isinstance(structured_response, dict):
                            if 'agent_final_response' in structured_response:
                                assistant_content_to_send = structured_response['agent_final_response']
                            if 'routine_number' in structured_response:
                                routine_number_from_agent = structured_response['routine_number']
                                print(f"--- Session [{current_session_id}] Agent set routine_number to: {routine_number_from_agent} ---")
                        else:
                            assistant_content_to_send = text_content
                    except json.JSONDecodeError:
                        assistant_content_to_send = ai_full_response_object.output[0].content[0].text
                        
        except Exception as e:
            print(f"--- Session [{current_session_id}] Error parsing routine-based registration AI response: {e} ---")
            assistant_content_to_send = f"Error parsing registration AI response: {str(e)}"
        
        print(f"--- Session [{current_session_id}] Final routine-based assistant content to send: {assistant_content_to_send} ---")
        
        # Check for routine 22 detection - loop back instead of sending response
        if routine_number_from_agent == 22:
            print(f"--- Session [{current_session_id}] Routine 22 detected - looping back to process age-based routing ---")
            
            # Add assistant response to session history (confirm same address)
            add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
            
            # Get updated session history for routine 22 processing
            session_history = get_session_history(current_session_id)
            
            # Get routine 22 message and create dynamic agent
            routine_22_message = RegistrationRoutines.get_routine_message(22)
            print(f"--- Session [{current_session_id}] Using routine 22 message for age-based routing: {routine_22_message} ---")
            
            # Get dynamic instructions for routine 22
            dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_22_message)
            
            # Create temporary agent for routine 22
            from registration_agent.agents_reg import Agent
            routine_22_agent = Agent(
                name=new_registration_agent.name,
                model=new_registration_agent.model,
                instructions=dynamic_instructions,
                tools=new_registration_agent.tools,
                use_mcp=new_registration_agent.use_mcp
            )
            
            # Process routine 22 (age-based routing)
            ai_full_response_object = chat_loop_new_registration_1(routine_22_agent, session_history, current_session_id)
            
            # Parse routine 22 response
            routine_22_assistant_content = "Error: Could not parse routine 22 response."
            routine_22_routine_number = None
            
            try:
                if hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                    if (len(ai_full_response_object.output) > 0 and 
                        hasattr(ai_full_response_object.output[0], 'content') and 
                        ai_full_response_object.output[0].content and 
                        len(ai_full_response_object.output[0].content) > 0 and
                        hasattr(ai_full_response_object.output[0].content[0], 'text')):
                        
                        try:
                            text_content = ai_full_response_object.output[0].content[0].text
                            structured_response = json.loads(text_content)
                            if isinstance(structured_response, dict):
                                if 'agent_final_response' in structured_response:
                                    routine_22_assistant_content = structured_response['agent_final_response']
                                if 'routine_number' in structured_response:
                                    routine_22_routine_number = structured_response['routine_number']
                                    print(f"--- Session [{current_session_id}] Routine 22 set next routine to: {routine_22_routine_number} ---")
                            else:
                                routine_22_assistant_content = text_content
                        except json.JSONDecodeError:
                            routine_22_assistant_content = ai_full_response_object.output[0].content[0].text
                            
            except Exception as e:
                print(f"--- Session [{current_session_id}] Error parsing routine 22 response: {e} ---")
                routine_22_assistant_content = f"Error parsing routine 22 response: {str(e)}"
            
            print(f"--- Session [{current_session_id}] Routine 22 final content: {routine_22_assistant_content} ---")
            
            # Add routine 22 response to session history
            add_message_to_session_history(current_session_id, "assistant", routine_22_assistant_content)
            
            # Return routine 22 response with new routine number
            response_json = {
                "response": routine_22_assistant_content,
                "last_agent": "new_registration",
                "routine_number": routine_22_routine_number or 999
            }
            print(f"--- Session [{current_session_id}] RETURNING ROUTINE 22 PROCESSED RESPONSE TO CLIENT: {response_json} ---")
            return response_json
        
        # Normal case - add assistant response to session history and return
        add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
        
        # Return response with routine_number from agent (or fallback to current)
        response_json = {
            "response": assistant_content_to_send,
            "last_agent": "new_registration",
            "routine_number": routine_number_from_agent or payload.routine_number
        }
        print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
        return response_json
    
    # Check if this is a registration continuation (last_agent indicates registration but routine_number missing)
    if hasattr(payload, 'last_agent') and payload.last_agent == "new_registration" and payload.routine_number is None:
        print(f"--- Session [{current_session_id}] Registration continuation detected (last_agent=new_registration, routine_number=None) ---")
        print(f"--- Session [{current_session_id}] Defaulting to routine_number=1 for registration flow ---")
        
        # Default to routine 1 (parent name collection) when routine_number is missing
        payload.routine_number = 1
        
        # Add user message to session history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        session_history = get_session_history(current_session_id)
        
        # Get the routine message for this step
        routine_message = RegistrationRoutines.get_routine_message(payload.routine_number)
        print(f"--- Session [{current_session_id}] Using routine message: {routine_message} ---")
        
        # Get dynamic instructions by injecting routine message into existing agent
        dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_message)
        
        # Create a temporary agent with the same configuration but dynamic instructions
        from registration_agent.agents_reg import Agent
        dynamic_agent = Agent(
            name=new_registration_agent.name,
            model=new_registration_agent.model,
            instructions=dynamic_instructions,
            tools=new_registration_agent.tools,
            use_mcp=new_registration_agent.use_mcp
        )
        
        # Use new registration flow with dynamic agent
        ai_full_response_object = chat_loop_new_registration_1(dynamic_agent, session_history, current_session_id)
        
        # Process the response (same logic as routine flow)
        print(f"--- Session [{current_session_id}] Registration continuation AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant" 
        assistant_content_to_send = "Error: Could not parse registration AI response for frontend."
        routine_number_from_agent = None
        
        try:
            # Parse structured response to get both message and routine_number
            if hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                if (len(ai_full_response_object.output) > 0 and 
                    hasattr(ai_full_response_object.output[0], 'content') and 
                    ai_full_response_object.output[0].content and 
                    len(ai_full_response_object.output[0].content) > 0 and
                    hasattr(ai_full_response_object.output[0].content[0], 'text')):
                    
                    try:
                        text_content = ai_full_response_object.output[0].content[0].text
                        structured_response = json.loads(text_content)
                        if isinstance(structured_response, dict):
                            if 'agent_final_response' in structured_response:
                                assistant_content_to_send = structured_response['agent_final_response']
                            if 'routine_number' in structured_response:
                                routine_number_from_agent = structured_response['routine_number']
                                print(f"--- Session [{current_session_id}] Agent set routine_number to: {routine_number_from_agent} ---")
                        else:
                            assistant_content_to_send = text_content
                    except json.JSONDecodeError:
                        assistant_content_to_send = ai_full_response_object.output[0].content[0].text
                        
        except Exception as e:
            print(f"--- Session [{current_session_id}] Error parsing registration continuation AI response: {e} ---")
            assistant_content_to_send = f"Error parsing registration AI response: {str(e)}"
        
        print(f"--- Session [{current_session_id}] Final registration continuation assistant content to send: {assistant_content_to_send} ---")
        
        # Add assistant response to session history
        add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
        
        # Return response with routine_number from agent (or fallback to 1)
        response_json = {
            "response": assistant_content_to_send,
            "last_agent": "new_registration",
            "routine_number": routine_number_from_agent or 1
        }
        print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
        return response_json
    
    # Check if this is a re-registration continuation (last_agent indicates re-registration)
    if hasattr(payload, 'last_agent') and payload.last_agent == "re_registration":
        print(f"--- Session [{current_session_id}] Re-registration continuation detected (last_agent=re_registration) ---")
        
        # Add user message to session history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        session_history = get_session_history(current_session_id)
        
        # Use re-registration flow (no routine system, just simple continuation)
        ai_full_response_object = chat_loop_renew_registration_1(re_registration_agent, session_history)
        
        # Process the re-registration agent response (same logic as initial re-registration)
        print(f"--- Session [{current_session_id}] Re-registration continuation AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant" 
        assistant_content_to_send = "Error: Could not parse re-registration AI response for frontend."
        
        try:
            # Handle structured output from Responses API (same logic as initial re-registration)
            if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
                try:
                    # Parse the structured JSON response
                    structured_response = json.loads(ai_full_response_object.output_text)
                    if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                        assistant_content_to_send = structured_response['agent_final_response']
                        print(f"--- Session [{current_session_id}] Extracted from re-registration continuation structured output: {assistant_content_to_send} ---")
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
                print(f"--- Session [{current_session_id}] Unexpected re-registration continuation response format ---")
                assistant_content_to_send = "Error: Unexpected response format from re-registration AI."
                
        except Exception as e:
            print(f"--- Session [{current_session_id}] Error parsing re-registration continuation AI response: {e} ---")
            assistant_content_to_send = f"Error parsing re-registration AI response: {str(e)}"
        
        print(f"--- Session [{current_session_id}] Final re-registration continuation assistant content to send: {assistant_content_to_send} ---")
        
        # Add assistant response to session history
        add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
        
        # Return response with last_agent for continued re-registration tracking
        response_json = {
            "response": assistant_content_to_send,
            "last_agent": "re_registration"
        }
        print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
        return response_json
    
    # Check for testing cheat code FIRST (before any other validation)
    if payload.user_message.strip().lower() == "lah":
        print(f"--- Session [{current_session_id}] Testing cheat code 'lah' detected - jumping to routine 29 with full conversation history ---")
        
        # Add the cheat code to session history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        
        # Inject structured registration data for age-based routing
        from registration_agent.routing_validation import inject_structured_registration_data
        inject_structured_registration_data(current_session_id, "200-leopards-u9-2526")
        
        # Pre-populate complete conversation history (routines 1-28)
        conversation_history = [
            # Routine 1 - Parent name
            ("assistant", "Can I take your first and last name so I know how to refer to you?"),
            ("user", "Lee Hayton"),
            ("assistant", "Perfect, thanks Lee! Now could you please tell me your child's first and last name?"),
            
            # Routine 2 - Child name  
            ("user", "Seb Hayton"),
            ("assistant", "Great! Could you please tell me Seb's date of birth?"),
            
            # Routine 3 - Child DOB
            ("user", "18th July 2014"),
            ("assistant", "Perfect! Could you tell me what gender Seb is?"),
            
            # Routine 4 - Child gender
            ("user", "He's a boy"),
            ("assistant", "Thanks! Does Seb have any known medical issues that the club should be aware of?"),
            
            # Routine 5 - Medical issues
            ("user", "Yes, he has asthma"),
            ("assistant", "Is there anything important we need to know about this condition, such as where inhalers are kept?"),
            ("user", "He keeps his inhaler in his bag"),
            ("assistant", "Thanks for that information. Did Seb play for another football team last season?"),
            
            # Routine 6 - Previous team
            ("user", "Yes, he played for Urmston Meds"),
            ("assistant", "What's your relationship to Seb?"),
            
            # Routine 7 - Parent relationship
            ("user", "I'm his dad"),
            ("assistant", "Could you provide your telephone number?"),
            
            # Routine 8 - Parent phone
            ("user", "07835 065 013"),
            ("assistant", "What's your email address?"),
            
            # Routine 9 - Parent email
            ("user", "junksamiad@gmail.com"),
            ("assistant", "Do you consent to receive club communications by email and SMS throughout the season?"),
            
            # Routine 10 - Communication consent
            ("user", "Yes, that's fine"),
            ("assistant", "Could you please provide your date of birth?"),
            
            # Routine 11 - Parent DOB
            ("user", "2nd June 1981"),
            ("assistant", "What's your postcode?"),
            
            # Routine 12 - Parent postcode
            ("user", "M32 8JL"),
            ("assistant", "What's your house number?"),
            
            # Routine 13 - Parent house number  
            ("user", "11"),
            ("assistant", "I found this address: 11 Granby Rd, Stretford, Manchester M32 8JL. Is this correct?"),
            
            # Routine 15 - Address confirmation
            ("user", "Yes, that's correct"),
            ("assistant", "Does Seb live at the same address?"),
            
            # Routine 16 - Child address same
            ("user", "Yes, same address"),
            
            # System would route to routine 22 for age check, then 28 for summary
            ("assistant", "Thanks Lee! Let me confirm all the details I've collected:\n\n**Your Details:**\n- Name: Lee Hayton\n- Relationship: Father\n- Phone: 07835 065 013\n- Email: junksamiad@gmail.com\n- DOB: 02-06-1981\n- Address: 11 Granby Rd, Stretford, Manchester M32 8JL\n\n**Seb's Details:**\n- Name: Seb Hayton\n- DOB: 18-07-2014\n- Gender: Male\n- Team: Leopards U9\n- Medical: Asthma (inhaler in bag)\n- Previous team: Urmston Meds\n- Address: Same as parent\n\n**Communication:** Consent given for club emails/SMS\n\nIs all this information correct?"),
            
            # Routine 28 - Confirmation
            ("user", "Yes, that's all correct"),
            ("assistant", "Brilliant! Now we need to collect the £45 signing-on fee and set up your £27.50 monthly Direct Debit (September to May). What's your preferred day of the month for the monthly payments?"),
        ]
        
        # Add all conversation history to session
        for role, message in conversation_history:
            add_message_to_session_history(current_session_id, role, message)
        
        # Generate message for routine 29 (payment day collection)
        cheat_message = "What's your preferred day of the month for the monthly subscription payment to come out (from September onwards)? (For example: 1st, 15th, 25th, or 'end of the month')"
        
        # Add cheat message to session history
        add_message_to_session_history(current_session_id, "assistant", cheat_message)
        
        # Return response that jumps to routine 29
        response_json = {
            "response": cheat_message,
            "last_agent": "new_registration", 
            "routine_number": 29  # Jump straight to payment day collection with full history
        }
        print(f"--- Session [{current_session_id}] RETURNING CHEAT CODE RESPONSE TO CLIENT: {response_json} ---")
        return response_json
    
    # Check for registration code and validate FIRST (before adding to history)
    validation_result = validate_and_route_registration(payload.user_message)
    
    # Handle validation errors for registration codes
    if not validation_result["valid"] and validation_result.get("error"):
        print(f"--- Session [{current_session_id}] Registration code validation failed: {validation_result['error']} ---")
        
        # Add user message to history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        
        # Return the standardized error message
        error_message = validation_result["error"]
        
        # Add error message to session history
        add_message_to_session_history(current_session_id, "assistant", error_message)
        
        response_json = {
            "response": error_message
        }
        print(f"--- Session [{current_session_id}] RETURNING VALIDATION ERROR TO CLIENT: {response_json} ---")
        return response_json
    
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
            
            # Add last_agent field for registration agent handoff tracking
            response_json = {
                "response": assistant_content_to_send,
                "last_agent": "re_registration"
            }
            print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
            return response_json
            
        elif route_type == "new_registration":
            print(f"--- Routing to new registration for team {registration_code['team']} {registration_code['age_group']} ---")
            
            # Add the registration code to session history
            add_message_to_session_history(current_session_id, "user", payload.user_message)
            
            # Inject structured registration data for age-based routing later
            from registration_agent.routing_validation import inject_structured_registration_data
            inject_structured_registration_data(current_session_id, payload.user_message)
            
            # Generate dynamic welcome message with team and age group info
            team = registration_code['team'].title()
            age_group = registration_code['age_group'].upper()
            
            welcome_message = f"""🎉 Great news! Your registration code is valid.

I'm here to help you register your child for the {team} {age_group} team this season.

The registration process is quick and straightforward. I'll ask you for some basic information about you and your child, and then we'll get you set up.

Can I take your first and last name so I know how to refer to you?"""
            
            print(f"--- Session [{current_session_id}] Generated welcome message for new registration ---")
            
            # Add welcome message to session history
            add_message_to_session_history(current_session_id, "assistant", welcome_message)
            
                         # Return static welcome message with last_agent and routine_number tracking
            response_json = {
                "response": welcome_message,
                "last_agent": "new_registration",
                "routine_number": 1  # Set initial routine number
            }
            print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
            return response_json
    
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
    
    response_json = {"response": assistant_content_to_send}
    print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
    return response_json

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