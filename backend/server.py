# This file will be populated with the content of simple_test_backend/main.py
# The old simple_test_backend/main.py will be deleted by a subsequent operation. 

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from typing import Optional
import uvicorn
import json
import os
import tempfile
import asyncio
from pathlib import Path
import threading
from datetime import datetime

from urmston_town_agent.responses import chat_loop_1
from urmston_town_agent.chat_history import get_session_history, add_message_to_session_history, clear_session_history, DEFAULT_SESSION_ID, set_session_context
from urmston_town_agent.agents import Agent # Import the Agent class

# Import registration agent components
from registration_agent.routing_validation import validate_and_route_registration
from registration_agent.registration_agents import re_registration_agent, new_registration_agent
from registration_agent.registration_routines import RegistrationRoutines
from registration_agent.responses_reg import chat_loop_new_registration_1, chat_loop_renew_registration_1
import time

app = FastAPI()

def retry_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0, session_id="unknown", call_type="AI"):
    """
    Retry an AI function call with exponential backoff when parsing fails.
    
    Args:
        ai_call_func: The AI function to call (e.g., chat_loop_new_registration_1)
        *args: Arguments to pass to the AI function
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        session_id: Session ID for logging
        call_type: Type of AI call for logging (e.g., "registration", "photo upload")
    
    Returns:
        tuple: (success, ai_response_object, parsed_content, routine_number)
               success: bool - whether parsing was successful
               ai_response_object: the raw AI response
               parsed_content: the parsed message content (or error message)
               routine_number: extracted routine number (or None)
    """
    for attempt in range(max_retries + 1):
        try:
            print(f"--- Session [{session_id}] {call_type} AI call attempt {attempt + 1}/{max_retries + 1} ---")
            
            # Call the AI function
            ai_full_response_object = ai_call_func(*args)
            
            # Attempt to parse the response
            parsed_content = f"Error: Could not parse {call_type.lower()} AI response for frontend."
            routine_number = None
            
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
                                    parsed_content = structured_response['agent_final_response']
                                    print(f"--- Session [{session_id}] Successfully parsed {call_type} response on attempt {attempt + 1} ---")
                                    if 'routine_number' in structured_response:
                                        routine_number = structured_response['routine_number']
                                    return True, ai_full_response_object, parsed_content, routine_number
                                else:
                                    print(f"--- Session [{session_id}] Missing 'agent_final_response' in structured response ---")
                            else:
                                parsed_content = text_content
                                print(f"--- Session [{session_id}] Response not a dict, using raw text ---")
                                return True, ai_full_response_object, parsed_content, routine_number
                        except json.JSONDecodeError as e:
                            print(f"--- Session [{session_id}] JSON decode error on attempt {attempt + 1}: {e} ---")
                            parsed_content = ai_full_response_object.output[0].content[0].text
                            return True, ai_full_response_object, parsed_content, routine_number
                            
            except Exception as parse_error:
                print(f"--- Session [{session_id}] Parse error on attempt {attempt + 1}: {parse_error} ---")
                
                # If this is the last attempt, return the failed response
                if attempt == max_retries:
                    print(f"--- Session [{session_id}] All {max_retries + 1} attempts failed, returning error ---")
                    return False, ai_full_response_object, parsed_content, routine_number
                
                # Wait before retrying (exponential backoff)
                wait_time = delay * (2 ** attempt)
                print(f"--- Session [{session_id}] Retrying in {wait_time} seconds... ---")
                time.sleep(wait_time)
                
        except Exception as ai_error:
            print(f"--- Session [{session_id}] AI call error on attempt {attempt + 1}: {ai_error} ---")
            
            # If this is the last attempt, return the failed response
            if attempt == max_retries:
                print(f"--- Session [{session_id}] All {max_retries + 1} attempts failed due to AI errors ---")
                return False, None, f"Error: {call_type} AI call failed after {max_retries + 1} attempts", None
            
            # Wait before retrying (exponential backoff)
            wait_time = delay * (2 ** attempt)
            print(f"--- Session [{session_id}] Retrying in {wait_time} seconds... ---")
            time.sleep(wait_time)
    
    # Should never reach here, but just in case
    return False, None, f"Error: {call_type} AI call failed unexpectedly", None


def retry_rereg_ai_call_with_parsing(ai_call_func, *args, max_retries=3, delay=1.0, session_id="unknown"):
    """
    Retry a re-registration AI function call with exponential backoff when parsing fails.
    Re-registration uses a different response structure (output_text instead of output[0].content[0].text).
    
    Args:
        ai_call_func: The AI function to call (e.g., chat_loop_renew_registration_1)
        *args: Arguments to pass to the AI function
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        session_id: Session ID for logging
    
    Returns:
        tuple: (success, ai_response_object, parsed_content)
               success: bool - whether parsing was successful
               ai_response_object: the raw AI response
               parsed_content: the parsed message content (or error message)
    """
    for attempt in range(max_retries + 1):
        try:
            print(f"--- Session [{session_id}] Re-registration AI call attempt {attempt + 1}/{max_retries + 1} ---")
            
            # Call the AI function
            ai_full_response_object = ai_call_func(*args)
            
            # Attempt to parse the response
            parsed_content = "Error: Could not parse re-registration AI response for frontend."
            
            try:
                # Handle structured output from Responses API (re-registration specific)
                if hasattr(ai_full_response_object, 'output_text') and ai_full_response_object.output_text:
                    try:
                        # Parse the structured JSON response
                        structured_response = json.loads(ai_full_response_object.output_text)
                        if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                            parsed_content = structured_response['agent_final_response']
                            print(f"--- Session [{session_id}] Successfully parsed re-registration response on attempt {attempt + 1} ---")
                            return True, ai_full_response_object, parsed_content
                        else:
                            # Fallback to raw output_text if not properly structured
                            parsed_content = ai_full_response_object.output_text
                            print(f"--- Session [{session_id}] Using raw output_text as fallback ---")
                            return True, ai_full_response_object, parsed_content
                    except json.JSONDecodeError as e:
                        print(f"--- Session [{session_id}] JSON decode error on attempt {attempt + 1}: {e}, using raw output_text ---")
                        parsed_content = ai_full_response_object.output_text
                        return True, ai_full_response_object, parsed_content
                        
                # Fallback to detailed parsing for Responses API (if output_text not available)
                elif hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                    if (len(ai_full_response_object.output) > 0 and 
                        hasattr(ai_full_response_object.output[0], 'content') and 
                        ai_full_response_object.output[0].content and 
                        len(ai_full_response_object.output[0].content) > 0 and
                        hasattr(ai_full_response_object.output[0].content[0], 'text')):
                        
                        try:
                            text_content = ai_full_response_object.output[0].content[0].text
                            structured_response = json.loads(text_content)
                            if isinstance(structured_response, dict) and 'agent_final_response' in structured_response:
                                parsed_content = structured_response['agent_final_response']
                                print(f"--- Session [{session_id}] Successfully parsed re-registration detailed response on attempt {attempt + 1} ---")
                                return True, ai_full_response_object, parsed_content
                            else:
                                parsed_content = text_content
                                return True, ai_full_response_object, parsed_content
                        except json.JSONDecodeError as e:
                            print(f"--- Session [{session_id}] JSON decode error in detailed parsing: {e} ---")
                            parsed_content = ai_full_response_object.output[0].content[0].text
                            return True, ai_full_response_object, parsed_content
                            
            except Exception as parse_error:
                print(f"--- Session [{session_id}] Re-registration parse error on attempt {attempt + 1}: {parse_error} ---")
                
                # If this is the last attempt, return the failed response
                if attempt == max_retries:
                    print(f"--- Session [{session_id}] All {max_retries + 1} re-registration attempts failed, returning error ---")
                    return False, ai_full_response_object, parsed_content
                
                # Wait before retrying (exponential backoff)
                wait_time = delay * (2 ** attempt)
                print(f"--- Session [{session_id}] Retrying re-registration in {wait_time} seconds... ---")
                time.sleep(wait_time)
                
        except Exception as ai_error:
            print(f"--- Session [{session_id}] Re-registration AI call error on attempt {attempt + 1}: {ai_error} ---")
            
            # If this is the last attempt, return the failed response
            if attempt == max_retries:
                print(f"--- Session [{session_id}] All {max_retries + 1} re-registration attempts failed due to AI errors ---")
                return False, None, f"Error: Re-registration AI call failed after {max_retries + 1} attempts"
            
            # Wait before retrying (exponential backoff)
            wait_time = delay * (2 ** attempt)
            print(f"--- Session [{session_id}] Retrying re-registration in {wait_time} seconds... ---")
            time.sleep(wait_time)
    
    # Should never reach here, but just in case
    return False, None, "Error: Re-registration AI call failed unexpectedly"


