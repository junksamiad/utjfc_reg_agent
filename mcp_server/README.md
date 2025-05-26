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
cp env.example .env

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

## 🚀 Deployment on Replit

### Step 1: Fork/Import to Replit

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Import from GitHub or upload the `mcp_server` folder
4. Select "Python" as the template

### Step 2: Set Environment Variables

In Replit, go to "Secrets" (🔐 icon) and add:

```
OPENAI_API_KEY=your_openai_api_key_here
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=appBLxf3qmGIBc6ue
MCP_AUTH_TOKEN=your_secure_random_token_here
```

**Important**: Generate a secure `MCP_AUTH_TOKEN` using:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Step 3: Deploy

1. Click "Run" to test locally
2. Click "Deploy" to get a production URL
3. Your MCP server will be available at: `https://your-repl-name.repl.co`

## 🔧 Configuration for OpenAI

Once deployed, use your MCP server with OpenAI like this:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1",
    tools=[{
        "type": "mcp",
        "server_label": "utjfc_registration",
        "server_url": "https://your-repl-name.repl.co/mcp",
        "require_approval": "never",
        "headers": {
            "X-MCP-Auth-Token": "your_mcp_auth_token_here"
        }
    }],
    input="How many players are registered for season 2526?"
)
```

## 📋 Available Tools

### airtable_database_operation

Execute CRUD operations on UTJFC registration database.

**Parameters:**
- `season` (required): "2526" or "2425"
- `query` (required): Natural language description of the operation

**Examples:**
- "Count all registrations"
- "Find all players in team Tigers"
- "Create registration for John Smith, age u10, team Eagles"
- "Update player ID rec123 to team Dragons"

## 🔐 Security

1. **Always use HTTPS** - Replit provides this automatically
2. **Set MCP_AUTH_TOKEN** - This prevents unauthorized access
3. **Keep your tokens secret** - Never commit them to Git
4. **Monitor usage** - Check Replit logs for suspicious activity

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-repl-name.repl.co/health
```

### Direct JSON-RPC Test
```bash
curl -X POST https://your-repl-name.repl.co/mcp \
  -H "Content-Type: application/json" \
  -H "X-MCP-Auth-Token: your_token_here" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

## 📊 Monitoring

- Check Replit logs for request/response details
- Monitor the "Observability" tab in Replit for performance
- Set up alerts for errors or high usage

## 🆘 Troubleshooting

### Common Issues

1. **424 Error from OpenAI**
   - Ensure your server is publicly accessible
   - Check that HTTPS is working
   - Verify authentication token is correct

2. **Authentication Errors**
   - Double-check MCP_AUTH_TOKEN in both Replit and your client
   - Ensure you're using the correct header name

3. **Tool Execution Errors**
   - Verify AIRTABLE_API_KEY is set correctly
   - Check Airtable base permissions
   - Look at Replit logs for detailed error messages

## 📚 Resources

- [Model Context Protocol Docs](https://modelcontextprotocol.io)
- [OpenAI MCP Guide](https://platform.openai.com/docs/guides/tools-remote-mcp)
- [Replit Deployment Guide](https://docs.replit.com/hosting/deployments)

## 🤝 Support

For issues specific to:
- **MCP Protocol**: Check the MCP documentation
- **Replit Deployment**: Use Replit's support channels
- **UTJFC Registration**: Contact your system administrator 