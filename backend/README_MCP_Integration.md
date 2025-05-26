# UTJFC Backend - MCP Integration

This document explains how the UTJFC Registration backend integrates with the Model Context Protocol (MCP) server.

## 🏗️ Architecture Overview

The backend now supports two modes of operation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Next.js)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP API calls
┌─────────────────────▼───────────────────────────────────────┐
│                Backend (FastAPI)                           │
│  ┌─────────────────┬─────────────────────────────────────┐  │
│  │  Local Mode     │         MCP Mode                    │  │
│  │                 │                                     │  │
│  │  Agent ──────►  │  Agent ──────► MCP Server ──────►   │  │
│  │  │              │  │              (Port 8002)        │  │
│  │  ▼              │  ▼                     │            │  │
│  │  Local Tools    │  OpenAI handles        ▼            │  │
│  │  (Direct)       │  tool calls      Airtable DB       │  │
│  └─────────────────┴─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Two Operating Modes

### 1. **Local Function Calling Mode** (`use_mcp=False`)
- **How it works**: Backend executes tools directly using local Python functions
- **Pros**: Lower latency, no external dependencies
- **Cons**: Tools are tightly coupled to backend, harder to scale
- **Use case**: Development, testing, simple deployments

### 2. **MCP Server Mode** (`use_mcp=True`)
- **How it works**: Backend connects to remote MCP server via OpenAI's Responses API
- **Pros**: Scalable, tools can be deployed independently, follows MCP standard
- **Cons**: Requires MCP server to be running, slightly higher latency
- **Use case**: Production, microservices architecture, when tools need to be shared

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your values
OPENAI_API_KEY=your_openai_api_key
AIRTABLE_API_KEY=your_airtable_api_key
MCP_SERVER_URL=http://localhost:8002/mcp
USE_MCP=true
```

### 2. Start MCP Server (if using MCP mode)

```bash
# In another terminal
cd ../mcp_server
source .venv/bin/activate
python server.py
```

### 3. Start Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

## 🧪 Testing the Integration

### Test Script

```bash
# Run comprehensive test
python test_mcp_integration.py
```

This will test both local and MCP modes with the same query.

### Manual Testing via API

```bash
# Check current agent status
curl http://localhost:8000/agent/status

# Switch to local mode
curl -X POST http://localhost:8000/agent/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "local"}'

# Switch to MCP mode  
curl -X POST http://localhost:8000/agent/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "mcp"}'

# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "How many players are registered for season 2526?"}'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `AIRTABLE_API_KEY` | Airtable API key (local mode) | - | Yes* |
| `AIRTABLE_BASE_ID` | Airtable base ID | `appBLxf3qmGIBc6ue` | No |
| `MCP_SERVER_URL` | MCP server endpoint | `http://localhost:8002/mcp` | Yes** |
| `USE_MCP` | Default mode on startup | `true` | No |

*Required for local mode  
**Required for MCP mode

### Agent Configuration

The backend creates two agent instances:

```python
# Local agent
local_agent = Agent(
    name="UTJFC Registration Assistant (Local)",
    model="gpt-4.1",
    use_mcp=False,
    tools=["airtable_database_operation"]
)

# MCP agent  
mcp_agent = Agent.create_mcp_agent(
    name="UTJFC Registration Assistant (MCP)",
    mcp_server_url="http://localhost:8002/mcp"
)
```

## 🔀 Switching Between Modes

### Via Environment Variable
Set `USE_MCP=true` or `USE_MCP=false` in `.env` file.

### Via API (Runtime)
```bash
# Switch to MCP mode
POST /agent/mode {"mode": "mcp"}

# Switch to local mode  
POST /agent/mode {"mode": "local"}

# Check current mode
GET /agent/status
```

### Via Code
```python
from agents import Agent

# Create local agent
local_agent = Agent(use_mcp=False, tools=["airtable_database_operation"])

# Create MCP agent
mcp_agent = Agent.create_mcp_agent()
```

## 🛠️ API Endpoints

### Chat Endpoints
- `POST /chat` - Send message to current agent
- `POST /clear` - Clear chat history

### Agent Management
- `GET /agent/status` - Get current agent configuration
- `POST /agent/mode` - Switch between local/MCP modes

### Response Format
```json
{
  "current_agent": {
    "name": "UTJFC Registration Assistant (MCP)",
    "model": "gpt-4.1", 
    "use_mcp": true,
    "mcp_server_url": "http://localhost:8002/mcp",
    "tools": ["airtable_database_operation"]
  },
  "available_modes": {
    "local": {
      "name": "UTJFC Registration Assistant (Local)",
      "description": "Uses local function calling (backend tools directly)"
    },
    "mcp": {
      "name": "UTJFC Registration Assistant (MCP)", 
      "description": "Uses remote MCP server for tool execution",
      "server_url": "http://localhost:8002/mcp"
    }
  }
}
```

## 🔍 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **MCP Server Not Running**
   ```
   Error: Connection refused to http://localhost:8002/mcp
   ```
   **Solution**: Start the MCP server first

2. **Missing Environment Variables**
   ```
   Error: Missing required environment variables: ['OPENAI_API_KEY']
   ```
   **Solution**: Create `.env` file with required variables

3. **Tool Call Failures**
   - Check MCP server logs
   - Verify Airtable API key and permissions
   - Test with local mode first

## 🚀 Deployment Considerations

### Local Mode
- Simpler deployment (single service)
- All dependencies in one place
- Good for small-scale deployments

### MCP Mode  
- Requires MCP server deployment
- Better for microservices architecture
- Easier to scale tools independently
- Follows industry standards (MCP protocol)

### Production Recommendations
1. Use MCP mode for production
2. Deploy MCP server on separate infrastructure
3. Use environment-specific MCP server URLs
4. Implement proper error handling and retries
5. Monitor both backend and MCP server health

## 📚 Related Documentation

- [MCP Server README](../mcp_server/README.md)
- [OpenAI MCP Integration](../docs/openai_built_in_mcp.md)
- [Agent Configuration](./agents.py)
- [Response Handling](./responses.py) 