# In-memory storage for upload processing status
upload_status_store = {}
status_lock = threading.Lock()

def set_upload_status(session_id: str, status: dict):
    """Thread-safe status update"""
    with status_lock:
        upload_status_store[session_id] = {
            **status,
            'updated_at': datetime.now().isoformat()
        }

def get_upload_status(session_id: str) -> dict:
    """Thread-safe status retrieval"""
    with status_lock:
        return upload_status_store.get(session_id, {'complete': False, 'message': 'Not found'})

def process_photo_background(session_id: str, temp_file_path: str, routine_number: int, last_agent: str):
    """Background task to process photo upload with AI agent"""
    try:
        print(f"--- Background processing started for session [{session_id}] ---")
        
        # Set initial processing status
        set_upload_status(session_id, {
            'complete': False,
            'message': 'Processing photo with AI...',
            'progress': 'ai_processing'
        })
        
        # Get session history
        session_history = get_session_history(session_id)
        
        # Route to photo upload routine (assuming this is routine 34)
        upload_routine_number = 34
        routine_message = RegistrationRoutines.get_routine_message(upload_routine_number)
        
        if not routine_message:
            set_upload_status(session_id, {
                'complete': True,
                'error': True,
                'response': 'Photo upload routine not configured',
                'last_agent': last_agent,
                'routine_number': routine_number
            })
            return
        
        print(f"--- Background session [{session_id}] Using photo upload routine: {routine_message[:100]}... ---")
        
        # Create dynamic agent for photo upload
        dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_message)
        
        from registration_agent.agents_reg import Agent
        dynamic_agent = Agent(
            name=new_registration_agent.name,
            model=new_registration_agent.model,
            instructions=dynamic_instructions,
            tools=new_registration_agent.tools,
            use_mcp=new_registration_agent.use_mcp
        )
        
        # Set the current session ID in environment for the upload tool to access
        os.environ['CURRENT_SESSION_ID'] = session_id
        
        # Route to AI agent for photo validation and processing
        print(f"--- Background session [{session_id}] Routing to AI agent for photo validation and upload ---")
        
        # Use the special photo validation chat function for routine 34
        from registration_agent.responses_reg import chat_loop_new_registration_with_photo
        ai_full_response_object = chat_loop_new_registration_with_photo(dynamic_agent, session_history, session_id)
        
        # Parse the AI response
        assistant_content_to_send = "✅ Photo uploaded successfully! Your registration is now complete pending payment setup. Please use the payment link sent to you via SMS to complete your monthly subscription setup. If you experience any issues, please contact the club at admin@urmstontownjfc.co.uk. We look forward to seeing you on the pitch! ⚽🏃‍♂️🎉"
        routine_number_from_agent = None
        
        try:
            print(f"Background session [{session_id}] AI response object type: {type(ai_full_response_object)}")
            print(f"Background session [{session_id}] AI response object: {ai_full_response_object}")
            
            if hasattr(ai_full_response_object, 'output') and ai_full_response_object.output:
                print(f"Background session [{session_id}] Found output, length: {len(ai_full_response_object.output)}")
                if (len(ai_full_response_object.output) > 0 and 
                    hasattr(ai_full_response_object.output[0], 'content') and 
                    ai_full_response_object.output[0].content and 
                    len(ai_full_response_object.output[0].content) > 0 and
                    hasattr(ai_full_response_object.output[0].content[0], 'text')):
                    
                    text_content = ai_full_response_object.output[0].content[0].text
                    print(f"Background session [{session_id}] Raw text content: {text_content}")
                    
                    try:
                        structured_response = json.loads(text_content)
                        print(f"Background session [{session_id}] Parsed JSON: {structured_response}")
                        if isinstance(structured_response, dict):
                            assistant_content_to_send = structured_response.get("response", assistant_content_to_send)
                            routine_number_from_agent = structured_response.get("routine_number")
                        else:
                            assistant_content_to_send = str(structured_response)
                    except (json.JSONDecodeError, TypeError, AttributeError) as parse_error:
                        print(f"Background session [{session_id}] JSON parse failed, using text directly: {parse_error}")
                        assistant_content_to_send = text_content
                else:
                    print(f"Background session [{session_id}] AI response structure unexpected")
                    assistant_content_to_send = "✅ Photo uploaded and processed successfully!"
            else:
                print(f"Background session [{session_id}] No output found in AI response")
                assistant_content_to_send = "✅ Photo uploaded and processed successfully!"
                
        except Exception as response_error:
            print(f"Background session [{session_id}] Response parsing error: {response_error}")
            assistant_content_to_send = "✅ Photo uploaded successfully! Registration details have been saved."
        
        # Store successful completion
        set_upload_status(session_id, {
            'complete': True,
            'error': False,
            'response': assistant_content_to_send,
            'last_agent': last_agent,
            'routine_number': routine_number_from_agent or routine_number
        })
        
        print(f"--- Background processing completed for session [{session_id}] ---")
        
    except Exception as e:
        print(f"--- Background processing failed for session [{session_id}]: {e} ---")
        set_upload_status(session_id, {
            'complete': True,
            'error': True,
            'response': f'Photo processing failed: {str(e)}',
            'last_agent': last_agent,
            'routine_number': routine_number
        })
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"--- Cleaned up temp file: {temp_file_path} ---")
        except Exception as cleanup_error:
            print(f"--- Failed to clean up temp file {temp_file_path}: {cleanup_error} ---")

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
    
    # Start SMS metrics background processor
    try:
        from registration_agent.tools.registration_tools.sms_metrics_queue import start_sms_processor
        import asyncio
        
        # Start the SMS processor in the background (every 30 seconds)
        asyncio.create_task(start_sms_processor(interval_seconds=30))
        print("🚀 SMS metrics background processor started")
        
    except Exception as e:
        print(f"⚠️ Failed to start SMS metrics processor: {e}")

