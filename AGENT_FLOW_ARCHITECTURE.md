# UTJFC Agent Orchestration Flow - Complete Analysis

## 🏗️ **Agent Architecture Overview**

The system implements a **two-tier agent architecture** with intelligent routing:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🎯 UTJFC Agent Flow System                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              📱 User Input
                                   ↓
                         ┌─────────────────────┐
                         │   🎯 ENTRY POINT    │
                         │   /chat endpoint    │
                         │   (server.py:1040)  │
                         └─────────────────────┘
                                   ↓
                    ┌─────────────────────────────────┐
                    │    🔍 REGISTRATION CODE         │
                    │    DETECTION & VALIDATION       │
                    │    (routing_validation.py)     │
                    └─────────────────────────────────┘
                                   ↓
                         ┌─────────────────────┐
                         │   📊 ROUTE DECISION │
                         └─────────────────────┘
                                   ↓
        ┌─────────────────────────────────────────────────────────────────────┐
        │                                                                     │
        ↓                             ↓                             ↓        │
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐ │
│   🔄 100-SERIES │      │   🆕 200-SERIES     │      │   🌍 NO VALID CODE  │ │
│   RE-REGISTRATION│      │   NEW REGISTRATION  │      │   UNIVERSAL AGENT   │ │
│   (line 1155)   │      │   (line 1200)      │      │   (line 1255)       │ │
└─────────────────┘      └─────────────────────┘      └─────────────────────┘ │
        ↓                             ↓                             ↓        │
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐ │
│  🎯 SPECIALIZED │      │  🎯 SPECIALIZED     │      │  🎯 ORCHESTRATOR    │ │
│  RE-REG AGENT   │      │  NEW-REG AGENT      │      │  AGENT              │ │
│  (registration_ │      │  (registration_     │      │  (urmston_town_     │ │
│  agent/)        │      │  agent/)            │      │  agent/)            │ │
└─────────────────┘      └─────────────────────┘      └─────────────────────┘ │
        ↓                             ↓                             ↓        │
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐ │
│   📝 35-STEP    │      │   📝 35-STEP        │      │   💬 GENERAL CHAT   │ │
│   WORKFLOW      │      │   WORKFLOW          │      │   & LOOKUPS         │ │
│   (routines)    │      │   (routines)        │      │   (Airtable tools)  │ │
└─────────────────┘      └─────────────────────┘      └─────────────────────┘ │
                                                                               │
└───────────────────────────────────────────────────────────────────────────┘
```

## 🔄 **Detailed Flow Analysis**

### **1. Entry Point - `/chat` endpoint** (`server.py:1040`)

**Input**: User message from frontend
**Processing**: 
- Session management
- Cheat code detection ("lah", "SDH")
- **Primary routing logic**

### **2. Registration Code Detection** (`server.py:1122`)

```python
validation_result = validate_and_route_registration(payload.user_message)
```

**Function**: `validate_and_route_registration()` in `routing_validation.py`
**Logic**:
- **Regex Pattern**: `^(100|200)-([A-Za-z0-9_]+)-([Uu]\d+)-(2526)(?:-([A-Za-z]+)-([A-Za-z]+))?$`
- **100-series**: `100-TEAM-AGE-2526-FIRSTNAME-LASTNAME` (re-registration)
- **200-series**: `200-TEAM-AGE-2526` (new registration)
- **Validation**: Team/age group checked against Airtable `team_info` table

### **3. Three-Way Routing Decision**

#### **Route A: 100-Series Re-Registration** (`server.py:1155`)
```python
if route_type == "re_registration":
    # Route to re-registration agent
    success, ai_full_response_object, assistant_content_to_send = retry_rereg_ai_call_with_parsing(
        chat_loop_renew_registration_1,  # From registration_agent
        re_registration_agent,           # Specialized agent
        session_history,
        max_retries=3,
        session_id=current_session_id
    )
```

#### **Route B: 200-Series New Registration** (`server.py:1200`)
```python
elif route_type == "new_registration":
    # Generate welcome message
    welcome_message = f"🎉 **Great news!** Your registration code is valid..."
    # Set routine_number = 1 to start 35-step workflow
    response_json = {
        "response": welcome_message,
        "last_agent": "new_registration",
        "routine_number": 1
    }
```

#### **Route C: Universal Agent (No Valid Code)** (`server.py:1255`)
```python
# Continue with universal bot (urmston_town_agent)
success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
    chat_loop_1,        # From urmston_town_agent
    default_agent,      # Orchestrator agent
    session_history,
    max_retries=3,
    session_id=current_session_id,
    call_type="Universal Agent"
)
```

## 🎯 **Agent Definitions**

### **Orchestrator Agent (urmston_town_agent)**
- **File**: `urmston_town_agent/agents.py`
- **Response Function**: `chat_loop_1` in `urmston_town_agent/responses.py`
- **Purpose**: 
  - General club inquiries
  - Player lookups
  - Team information
  - Database operations via Airtable tools
- **Tools**: `["airtable_database_operation"]`
- **Two Modes**:
  - **Local Mode**: Direct function calls
  - **MCP Mode**: Remote MCP server integration

### **Registration Agents (registration_agent)**
- **File**: `registration_agent/registration_agents.py`
- **Response Functions**: 
  - `chat_loop_renew_registration_1` (re-registration)
  - `chat_loop_new_registration_1` (new registration)
- **Purpose**: 35-step registration workflow
- **Tools**: 14+ specialized tools for validation, payments, etc.

## 🔧 **MCP Configuration**

The system supports **dual-mode operation**:

```python
# Two agent instances (server.py:380-438)
local_agent = Agent(
    name="UTJFC Registration Assistant (Local)",
    tools=["airtable_database_operation"],
    use_mcp=False  # Direct function calls
)

