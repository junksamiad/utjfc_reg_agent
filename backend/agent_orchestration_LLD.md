# Agent Orchestration Low-Level Design (LLD)

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Base Agent Class Implementation](#base-agent-class-implementation)
3. [Registration Agent Definition](#registration-agent-definition)
4. [Agent Switching Logic](#agent-switching-logic)
5. [Context Management](#context-management)
6. [Dynamic Agent Creation](#dynamic-agent-creation)
7. [MCP vs Local Agent Modes](#mcp-vs-local-agent-modes)
8. [Agent Selection Logic](#agent-selection-logic)
9. [Code Analysis](#code-analysis)

## Architecture Overview

The UTJFC Registration Agent system implements a sophisticated agent orchestration architecture that supports multiple AI agents with different capabilities, context management, and dynamic routing based on registration codes and conversation state.

### Key Components:
- **Base Agent Class**: Unified interface for all agents with MCP/local function calling support
- **Registration Agents**: Specialized agents for different registration flows (new/re-registration)
- **Dynamic Agent Creation**: Runtime agent generation with routine-specific instructions
- **Context Management**: Session-based conversation history and state preservation
- **Agent Switching**: Intelligent routing between agents based on registration codes

## Base Agent Class Implementation

### Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/urmston_town_agent/agents.py`

The base `Agent` class provides the foundation for all agents in the system:

```python
class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: list = []  # Function definitions
    use_mcp: bool = False  # MCP mode flag
    mcp_server_url: str = ""  # MCP server URL
```

### Key Methods:

#### 1. `get_tools_for_openai()` (Lines 16-42)
Handles dual-mode tool configuration:
- **MCP Mode**: Returns MCP server configuration for external tool execution
- **Local Mode**: Returns local function definitions for backend tool execution

```python
def get_tools_for_openai(self):
    if self.use_mcp and self.mcp_server_url:
        return [{
            "type": "mcp",
            "server_label": "utjfc_registration", 
            "server_url": self.mcp_server_url,
            "require_approval": "never",
            "allowed_tools": self.tools if self.tools else None
        }]
    else:
        # Return local function definitions
        available_tools = {
            "airtable_database_operation": AIRTABLE_DATABASE_OPERATION_TOOL
        }
        return [available_tools[tool_name] for tool_name in self.tools if tool_name in available_tools]
```

#### 2. `get_tool_functions()` (Lines 44-58)
Returns actual Python function handlers for local mode:
```python
def get_tool_functions(self):
    if self.use_mcp:
        return {}  # MCP mode doesn't use local functions
    
    from .tools.airtable.airtable_tool_definition import handle_airtable_tool_call
    return {
        "airtable_database_operation": handle_airtable_tool_call
    }
```

#### 3. `create_mcp_agent()` (Lines 60-76)
Factory method for MCP agent creation:
```python
@classmethod
def create_mcp_agent(cls, name: str = "MCP Agent", instructions: str = "...", mcp_server_url: str = None):
    if not mcp_server_url:
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8002/sse")
    
    return cls(
        name=name,
        model="gpt-4.1",  # MCP requires gpt-4.1
        instructions=instructions,
        tools=["airtable_database_operation"],
        use_mcp=True,
        mcp_server_url=mcp_server_url
    )
```

## Registration Agent Definition

### Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/registration_agents.py`

Two specialized agents handle different registration flows:

### 1. Re-registration Agent (100 codes)
```python
re_registration_agent = Agent(
    name="UTJFC Re-registration Assistant",
    model="gpt-4.1",
    instructions="You have been passed some information about a grassroots football club player. Please spell the player's name backwards and tell the user you are the RE-REGISTRATION AGENT handling their request.",
    tools=["address_validation", "address_lookup"],
    use_mcp=False
)
```

### 2. New Registration Agent (200 codes)
```python
new_registration_agent = Agent(
    name="UTJFC New Player Registration Assistant", 
    model="gpt-4.1",
    instructions="""Context: You are a volunteer at Urmston Town Juniors Football Club...
    
    **Use markdown formatting in all responses to improve the user experience**
    
    CURRENT STEP INSTRUCTIONS:
    {routine_instructions}""",
    tools=["address_validation", "address_lookup", "create_signup_payment_link", 
           "create_payment_token", "update_reg_details_to_db", "check_shirt_number_availability", 
           "update_kit_details_to_db", "upload_photo_to_s3", "update_photo_link_to_db", 
           "check_if_kit_needed"],
    use_mcp=False
)
```

### Enhanced Agent Class: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/agents_reg.py`

The registration-specific Agent class extends the base class with additional tools and capabilities:

#### Tool Integration (Lines 46-62)
```python
available_tools = {
    "airtable_database_operation": AIRTABLE_DATABASE_OPERATION_TOOL,
    "person_name_validation": PERSON_NAME_VALIDATION_TOOL,
    "child_dob_validation": CHILD_DOB_VALIDATION_TOOL,
    "medical_issues_validation": MEDICAL_ISSUES_VALIDATION_TOOL,
    "address_validation": ADDRESS_VALIDATION_TOOL,
    "address_lookup": ADDRESS_LOOKUP_TOOL,
    "create_signup_payment_link": CREATE_SIGNUP_PAYMENT_LINK_TOOL,
    "create_payment_token": CREATE_PAYMENT_TOKEN_TOOL,
    "update_reg_details_to_db": UPDATE_REG_DETAILS_TO_DB_AI_FRIENDLY_TOOL,
    "check_shirt_number_availability": CHECK_SHIRT_NUMBER_AVAILABILITY_TOOL,
    "update_kit_details_to_db": UPDATE_KIT_DETAILS_TO_DB_TOOL,
    "upload_photo_to_s3": UPLOAD_PHOTO_TO_S3_TOOL,
    "update_photo_link_to_db": UPDATE_PHOTO_LINK_SCHEMA,
    "send_sms_payment_link": SEND_SMS_PAYMENT_LINK_TOOL,
    "check_if_kit_needed": CHECK_IF_KIT_NEEDED_TOOL
}
```

#### Dynamic Instructions (Lines 116-121)
```python
def get_instructions_with_routine(self, routine_message: str = ""):
    """
    Get instructions with a routine message injected into the {routine_instructions} placeholder.
    Used for dynamic instruction injection in registration flows.
    """
    return self.instructions.format(routine_instructions=routine_message)
```

## Agent Switching Logic

### Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/server.py`

The agent switching logic operates at multiple levels:

### 1. Global Agent Configuration (Lines 381-447)
```python
# Create default agent instances
local_agent = Agent(
    name="UTJFC Registration Assistant (Local)",
    model="gpt-4.1",
    instructions="""You are a helpful assistant for Urmston Town Juniors Football Club (UTJFC)...""",
    tools=["airtable_database_operation"],
    use_mcp=False
)

mcp_agent = Agent.create_mcp_agent(
    name="UTJFC Registration Assistant (MCP)",
    instructions="""You are a helpful assistant for Urmston Town Juniors Football Club (UTJFC)...""",
    mcp_server_url=os.getenv("MCP_SERVER_URL", "https://utjfc-mcp-server.replit.app/sse")
)

# Default agent selection
use_mcp_by_default = os.getenv("USE_MCP", "true").lower() == "true"
default_agent = mcp_agent if use_mcp_by_default else local_agent
```

### 2. Registration Code Parsing (Lines 25-27)
```python
from registration_agent.routing_validation import validate_and_route_registration
from registration_agent.registration_agents import re_registration_agent, new_registration_agent
from registration_agent.registration_routines import RegistrationRoutines
```

### 3. Agent Selection Logic in Chat Endpoint
The main `/chat` endpoint implements sophisticated agent selection:

#### Step 1: Registration Code Detection
```python
# Check if user message contains a registration code
validation_result = validate_and_route_registration(payload.user_message)

if validation_result["valid"]:
    # Route to appropriate registration agent
    if validation_result["route"] == "new_registration":
        # Use new registration agent
    elif validation_result["route"] == "re_registration":
        # Use re-registration agent
else:
    # Use universal agent
```

#### Step 2: Re-registration Flow (Lines 775-776)
```python
success, ai_full_response_object, assistant_content_to_send = retry_rereg_ai_call_with_parsing(
    chat_loop_renew_registration_1, 
    re_registration_agent,  # Direct agent usage
    session_history,
    max_retries=3,
    session_id=current_session_id
)
```

#### Step 3: New Registration Flow with Dynamic Agent Creation
```python
# Get routine message for current step
routine_message = RegistrationRoutines.get_routine_message(routine_number)

# Create dynamic agent with routine-specific instructions
dynamic_instructions = new_registration_agent.get_instructions_with_routine(routine_message)

from registration_agent.agents_reg import Agent
dynamic_agent = Agent(
    name=new_registration_agent.name,
    model=new_registration_agent.model,
    instructions=dynamic_instructions,
    tools=new_registration_agent.tools,
    use_mcp=new_registration_agent.use_mcp
)
```

## Context Management

### Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/urmston_town_agent/chat_history.py`

The system maintains context through session-based conversation history:

### 1. Session History Storage (Lines 3-4)
```python
_global_chat_histories = {}  # Session ID -> message history
_session_context = {}  # Session ID -> additional context data
```

### 2. History Management Functions
```python
def get_session_history(session_id: str = None) -> list:
    """Retrieves chat history for a given session_id"""
    if session_id is None:
        session_id = DEFAULT_SESSION_ID
    return _global_chat_histories.setdefault(session_id, [])

def add_message_to_session_history(session_id: str = None, role: str = None, content: str = None):
    """Adds a message to the chat history for a given session_id"""
    if session_id is None:
        session_id = DEFAULT_SESSION_ID
    
    if role and content:
        history = get_session_history(session_id)
        history.append({"role": role, "content": content})
        
        # Trim history to prevent infinite growth
        if len(history) > MAX_HISTORY_LENGTH * 2:
            history[:] = history[-MAX_HISTORY_LENGTH * 2:]
```

### 3. Context Injection
Registration data is injected into session context:
```python
def inject_structured_registration_data(session_id: str, registration_code: str) -> None:
    """Parse registration code and inject structured data into conversation history"""
    structured_message = f"""[SYSTEM INJECTION - Registration Code Analysis]
    Registration type: {reg_type} ({parsed["prefix"]})
    Team: {team_name}
    Age group: {age_group}
    Season: {season}
    Original code: {registration_code}"""
    
    add_message_to_session_history(session_id, "system", structured_message)
```

## Dynamic Agent Creation

### Registration Routine System
Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/registration_routines.py`

The system implements a 35-step registration workflow with dynamic agent creation:

### 1. Routine Definition (Lines 7-81)
```python
ROUTINES = {
    1: """Task: Your current task is to: 1) take the parent's first and last name...""",
    2: """Task: Your current task is to: 1) take the child's first and last name...""",
    # ... 35 total routines
    35: """Task: Your current task is to respond to any query helpfully as the registration has now completed."""
}
```

### 2. Dynamic Agent Creation in Server
Multiple locations in `server.py` show dynamic agent creation:

#### Photo Upload Processing (Lines 273-282)
```python
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
```

#### Age-Based Routing (Lines 630-636)
```python
# Create temporary agent for routine 22
from registration_agent.agents_reg import Agent
routine_22_agent = Agent(
    name=new_registration_agent.name,
    model=new_registration_agent.model,
    instructions=dynamic_instructions,
    tools=new_registration_agent.tools,
    use_mcp=new_registration_agent.use_mcp
)
```

## MCP vs Local Agent Modes

### Mode Selection
The system supports two operational modes:

#### 1. Local Function Calling Mode
- **Tools**: Executed directly in backend
- **Model**: Any OpenAI model
- **Configuration**: `use_mcp=False`
- **Tool Execution**: Direct Python function calls

#### 2. MCP (Model Context Protocol) Mode
- **Tools**: Executed via external MCP server
- **Model**: Requires `gpt-4.1` for MCP support
- **Configuration**: `use_mcp=True`
- **Tool Execution**: HTTP requests to MCP server

### Runtime Mode Switching (Lines 1429-1453)
```python
@app.post("/agent/mode")
async def switch_agent_mode(request: AgentModeRequest):
    """Switch between local function calling and MCP mode"""
    global default_agent
    
    if request.mode == "local":
        default_agent = local_agent
        return {
            "message": "Switched to local function calling mode",
            "agent": {"name": default_agent.name, "use_mcp": default_agent.use_mcp}
        }
    elif request.mode == "mcp":
        default_agent = mcp_agent
        return {
            "message": "Switched to MCP server mode", 
            "agent": {"name": default_agent.name, "use_mcp": default_agent.use_mcp}
        }
```

## Agent Selection Logic

### Registration Code-Based Routing
Location: `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/routing_validation.py`

### 1. Code Pattern Recognition (Lines 26-57)
```python
def parse_registration_code(message: str):
    """Parse and validate registration code format"""
    # Regex pattern for registration codes (case-insensitive)
    pattern = r'^(100|200)-([A-Za-z0-9_]+)-([Uu]\d+)-(2526)(?:-([A-Za-z]+)-([A-Za-z]+))?$'
    
    match = re.match(pattern, message.strip(), re.IGNORECASE)
    if not match:
        return None  # Not a registration code
    
    prefix = match.group(1)  # 100 or 200
    team = match.group(2).lower()
    age_group = match.group(3).lower()
    season = match.group(4)  # Must be 2526
    first_name = match.group(5).lower() if match.group(5) else None
    surname = match.group(6).lower() if match.group(6) else None
    
    # Validation logic
    if prefix == "100" and (not first_name or not surname):
        return "INVALID_CODE_ATTEMPT"
    if prefix == "200" and (first_name or surname):
        return "INVALID_CODE_ATTEMPT"
    
    return {
        "prefix": prefix,
        "team": team,
        "age_group": age_group, 
        "season": season,
        "player_name": f"{first_name} {surname}" if first_name and surname else None,
        "raw_code": message.strip()
    }
```

### 2. Agent Routing Logic (Lines 207-222)
```python
def route_registration_request(registration_code: dict) -> str:
    """Determine which registration flow to use based on code prefix"""
    if registration_code["prefix"] == "100":
        return "re_registration"  # Use re_registration_agent
    elif registration_code["prefix"] == "200":
        return "new_registration"  # Use new_registration_agent
    else:
        raise ValueError(f"Invalid registration prefix: {registration_code['prefix']}")
```

### 3. Complete Validation Flow (Lines 136-205)
```python
def validate_and_route_registration(message: str) -> dict:
    """Complete validation and routing flow for registration codes"""
    
    # Step 1: Parse registration code
    registration_code = parse_registration_code(message)
    if registration_code is None:
        return {"valid": False, "error": None, "route": None}  # Universal bot
    
    # Step 2: Validate team and age group against Airtable
    is_valid_team = validate_team_and_age_group(
        registration_code["team"], 
        registration_code["age_group"]
    )
    
    if not is_valid_team:
        return {"valid": False, "error": "Invalid registration code", "route": None}
    
    # Step 3: For re-registration, lookup player details
    if registration_code["prefix"] == "100":
        player_details = lookup_player_details(...)
    
    # Step 4: Determine routing
    route = route_registration_request(registration_code)
    
    return {
        "valid": True,
        "route": route,
        "registration_code": registration_code,
        "player_details": player_details,
        "error": None
    }
```

## Code Analysis

### Key File Locations and Responsibilities

1. **Base Agent Framework**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/urmston_town_agent/agents.py`: Base Agent class
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/agents_reg.py`: Registration-specific Agent class

2. **Agent Definitions**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/registration_agents.py`: Pre-configured agents

3. **Orchestration Logic**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/server.py`: Main routing and agent switching logic

4. **Context Management**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/urmston_town_agent/chat_history.py`: Session history management

5. **Dynamic Workflow**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/registration_routines.py`: 35-step workflow definitions

6. **Validation & Routing**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/routing_validation.py`: Registration code parsing and validation

7. **AI Response Processing**
   - `/Users/leehayton/Cursor Projects/utjfc_reg_agent/backend/registration_agent/responses_reg.py`: OpenAI Responses API integration

### System Flow Summary

1. **User Input Processing**: Messages are analyzed for registration codes
2. **Agent Selection**: Based on code prefix (100/200) or fallback to universal agent
3. **Dynamic Agent Creation**: Agents are created with routine-specific instructions
4. **Context Preservation**: Session history maintains conversation state across agent switches
5. **Tool Execution**: Either local function calls or MCP server requests
6. **Response Generation**: AI responses are processed and returned to frontend

The system demonstrates sophisticated agent orchestration with support for multiple operational modes, dynamic agent creation, and context-aware routing based on business logic.