@app.get("/")
async def read_root():
    return {"message": "Hello from the Refactored Simple Test Backend with History and Agents!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "UTJFC Registration Backend is running"}

@app.get("/upload-status/{session_id}")
async def get_upload_processing_status(session_id: str):
    """Get the current status of photo upload processing"""
    status = get_upload_status(session_id)
    return status

@app.post("/upload-async")
async def upload_file_async_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    routine_number: Optional[int] = Form(None),
    last_agent: Optional[str] = Form(None)
):
    """Handle file uploads for player registration photos - ASYNC VERSION"""
    print(f"--- Session [{session_id}] ASYNC File upload received: {file.filename} ({file.content_type}, {file.size if hasattr(file, 'size') else 'unknown'} bytes) ---")
    
    # Validate file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic']
    if file.content_type not in allowed_types:
        return {"error": f"Invalid file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"}
    
    try:
        # Read file content and save to temporary file
        content = await file.read()
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.write(content)
        temp_file.close()
        
        print(f"--- Session [{session_id}] ASYNC File saved to temporary location: {temp_file.name} ---")
        
        # Add user message to session history
        add_message_to_session_history(session_id, "user", f"📎 Uploaded photo: {file.filename}")
        
        # Add the uploaded file path as a system message so the AI can access it
        add_message_to_session_history(session_id, "system", f"UPLOADED_FILE_PATH: {temp_file.name}")
        
        # Set initial status as processing
        set_upload_status(session_id, {
            'complete': False,
            'message': 'Photo received! Processing...',
            'progress': 'received'
        })
        
        # Start background processing in a separate thread
        import threading
        background_thread = threading.Thread(
            target=process_photo_background,
            args=(session_id, temp_file.name, routine_number or 34, last_agent or "new_registration")
        )
        background_thread.daemon = True
        background_thread.start()
        
        # Return immediately with dummy response and processing flag
        response_json = {
            "response": "📸 Photo Received. Processing your registration, please wait whilst we verify and upload your image. This could take between 30-90 seconds so please keep the chat open until we have completed this check.",
            "processing": True,
            "session_id": session_id,
            "last_agent": last_agent or "new_registration",
            "routine_number": routine_number or 34
        }
        
        print(f"--- Session [{session_id}] RETURNING IMMEDIATE ASYNC RESPONSE: {response_json} ---")
        print(f"--- Session [{session_id}] Background processing started in separate thread ---")
        return response_json
    
    except Exception as e:
        print(f"--- Session [{session_id}] Error in async upload endpoint: {e} ---")
        return {"error": f"File upload failed: {str(e)}"}

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
        
        # Use new registration flow with dynamic agent and retry mechanism
        success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
            chat_loop_new_registration_1, 
            dynamic_agent, 
            session_history, 
            current_session_id,
            max_retries=3,
            session_id=current_session_id,
            call_type="Registration"
        )
        
        # Process the response
        print(f"--- Session [{current_session_id}] Routine-based Registration AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant"
        
        if success:
            print(f"--- Session [{current_session_id}] Successfully parsed registration response ---")
            if routine_number_from_agent:
                print(f"--- Session [{current_session_id}] Agent set routine_number to: {routine_number_from_agent} ---")
        else:
            print(f"--- Session [{current_session_id}] Failed to parse registration response after retries ---")
        
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
        
        # Use new registration flow with dynamic agent and retry mechanism
        success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
            chat_loop_new_registration_1, 
            dynamic_agent, 
            session_history, 
            current_session_id,
            max_retries=3,
            session_id=current_session_id,
            call_type="Registration Continuation"
        )
        
        # Process the response
        print(f"--- Session [{current_session_id}] Registration continuation AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant"
        
        if success:
            print(f"--- Session [{current_session_id}] Successfully parsed registration continuation response ---")
            if routine_number_from_agent:
                print(f"--- Session [{current_session_id}] Agent set routine_number to: {routine_number_from_agent} ---")
        else:
            print(f"--- Session [{current_session_id}] Failed to parse registration continuation response after retries ---")
        
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
        
        # Use re-registration flow with retry mechanism
        success, ai_full_response_object, assistant_content_to_send = retry_rereg_ai_call_with_parsing(
            chat_loop_renew_registration_1, 
            re_registration_agent, 
            session_history,
            max_retries=3,
            session_id=current_session_id
        )
        
        # Process the re-registration agent response
        print(f"--- Session [{current_session_id}] Re-registration continuation AI Response Object: ---")
        print(ai_full_response_object)
        
        assistant_role_to_store = "assistant"
        
        if success:
            print(f"--- Session [{current_session_id}] Successfully parsed re-registration continuation response ---")
        else:
            print(f"--- Session [{current_session_id}] Failed to parse re-registration continuation response after retries ---")
        
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
        
        # Add explicit registration code for AI agent to extract
        add_message_to_session_history(current_session_id, "system", "REGISTRATION_CODE: 200-leopards-u9-2526")
        
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
            ("assistant", "Thanks for that information. Did Seb play for Urmston Town last season?"),
            
            # Routine 6 - Previous team
            ("user", "Yes"),
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
            ("assistant", "Thanks Lee! Let me confirm all the details I've collected:\n\n**Your Details:**\n- Name: Lee Hayton\n- Relationship: Father\n- Phone: 07835 065 013\n- Email: junksamiad@gmail.com\n- DOB: 02-06-1981\n- Address: 11 Granby Rd, Stretford, Manchester M32 8JL\n\n**Seb's Details:**\n- Name: Seb Hayton\n- DOB: 18-07-2014\n- Gender: Male\n- Team: Leopards U9\n- Medical: Asthma (inhaler in bag)\n- Address: Same as parent\n\n**Communication:** Consent given for club emails/SMS\n\nIs all this information correct?"),
            
            # Routine 28 - Confirmation
            ("user", "Yes, that's all correct"),
            ("assistant", "Brilliant! Now we need to collect the £1 signing-on fee and set up your £1 monthly Direct Debit (September to May). What's your preferred day of the month for the monthly payments?"),
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
    
    # Check for extended testing cheat code 'sdh' (Skip to Photo Upload)
    if payload.user_message.strip().lower() == "sdh":
        print(f"--- Session [{current_session_id}] Extended testing cheat code 'sdh' detected - jumping directly to routine 34 (photo upload) with full registration completed ---")
        
        # Add the cheat code to session history
        add_message_to_session_history(current_session_id, "user", payload.user_message)
        
        # Inject structured registration data for age-based routing
        from registration_agent.routing_validation import inject_structured_registration_data
        inject_structured_registration_data(current_session_id, "200-leopards-u9-2526")
        
        # Add explicit registration code for AI agent to extract
        add_message_to_session_history(current_session_id, "system", "REGISTRATION_CODE: 200-leopards-u9-2526")
        
        # Pre-populate complete conversation history (routines 1-28) - same as 'lah'
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
            ("assistant", "Thanks for that information. Did Seb play for Urmston Town last season?"),
            
            # Routine 6 - Previous team
            ("user", "Yes"),
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
            ("assistant", "Thanks Lee! Let me confirm all the details I've collected:\n\n**Your Details:**\n- Name: Lee Hayton\n- Relationship: Father\n- Phone: 07835 065 013\n- Email: junksamiad@gmail.com\n- DOB: 02-06-1981\n- Address: 11 Granby Rd, Stretford, Manchester M32 8JL\n\n**Seb's Details:**\n- Name: Seb Hayton\n- DOB: 18-07-2014\n- Gender: Male\n- Team: Leopards U9\n- Medical: Asthma (inhaler in bag)\n- Address: Same as parent\n\n**Communication:** Consent given for club emails/SMS\n\nIs all this information correct?"),
            
            # Routine 28 - Confirmation
            ("user", "Yes, that's all correct"),
            ("assistant", "Brilliant! Now we need to collect the £1 signing-on fee and set up your £1 monthly Direct Debit (September to May). What's your preferred day of the month for the monthly payments?"),
            
            # Routine 29 - Payment day (auto-completed)
            ("user", "15th"),
            ("assistant", "Perfect! I'm now creating your payment link..."),
            
            # Routine 29 completion - Payment link confirmation
            ("user", "Yes, I've received the payment link"),
            ("assistant", "Great! Now let's sort out Seb's kit. What size would you like for the shirt and shorts?"),
            
            # Routine 33 - Kit size (auto-completed)
            ("user", "9-10"),
            ("assistant", "Perfect! Finally, what shirt number would Seb like? (1-99)"),
            
            # Routine 33 - Shirt number (auto-completed)
            ("user", "19"),
            ("assistant", "Excellent! The only thing left is to upload a passport-style photo of Seb for registration. Please use the + symbol in the chat window to upload a clear photo of Seb (similar style to a school or passport picture)."),
        ]
        
        # Add all conversation history to session
        for role, message in conversation_history:
            add_message_to_session_history(current_session_id, role, message)
        
        # Now execute the actual tool calls to create real database records
        print(f"--- Session [{current_session_id}] Executing real tool calls for complete registration ---")
        
        try:
            # Import the tools we need
            from registration_agent.tools.registration_tools.create_payment_token import create_payment_token
            from registration_agent.tools.registration_tools.update_reg_details_to_db_tool_ai_friendly import update_reg_details_to_db
            from registration_agent.tools.registration_tools.check_shirt_number_availability import check_shirt_number_availability
            from registration_agent.tools.registration_tools.update_kit_details_to_db import update_kit_details_to_db
            
            # 1. Create payment token (routine 29 tool call)
            print(f"--- Session [{current_session_id}] Creating payment token ---")
            payment_result = create_payment_token(
                parent_first_name="Lee",
                parent_last_name="Hayton", 
                parent_email="junksamiad@gmail.com",
                parent_phone="07835065013",
                player_first_name="Seb",
                player_last_name="Hayton",
                registration_code="200-leopards-u9-2526",
                preferred_payment_day=15,
                monthly_amount=300  # £3.00 test amount
            )
            print(f"--- Session [{current_session_id}] Payment token result: {payment_result} ---")
            
            # 2. Update registration details to database
            print(f"--- Session [{current_session_id}] Updating registration details to database ---")
            db_result = update_reg_details_to_db(
                registration_code="200-leopards-u9-2526",
                parent_full_name="Lee Hayton",
                parent_first_name="Lee",
                parent_last_name="Hayton",
                parent_email="junksamiad@gmail.com", 
                parent_phone="07835065013",
                parent_dob="02-06-1981",
                parent_relationship_to_player="Father",
                parent_address_line_1="11 Granby Rd",
                parent_town="Stretford",
                parent_city="Manchester",
                parent_full_address="11 Granby Rd, Stretford, Manchester M32 8JL",
                parent_post_code="M32 8JL",
                parent_house_number="11",
                communication_consent="Y",
                player_full_name="Seb Hayton",
                player_first_name="Seb",
                player_last_name="Hayton", 
                player_dob="18-07-2014",
                player_gender="Male",
                player_address_line_1="11 Granby Rd",
                player_town="Stretford",
                player_city="Manchester",
                player_full_address="11 Granby Rd, Stretford, Manchester M32 8JL",
                player_post_code="M32 8JL",
                player_house_number="11",
                player_has_any_medical_issues="Y",
                description_of_player_medical_issues="Asthma (inhaler in bag)",
                played_for_urmston_town_last_season="Y",
                team="Leopards",
                age_group="u9",
                registration_type="200",
                season="2526",
                billing_request_id=payment_result.get("billing_request_id", "TEST_BILLING_ID"),
                preferred_payment_day=15,
                signing_on_fee_amount=payment_result.get("signing_fee_amount_pounds", 1.0),
                monthly_subscription_amount=payment_result.get("monthly_amount_pounds", 3.0)
            )
            print(f"--- Session [{current_session_id}] Database update result: {db_result} ---")
            
            # 3. Check shirt number availability (routine 33)
            print(f"--- Session [{current_session_id}] Checking shirt number availability ---")
            number_check = check_shirt_number_availability(
                registration_code="200-leopards-u9-2526",
                requested_number=19
            )
            print(f"--- Session [{current_session_id}] Number check result: {number_check} ---")
            
            # 4. Update kit details to database (routine 33) 
            print(f"--- Session [{current_session_id}] Updating kit details to database ---")
            kit_result = update_kit_details_to_db(
                registration_code="200-leopards-u9-2526",
                kit_size="9-10",
                shirt_number=19
            )
            print(f"--- Session [{current_session_id}] Kit update result: {kit_result} ---")
            
            print(f"--- Session [{current_session_id}] All tool calls completed successfully ---")
            
        except Exception as e:
            print(f"--- Session [{current_session_id}] Error executing tool calls: {e} ---")
        
        # Generate final message for routine 34 (photo upload)
        cheat_message = "The only thing left is to upload a passport-style photo of Seb for registration. Please use the + symbol in the chat window to upload a clear photo of Seb (similar style to a school or passport picture)."
        
        # Add final message to session history
        add_message_to_session_history(current_session_id, "assistant", cheat_message)
        
        # Return response that jumps to routine 34 (photo upload) with complete registration
        response_json = {
            "response": cheat_message,
            "last_agent": "new_registration", 
            "routine_number": 34  # Jump straight to photo upload with full registration completed
        }
        print(f"--- Session [{current_session_id}] RETURNING EXTENDED CHEAT CODE RESPONSE TO CLIENT: {response_json} ---")
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
        
        # Store the raw registration code in session context for later retrieval
        raw_registration_code = payload.user_message.strip()
        set_session_context(current_session_id, "registration_code", raw_registration_code)
        
        if route_type == "re_registration":
            print(f"--- Routing to re-registration agent for {registration_code.get('player_name', 'player')} ---")
            if player_details:
                print(f"--- Player found in database: {player_details} ---")
            
            # Add the registration code to session history
            add_message_to_session_history(current_session_id, "user", payload.user_message)
            session_history = get_session_history(current_session_id)
            
            # Use re-registration flow with retry mechanism
            success, ai_full_response_object, assistant_content_to_send = retry_rereg_ai_call_with_parsing(
                chat_loop_renew_registration_1, 
                re_registration_agent, 
                session_history,
                max_retries=3,
                session_id=current_session_id
            )
            
            # Process the re-registration agent response
            print(f"--- Session [{current_session_id}] Re-registration AI Response Object: ---")
            print(ai_full_response_object)
            print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\n")

            print(f"--- Session [{current_session_id}] Attempting to parse re-registration structured response ---")

            assistant_role_to_store = "assistant"
            
            if success:
                print(f"--- Session [{current_session_id}] Successfully parsed re-registration initial response ---")
            else:
                print(f"--- Session [{current_session_id}] Failed to parse re-registration initial response after retries ---")
            
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
            
            welcome_message = f"""🎉 **Great news!** Your registration code is valid.

I'm here to help you register your child for the **{team} {age_group}** team this season.

The registration process is quick and straightforward. I'll ask you for some basic information about you and your child, and then we'll get you set up.

## 📋 Before We Begin

Please note:

1. **📸 Have a photo ready** - You'll need to upload a passport-style photo of your child from your device to complete registration
2. **📱 SMS payment link** - You'll receive a payment link via SMS during this process. Please don't close this chat when you get the SMS - you can complete payment anytime after our chat finishes
3. **⏳ Processing time** - If any of my responses feel like they are taking a bit longer than normal, please stay in the chat as I'm working behind the scenes to save your information
4. **🎉 Sibling discount** - If you're registering an additional child (sibling) with the same surname, a 10% discount will automatically be applied to their monthly subscription payment

---

Ready to get started? **Can I take your first and last name so I know how to refer to you?**"""
            
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
    
    # Get AI response using the agent with retry mechanism
    success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
        chat_loop_1, 
        default_agent, 
        session_history,
        max_retries=3,
        session_id=current_session_id,
        call_type="Universal Agent"
    )
    
    print(f"--- Session [{current_session_id}] Full AI Response Object: ---")
    print(ai_full_response_object)
    print(f"--- Type of Response Object: {type(ai_full_response_object)} ---\n")

    print(f"--- Session [{current_session_id}] Attempting to parse structured response ---")

    assistant_role_to_store = "assistant"
    
    if success:
        print(f"--- Session [{current_session_id}] Successfully parsed universal agent response ---")
    else:
        print(f"--- Session [{current_session_id}] Failed to parse universal agent response after retries ---")
    
    print(f"--- Session [{current_session_id}] Final assistant content to send: {assistant_content_to_send} ---")
    
    # Add assistant response to session history
    add_message_to_session_history(current_session_id, assistant_role_to_store, assistant_content_to_send)
    
    response_json = {"response": assistant_content_to_send}
    print(f"--- Session [{current_session_id}] RETURNING JSON TO CLIENT: {response_json} ---")
    return response_json

