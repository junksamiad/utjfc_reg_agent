# UTJFC Registration MCP Server

A Model Context Protocol (MCP) server that provides tools for managing UTJFC player registrations through Airtable integration.

## 🏗️ Architecture

This MCP server exposes the UTJFC registration database tools via the standardized MCP protocol, allowing any MCP-compatible client (like OpenAI's Responses API) to interact with the registration system.

```
OpenAI Responses API ──► MCP Server ──► Airtable Database
                         (Port 8002)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd mcp_server
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the template and fill in your values
cp env_template.txt .env

# Edit .env with your actual API keys
OPENAI_API_KEY=your_openai_api_key
AIRTABLE_API_KEY=your_airtable_api_key
```

### 3. Run the Server

```bash
python server.py
```

The server will start on `http://localhost:8002/mcp`

## 🛠️ Available Tools

### `airtable_database_operation`

Execute CRUD operations on the UTJFC registration database with automatic data validation and normalization.

**Parameters:**
- `season` (string): Season identifier ("2526" for 2025-26, "2425" for 2024-25)
- `query` (string): Natural language description of the database operation

**Examples:**
```
"Find Stefan Hayton"
"Create registration for Seb Charlton, age u10s, tigers team"
"Show all players with medical issues"
"Update Stefan's team to Eagles"
"How many players are registered this season?"
```

## 🔌 Integration with OpenAI

Use this MCP server with OpenAI's Responses API:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    tools=[{
        "type": "mcp",
        "server_label": "utjfc_registration",
        "server_url": "http://localhost:8002/mcp",
        "require_approval": "never",
        "allowed_tools": ["airtable_database_operation"]
    }],
    input="Find all U10 players on the Tigers team"
)

print(response.output_text)
```

## 🏃‍♂️ Development

### Testing with MCP Inspector

```bash
# Install MCP CLI tools
pip install mcp[cli]

# Test the server
mcp dev server.py
```

### Project Structure

```
mcp_server/
├── server.py              # Main MCP server
├── requirements.txt       # Dependencies
├── env_template.txt       # Environment template
├── tools/                 # Tool implementations
│   └── airtable/         # Airtable integration
└── README.md             # This file
```

## 🚀 Deployment

### Local Development
- Runs on `http://localhost:8002/mcp`
- Uses Streamable HTTP transport (stateless)

### Production Options
1. **Replit**: Deploy directly with automatic HTTPS
2. **AWS App Runner**: Container-based deployment
3. **AWS ECS Fargate**: More control over infrastructure

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for the helper agent | Yes |
| `AIRTABLE_API_KEY` | Airtable API key | Yes |
| `AIRTABLE_BASE_ID` | Airtable base ID (default: appBLxf3qmGIBc6ue) | No |
| `PORT` | Server port (default: 8002) | No |
| `HOST` | Server host (default: 0.0.0.0) | No |

### Transport Protocol

This server uses **Streamable HTTP** transport for:
- Better scalability and stateless operation
- Production-ready deployment
- Compatibility with cloud platforms
- Standard HTTP semantics

## 🔍 Monitoring

The server provides basic logging and health information:
- Startup configuration details
- Environment variable validation
- Tool execution status
- Error handling and reporting

## 🛡️ Security

- No authentication required (internal use)
- Environment variables for sensitive data
- Input validation on all tool parameters
- Error handling prevents data exposure

## 📚 Related Documentation

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OpenAI MCP Integration](https://platform.openai.com/docs/guides/tools-remote-mcp)
- [Airtable Tool Documentation](./tools/airtable/README.md) 