mcp_agent = Agent.create_mcp_agent(
    name="UTJFC Registration Assistant (MCP)",
    # Uses remote MCP server at https://utjfc-mcp-server.replit.app/mcp
)

# Selection based on environment
use_mcp_by_default = os.getenv("USE_MCP", "true").lower() == "true"
default_agent = mcp_agent if use_mcp_by_default else local_agent
```

## 🏃‍♂️ **Registration Code Examples**

### **Valid Codes**:
- `100-tigers-u13-2526-jack-grealish` → Re-registration flow
- `200-leopards-u9-2526` → New registration flow

### **Invalid Codes**:
- `200-tigers-u13-2525` → Wrong season
- `100-tigers-u13-2526` → Missing player name
- `200-tigers-u13-2526-extra-data` → Extra data for new registration

### **Non-Codes**:
- `"Hello"` → Universal agent
- `"Who plays for Tigers U13?"` → Universal agent

## 📊 **Session State Management**

The system maintains:
- **Session History**: All conversation turns stored
- **Session Context**: Registration codes, agent states
- **Agent Tracking**: `last_agent` field for frontend routing
- **Routine Tracking**: `routine_number` for 35-step workflow progress

## 🔍 **Code Reference Map**

### **Key Files and Functions**:

| Component | File | Key Functions | Purpose |
|-----------|------|---------------|---------|
| **Entry Point** | `server.py:1040` | `/chat` endpoint | Main routing logic |
| **Code Detection** | `routing_validation.py` | `validate_and_route_registration()` | Registration code parsing |
| **Orchestrator** | `urmston_town_agent/responses.py` | `chat_loop_1()` | General chat handling |
| **Registration** | `registration_agent/responses_reg.py` | `chat_loop_new_registration_1()` | 35-step workflow |
| **Agent Definitions** | `urmston_town_agent/agents.py` | `Agent` class | Agent configuration |
| **Session Management** | `urmston_town_agent/chat_history.py` | Session functions | History tracking |

### **Critical Code Locations**:

```python
# Main routing decision (server.py:1122)
validation_result = validate_and_route_registration(payload.user_message)

# Universal agent call (server.py:1258-1264)
success, ai_full_response_object, assistant_content_to_send, routine_number_from_agent = retry_ai_call_with_parsing(
    chat_loop_1,        # urmston_town_agent
    default_agent,      # Orchestrator
    session_history,
    max_retries=3,
    session_id=current_session_id,
    call_type="Universal Agent"
)

# Registration agent routing (server.py:1155 & 1200)
if route_type == "re_registration":
    # Route to re-registration agent
elif route_type == "new_registration":
    # Route to new registration agent
```

## 🎯 **Key Insights**

1. **Your architectural understanding is 100% correct** - the code implements exactly what you described
2. **urmston_town_agent is the orchestrator** - it handles all non-registration interactions
3. **registration_agent handles specialized workflows** - triggered only by valid codes
4. **The routing is intelligent** - validates codes against database before routing
5. **MCP integration is seamless** - allows local/remote tool execution modes

## 🏗️ **Development Implications**

### **For Building Out the Orchestrator Agent**:

1. **Tool Expansion**: Add more tools to `urmston_town_agent/agents.py`
2. **Instruction Enhancement**: Improve agent instructions in `server.py:380-433`
3. **Response Handling**: Modify `chat_loop_1()` for new capabilities
4. **Database Integration**: Extend Airtable tools for additional operations

### **Session Handoff Points**:

- **Universal → Registration**: When valid code detected
- **Registration → Universal**: Currently not implemented (registration is one-way)
- **State Preservation**: Session history maintained across agent switches

### **Testing Strategy**:

- **Universal Agent**: Test general inquiries, player lookups
- **Code Detection**: Test all code formats (valid/invalid)
- **Registration Flow**: Test 35-step workflows
- **MCP Integration**: Test local vs remote tool execution

## 🚀 **Architecture Summary**

The system is well-architected with:
- **Clear separation of concerns** between orchestrator and specialized agents
- **Robust validation** before routing to expensive registration workflows
- **Flexible tool integration** supporting both local and remote execution
- **Comprehensive session management** for context preservation
- **Intelligent routing** based on regex pattern matching and database validation

This architecture provides a solid foundation for expanding the orchestrator agent's capabilities while maintaining the specialized registration workflows.