@app.post("/upload")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    routine_number: Optional[int] = Form(None),
    last_agent: Optional[str] = Form(None)
):
    """Handle file uploads for player registration photos"""
    print(f"--- Session [{session_id}] File upload received: {file.filename} ({file.content_type}, {file.size if hasattr(file, 'size') else 'unknown'} bytes) ---")
    
    # Validate file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/heic']
    if file.content_type not in allowed_types:
        return {"error": f"Invalid file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"}
    
    # Create temporary file
    temp_file = None
    try:
        # Read file content
        content = await file.read()
        
        # Create temporary file with correct extension
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.write(content)
        temp_file.close()
        
        print(f"--- Session [{session_id}] File saved to temporary location: {temp_file.name} ---")
        
        # Add user message to session history
        add_message_to_session_history(session_id, "user", f"📎 Uploaded photo: {file.filename}")
        session_history = get_session_history(session_id)
        
        # Route to photo upload routine (assuming this is routine 34)
        upload_routine_number = 34
        routine_message = RegistrationRoutines.get_routine_message(upload_routine_number)
        
        if not routine_message:
            return {"error": "Photo upload routine not configured"}
        
        print(f"--- Session [{session_id}] Using photo upload routine: {routine_message} ---")
        
        # Create dynamic agent for photo upload
        dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_message)
        
        from registration_agent.agents_reg import Agent
        dynamic_agent = Agent(
            name=new_registration_agent.name,
            model=new_registration_agent.model,
            instructions=dynamic_instructions,
            tools=new_registration_agent.tools,
            use_mcp=new_registration_agent.use_mcp
        )
        
        # Add the uploaded file path as a system message so the AI can access it
        add_message_to_session_history(session_id, "system", f"UPLOADED_FILE_PATH: {temp_file.name}")
        
        # Set the current session ID in environment for the upload tool to access
        os.environ['CURRENT_SESSION_ID'] = session_id
        
        # Get updated session history including the file path
        session_history = get_session_history(session_id)
        
        # Route to AI agent for photo validation and processing
        print(f"--- Session [{session_id}] Routing to AI agent for photo validation and upload ---")
        
        # Use the special photo validation chat function for routine 34 with retry mechanism
        from registration_agent.responses_reg import chat_loop_new_registration_with_photo
        success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
            chat_loop_new_registration_with_photo,
            dynamic_agent,
            session_history,
            session_id,
            max_retries=3,
            session_id=session_id,
            call_type="Photo Upload"
        )
        
        if success:
            print(f"--- Session [{session_id}] Successfully parsed photo upload response ---")
            if routine_number_from_agent:
                print(f"--- Session [{session_id}] AI agent set routine_number to: {routine_number_from_agent} ---")
        else:
            print(f"--- Session [{session_id}] Failed to parse photo upload response after retries ---")
        
        response_json = {
            "response": assistant_content_to_send,
            "last_agent": "new_registration",
            "routine_number": routine_number_from_agent or 34
        }
        
        # Add assistant response to session history
        add_message_to_session_history(session_id, "assistant", response_json["response"])
        
        print(f"--- Session [{session_id}] RETURNING UPLOAD RESPONSE: {response_json} ---")
        return response_json
        
    except Exception as e:
        print(f"--- Session [{session_id}] Error processing file upload: {e} ---")
        return {"error": f"File upload failed: {str(e)}"}
    
    finally:
        # Note: Temporary file cleanup is handled by upload_photo_to_s3 tool after processing
        pass

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

@app.get("/reg_setup/{billing_request_id}")
async def handle_payment_link(billing_request_id: str):
    """
    Payment link handler for SMS payment links
    
    This endpoint is called when parents click the payment link in their SMS.
    It looks up the registration, validates payment status, and redirects to GoCardless.
    """
    print(f"--- Payment link accessed: billing_request_id={billing_request_id} ---")
    
    try:
        # Import required modules
        from pyairtable import Api
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        # Get Airtable configuration
        BASE_ID = "appBLxf3qmGIBc6ue"
        TABLE_ID = "tbl1D7hdjVcyHbT8a"
        AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
        
        if not AIRTABLE_API_KEY:
            print("--- Payment link error: Missing Airtable API key ---")
            return {"error": "Configuration error - please contact support"}
        
        # 1. Lookup registration by billing_request_id
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_ID)
        
        # Search for registration with this billing request ID
        records = table.all(formula=f"{{billing_request_id}} = '{billing_request_id}'")
        
        if not records:
            print(f"--- Payment link error: No registration found for billing_request_id={billing_request_id} ---")
            return {"error": "Invalid payment link - registration not found"}
        
        registration = records[0]['fields']
        registration_id = records[0]['id']
        
        print(f"--- Payment link found registration: ID={registration_id}, Player={registration.get('player_first_name', 'Unknown')} {registration.get('player_last_name', '')} ---")
        
        # 2. Check if already paid (Airtable stores as 'Y'/'N' strings)
        signing_fee_paid = registration.get('signing_on_fee_paid', 'N') == 'Y'
        mandate_authorized = registration.get('mandate_authorised', 'N') == 'Y'
        
        print(f"--- Payment status check: signing_fee_paid={signing_fee_paid}, mandate_authorized={mandate_authorized} ---")
        
        if signing_fee_paid and mandate_authorized:
            print(f"--- Payment already completed for registration {registration_id} ---")
            return {
                "message": "Payment already completed",
                "player_name": f"{registration.get('player_first_name', '')} {registration.get('player_last_name', '')}",
                "status": "already_paid"
            }
        
        # 3. Generate fresh GoCardless authorization URL using existing billing request
        print(f"--- Generating authorization URL for existing billing_request_id={billing_request_id} ---")
        
        try:
            # Import the create_billing_request_flow function
            from registration_agent.tools.registration_tools.gocardless_payment import create_billing_request_flow
            
            # Extract parent data for prefilling the payment form
            parent_email = registration.get('parent_email', '')
            parent_first_name = registration.get('parent_first_name', '')
            parent_last_name = registration.get('parent_last_name', '')
            parent_address_line_1 = registration.get('parent_address_line_1', '')
            parent_city = registration.get('parent_city', '')
            parent_post_code = registration.get('parent_post_code', '')
            
            # Create billing request flow with prefilled data
            flow_result = create_billing_request_flow(
                billing_request_id=billing_request_id,
                parent_email=parent_email,
                parent_first_name=parent_first_name,
                parent_last_name=parent_last_name,
                parent_address_line1=parent_address_line_1,
                parent_city=parent_city,
                parent_postcode=parent_post_code
            )
            
            if flow_result.get('success') and flow_result.get('authorization_url'):
                authorization_url = flow_result['authorization_url']
                
                print(f"--- Redirecting to GoCardless authorization URL: {authorization_url} ---")
                
                # Return redirect response - this will open in user's browser
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=authorization_url, status_code=302)
            else:
                error_msg = flow_result.get('message', 'Failed to generate authorization URL')
                print(f"--- Authorization URL generation failed: {error_msg} ---")
                return {"error": f"Payment setup failed: {error_msg}"}
                
        except Exception as payment_error:
            print(f"--- Authorization URL generation exception: {str(payment_error)} ---")
            return {"error": f"Payment setup error: {str(payment_error)}"}
            
    except Exception as e:
        print(f"--- Payment link handler exception: {str(e)} ---")
        return {"error": f"Payment link processing failed: {str(e)}"}

@app.get("/webhooks/gocardless/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook is accessible"""
    return {"status": "Webhook endpoint is accessible", "timestamp": "2025-01-27"}

@app.post("/webhooks/gocardless")
async def handle_gocardless_webhook(request: Request):
    """
    Handle GoCardless webhook events for payment and mandate completion.
    
    Key events we handle:
    - payment_confirmed: Payment has been confirmed 
    - mandate_active: Mandate is now active
    - billing_request_fulfilled: Billing request completed
    """
    print("--- GoCardless webhook received ---")
    
    try:
        # Get the raw body for signature verification
        body = await request.body()
        webhook_signature = request.headers.get("webhook-signature")
        
        print(f"Webhook signature: {webhook_signature}")
        
        # TODO: Add proper signature verification when we have the secret
        # For now, we'll skip verification during development
        webhook_secret = os.getenv('GOCARDLESS_WEBHOOK_SECRET')
        if webhook_secret and webhook_signature:
            # Verify webhook signature
            if not verify_webhook_signature(body, webhook_signature, webhook_secret):
                print("Invalid webhook signature")
                return {"error": "Invalid signature"}, 401
        else:
            print("⚠️  Webhook signature verification disabled (development mode)")
            
        # Parse the webhook payload
        webhook_data = json.loads(body.decode('utf-8'))
        
        print(f"Webhook events count: {len(webhook_data.get('events', []))}")
        
        # Process each event
        for event in webhook_data.get('events', []):
            await process_gocardless_event(event)
            
        return {"status": "success"}
        
    except Exception as e:
        print(f"Error processing GoCardless webhook: {str(e)}")
        return {"error": "Webhook processing failed"}, 500

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify GoCardless webhook signature"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

async def process_gocardless_event(event: dict):
    """Process individual GoCardless webhook event"""
    
    event_id = event.get('id')
    resource_type = event.get('resource_type')
    action = event.get('action')
    
    print(f"Processing event {event_id}: {resource_type}.{action}")
    
    # Only process events we care about
    if resource_type == 'payments' and action == 'confirmed':
        # Check if this is a subscription payment or signing fee payment
        subscription_id = event.get('links', {}).get('subscription')
        if subscription_id:
            await handle_subscription_payment_confirmed(event)
        else:
            await handle_payment_confirmed(event)  # Existing signing fee handler
    elif resource_type == 'payments' and action == 'failed':
        subscription_id = event.get('links', {}).get('subscription')
        if subscription_id:
            await handle_subscription_payment_failed(event)
        else:
            print(f"⚠️  Non-subscription payment failed: {event.get('links', {}).get('payment')}")
    elif resource_type == 'payments' and action in ['cancelled', 'charged_back', 'submitted']:
        subscription_id = event.get('links', {}).get('subscription')
        if subscription_id:
            await handle_subscription_payment_status_change(event)
    elif resource_type == 'mandates' and action == 'active':
        await handle_mandate_active(event)
    elif resource_type == 'billing_requests' and action == 'fulfilled':
        await handle_billing_request_fulfilled(event)
    elif resource_type == 'payments' and action == 'paid_out':
        print(f"💰 Payment paid out: {event.get('links', {}).get('payment')} (informational only)")
    else:
        print(f"Ignoring event: {resource_type}.{action}")

async def handle_payment_confirmed(event: dict):
    """Handle payment confirmation - set signing_on_fee_paid = 'Y'"""
    
    payment_id = event.get('links', {}).get('payment')
    billing_request_id = event.get('links', {}).get('billing_request')
    
    if not payment_id:
        print("No payment ID in event")
        return
        
    print(f"💳 Payment confirmed: {payment_id}")
    
    # Import required modules
    from pyairtable import Api
    import os
    
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        # Find registration by billing_request_id if available
        if billing_request_id:
            records = table.all(formula=f"{{billing_request_id}} = '{billing_request_id}'")
            
            if records:
                record = records[0]
                record_id = record['id']
                player_name = f"{record['fields'].get('player_first_name', 'Unknown')} {record['fields'].get('player_last_name', '')}"
                
                # Update payment status and check if we should update registration status
                current_mandate_status = record['fields'].get('mandate_authorised', 'N')
                
                update_data = {'signing_on_fee_paid': 'Y'}
                
                # If mandate is NOT authorized, set status to incomplete (payment without mandate)
                if current_mandate_status != 'Y':
                    update_data['registration_status'] = 'incomplete'
                    print(f"⚠️  Payment confirmed but no mandate - setting status to 'incomplete'")
                
                table.update(record_id, update_data)
                
                print(f"✅ Payment confirmed for {player_name} - updated signing_on_fee_paid = 'Y'")
                if update_data.get('registration_status') == 'incomplete':
                    print(f"🚨 WARNING: {player_name} paid fee but NO MANDATE - flagged for manual follow-up")
            else:
                print(f"❌ No registration found for billing_request_id: {billing_request_id}")
        else:
            print(f"⚠️  No billing_request_id in payment event - cannot link to registration")
        
    except Exception as e:
        print(f"Error updating payment status: {str(e)}")

async def handle_mandate_active(event: dict):
    """Handle mandate activation - set mandate_authorised = 'Y' only"""
    
    event_mandate_id = event.get('links', {}).get('mandate')
    billing_request_id = event.get('links', {}).get('billing_request')
    
    if not event_mandate_id:
        print("No mandate ID in event")
        return
        
    print(f"📋 Mandate active (from event): {event_mandate_id}")
    print(f"ℹ️  Note: Subscription activation will happen in billing_request.fulfilled event")
    
    # Import required modules  
    from pyairtable import Api
    import os
    
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        # Find registration by billing_request_id if available
        if billing_request_id:
            records = table.all(formula=f"{{billing_request_id}} = '{billing_request_id}'")
            
            if records:
                record = records[0]
                record_id = record['id']
                fields = record['fields']
                player_name = f"{fields.get('player_first_name', 'Unknown')} {fields.get('player_last_name', '')}"
                
                # Update mandate status only - subscription activation moved to billing_request.fulfilled
                update_data = {'mandate_authorised': 'Y'}
                
                # Check if we should update registration status
                current_payment_status = fields.get('signing_on_fee_paid', 'N')
                current_reg_status = fields.get('registration_status', 'pending_payment')
                
                # If payment is already confirmed and status is incomplete, we can now mark as active
                if current_payment_status == 'Y' and current_reg_status == 'incomplete':
                    update_data['registration_status'] = 'active'
                    print(f"✅ Late mandate authorization - registration now active!")
                
                table.update(record_id, update_data)
                print(f"✅ Mandate active for {player_name} - updated mandate_authorised = 'Y'")
            else:
                print(f"❌ No registration found for billing_request_id: {billing_request_id}")
        else:
            print(f"⚠️  No billing_request_id in mandate event - cannot link to registration")
        
    except Exception as e:
        print(f"Error updating mandate status: {str(e)}")

async def handle_billing_request_fulfilled(event: dict):
    """Handle billing request fulfillment - final completion step with subscription activation"""
    
    billing_request_id = event.get('links', {}).get('billing_request')
    mandate_id = event.get('links', {}).get('mandate_request_mandate')
    
    if not billing_request_id:
        print("No billing request ID in event")
        return
        
    print(f"🏆 Billing request fulfilled: {billing_request_id}")
    
    if mandate_id:
        print(f"📋 Mandate ID from billing request: {mandate_id}")
    else:
        print("⚠️  No mandate_request_mandate in billing request fulfilled event")
    
    # Import required modules
    from pyairtable import Api
    import os
    
    try:
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        # Find registration by billing_request_id
        records = table.all(formula=f"{{billing_request_id}} = '{billing_request_id}'")
        
        if records:
            record = records[0]
            record_id = record['id']
            fields = record['fields']
            player_name = f"{fields.get('player_first_name', 'Unknown')} {fields.get('player_last_name', '')}"
            
            print(f"Found registration for {player_name} (Record: {record_id})")
            
            # This event means both payment AND mandate are successful
            update_data = {
                'signing_on_fee_paid': 'Y',
                'mandate_authorised': 'Y',
                'registration_status': 'active'
            }
            
            # If we have a mandate ID, activate the subscription
            if mandate_id:
                print(f"🔄 Activating subscription for {player_name}...")
                
                # Import the subscription activation function
                from registration_agent.tools.registration_tools.gocardless_payment import activate_subscription
                
                # Activate the subscription (function now pulls all data from record)
                subscription_result = activate_subscription(
                    mandate_id=mandate_id,
                    registration_record=record
                )
                
                if subscription_result.get('success'):
                    ongoing_subscription_id = subscription_result.get('ongoing_subscription_id')
                    interim_subscription_id = subscription_result.get('interim_subscription_id')
                    start_date = subscription_result.get('start_date')
                    interim_created = subscription_result.get('interim_created', False)
                    
                    # Store subscription details in database
                    update_data['ongoing_subscription_id'] = ongoing_subscription_id
                    update_data['subscription_start_date'] = start_date
                    update_data['subscription_status'] = 'active'
                    update_data['subscription_activated'] = 'Y'
                    
                    if interim_created and interim_subscription_id:
                        update_data['interim_subscription_id'] = interim_subscription_id
                    
                    print(f"✅ Subscription activated for {player_name}")
                    print(f"   - Ongoing Subscription ID: {ongoing_subscription_id}")
                    print(f"   - Start Date: {start_date}")
                    if interim_created:
                        print(f"   - Interim Subscription ID: {interim_subscription_id}")
                        print(f"   - Interim payment created for immediate month")
                    
                    monthly_amount = fields.get('monthly_subscription_amount', 27.5)
                    print(f"   - Monthly Amount: £{monthly_amount:.2f}")
                else:
                    print(f"❌ Failed to activate subscription for {player_name}: {subscription_result.get('message')}")
                    # Don't fail the mandate update if subscription fails - log for manual follow-up
                    update_data['subscription_status'] = 'failed'
                    update_data['subscription_error'] = subscription_result.get('message', 'Unknown error')
                
            else:
                print(f"⚠️  No mandate ID available - cannot activate subscription")
                update_data['subscription_status'] = 'failed'
                update_data['subscription_error'] = 'No mandate ID available in billing request fulfilled event'
            
            # Update the database
            table.update(record_id, update_data)
            
            print(f"✅ Registration completed for {player_name} (billing request fulfilled)")
            print(f"   - Both payment and mandate confirmed")
            print(f"   - registration_status: active")
            
            # Send confirmation SMS to parent
            await send_payment_confirmation_sms(fields)
            
        else:
            print(f"❌ No registration found for billing_request_id: {billing_request_id}")
            
    except Exception as e:
        print(f"Error processing billing request fulfillment: {str(e)}")

async def send_payment_confirmation_sms(registration_data: dict):
    """Send SMS confirmation when payment is completed"""
    
    try:
        parent_phone = registration_data.get('parent_telephone')
        player_name = f"{registration_data.get('player_first_name', '')} {registration_data.get('player_last_name', '')}"
        
        if not parent_phone:
            print("No parent phone number - skipping confirmation SMS")
            return
            
        # Format phone number for SMS
        if parent_phone.startswith('0'):
            formatted_phone = '+44' + parent_phone[1:]
        elif not parent_phone.startswith('+'):
            formatted_phone = '+44' + parent_phone
        else:
            formatted_phone = parent_phone
            
        # Create confirmation message
        message = f"✅ Payment confirmed! {player_name}'s registration for Urmston Town JFC is now complete. Direct debit set up for monthly fees. See you on the pitch! 🏆"
        
        # Send SMS using existing SMS function
        from registration_agent.tools.registration_tools.send_sms_payment_link_tool import format_uk_phone_for_twilio
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioException
        import os
        
        # Get Twilio credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_phone]):
            sms_result = {
                'success': False,
                'error': 'Missing Twilio configuration'
            }
        else:
            try:
                # Initialize Twilio client and send SMS
                client = Client(account_sid, auth_token)
                twilio_message = client.messages.create(
                    body=message,
                    from_=twilio_phone,
                    to=formatted_phone
                )
                sms_result = {
                    'success': True,
                    'message_sid': twilio_message.sid
                }
            except TwilioException as e:
                sms_result = {
                    'success': False,
                    'error': f'Twilio error: {str(e)}'
                }
        
        if sms_result.get('success'):
            print(f"✅ Confirmation SMS sent to {formatted_phone}")
        else:
            print(f"❌ Failed to send confirmation SMS: {sms_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error sending confirmation SMS: {str(e)}")

async def handle_subscription_payment_confirmed(event: dict):
    """Handle successful subscription payment - update monthly status field"""
    
    subscription_id = event.get('links', {}).get('subscription')
    payment_id = event.get('links', {}).get('payment')
    payment_date = event.get('created_at')  # e.g., "2024-10-15T10:30:00Z"
    
    if not subscription_id:
        print("No subscription ID in payment confirmed event")
        return
        
    print(f"💳 Subscription payment confirmed: {payment_id} for subscription {subscription_id}")
    
    try:
        # Import required modules
        from pyairtable import Api
        from datetime import datetime
        import os
        
        # Parse payment date to get month/year
        payment_datetime = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
        payment_month = payment_datetime.month
        payment_year = payment_datetime.year
        
        # Map to status field name
        status_field = get_subscription_status_field_for_month(payment_month, payment_year)
        
        if not status_field:
            print(f"⚠️  Payment date {payment_date} doesn't map to a season month - ignoring")
            return
        
        # Find registration by subscription ID
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        # Search for registration with this subscription ID
        records = table.all(formula=f"{{ongoing_subscription_id}} = '{subscription_id}'")
        
        if records:
            record = records[0]
            record_id = record['id']
            player_name = f"{record['fields'].get('player_first_name', 'Unknown')} {record['fields'].get('player_last_name', '')}"
            
            # Update the monthly status field
            update_data = {status_field: 'confirmed'}
            table.update(record_id, update_data)
            
            month_name = status_field.replace('_subscription_payment_status', '').title()
            print(f"✅ Updated {month_name} payment status to 'confirmed' for {player_name}")
            
        else:
            print(f"❌ No registration found for subscription ID: {subscription_id}")
        
    except Exception as e:
        print(f"Error handling subscription payment confirmed: {str(e)}")

async def handle_subscription_payment_failed(event: dict):
    """Handle failed subscription payment - update monthly status field"""
    
    subscription_id = event.get('links', {}).get('subscription')
    payment_id = event.get('links', {}).get('payment')
    payment_date = event.get('created_at')
    
    if not subscription_id:
        print("No subscription ID in payment failed event")
        return
        
    print(f"❌ Subscription payment failed: {payment_id} for subscription {subscription_id}")
    
    try:
        from pyairtable import Api
        from datetime import datetime
        import os
        
        # Parse payment date to get month/year
        payment_datetime = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
        payment_month = payment_datetime.month
        payment_year = payment_datetime.year
        
        # Map to status field name
        status_field = get_subscription_status_field_for_month(payment_month, payment_year)
        
        if not status_field:
            print(f"⚠️  Payment date {payment_date} doesn't map to a season month - ignoring")
            return
        
        # Find registration by subscription ID
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        records = table.all(formula=f"{{ongoing_subscription_id}} = '{subscription_id}'")
        
        if records:
            record = records[0]
            record_id = record['id']
            player_name = f"{record['fields'].get('player_first_name', 'Unknown')} {record['fields'].get('player_last_name', '')}"
            
            # Update the monthly status field
            update_data = {status_field: 'failed'}
            table.update(record_id, update_data)
            
            month_name = status_field.replace('_subscription_payment_status', '').title()
            print(f"🚨 Updated {month_name} payment status to 'failed' for {player_name}")
            
            # TODO: Trigger recovery payment process here
            print(f"🔄 TODO: Trigger recovery payment for {player_name} - {month_name}")
            
        else:
            print(f"❌ No registration found for subscription ID: {subscription_id}")
        
    except Exception as e:
        print(f"Error handling subscription payment failed: {str(e)}")

async def handle_subscription_payment_status_change(event: dict):
    """Handle other subscription payment status changes (cancelled, charged_back, submitted)"""
    
    subscription_id = event.get('links', {}).get('subscription')
    payment_id = event.get('links', {}).get('payment')
    payment_date = event.get('created_at')
    action = event.get('action')
    
    if not subscription_id:
        print(f"No subscription ID in payment {action} event")
        return
        
    print(f"📋 Subscription payment {action}: {payment_id} for subscription {subscription_id}")
    
    try:
        from pyairtable import Api
        from datetime import datetime
        import os
        
        # Parse payment date to get month/year
        payment_datetime = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
        payment_month = payment_datetime.month
        payment_year = payment_datetime.year
        
        # Map to status field name
        status_field = get_subscription_status_field_for_month(payment_month, payment_year)
        
        if not status_field:
            print(f"⚠️  Payment date {payment_date} doesn't map to a season month - ignoring")
            return
        
        # Find registration by subscription ID
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table('appBLxf3qmGIBc6ue', 'tbl1D7hdjVcyHbT8a')
        
        records = table.all(formula=f"{{ongoing_subscription_id}} = '{subscription_id}'")
        
        if records:
            record = records[0]
            record_id = record['id']
            player_name = f"{record['fields'].get('player_first_name', 'Unknown')} {record['fields'].get('player_last_name', '')}"
            
            # Update the monthly status field
            update_data = {status_field: action}
            table.update(record_id, update_data)
            
            month_name = status_field.replace('_subscription_payment_status', '').title()
            print(f"📝 Updated {month_name} payment status to '{action}' for {player_name}")
            
        else:
            print(f"❌ No registration found for subscription ID: {subscription_id}")
        
    except Exception as e:
        print(f"Error handling subscription payment status change: {str(e)}")

def get_subscription_status_field_for_month(month: int, year: int) -> str:
    """Map calendar month/year to subscription status field name"""
    
    # Season runs September 2025 - May 2026
    month_mapping = {
        (9, 2025): 'sep_subscription_payment_status',
        (10, 2025): 'oct_subscription_payment_status',
        (11, 2025): 'nov_subscription_payment_status',
        (12, 2025): 'dec_subscription_payment_status',
        (1, 2026): 'jan_subscription_payment_status',
        (2, 2026): 'feb_subscription_payment_status',
        (3, 2026): 'mar_subscription_payment_status',
        (4, 2026): 'apr_subscription_payment_status',
        (5, 2026): 'may_subscription_payment_status'
    }
    
    return month_mapping.get((month, year))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 