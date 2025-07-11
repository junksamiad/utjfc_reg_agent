# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **UTJFC Registration Agent** - an AI-powered football club registration system for Urmston Town Juniors FC. It consists of a Python FastAPI backend with sophisticated AI agents, a Next.js frontend, and an MCP (Model Context Protocol) server for external integrations.

## Development Commands

### Backend Development
```bash
# Start backend server
cd backend
source .venv/bin/activate
uvicorn server:app --reload --port 8000

# With environment variables
cd backend
source .venv/bin/activate
OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2) uvicorn server:app --reload --port 8000

# Install dependencies
pip install -r requirements.txt
```

### Frontend Development
```bash
# Start frontend (Next.js)
cd frontend/web
pnpm dev

# Alternative commands
npm run dev
# or
yarn dev
# or
bun dev

# Build for production
npm run build
pnpm build

# Lint
npm run lint
```

### MCP Server
```bash
# Start MCP server (deployed on Replit)
cd mcp_server
source .venv/bin/activate
python server.py

# Available at: https://utjfc-mcp-server.replit.app/mcp
```

### Docker Development
```bash
# Start all services
docker compose up

# Rebuild after changes
docker compose up --build

# Stop services
docker compose down
```

### Testing
```bash
# Photo upload comprehensive test
cd test_scripts/integration
python test_photo_upload.py

# Backend MCP flow test
cd test_scripts/integration
python test_backend_mcp_flow.py

# S3 photo cleanup
cd test_scripts/utilities
python cleanup_test_photos.py
```

## Architecture Overview

### Core Components

1. **Backend (`backend/`)**
   - **Main Server**: `server.py` - FastAPI application with retry logic for AI calls
   - **Registration Agent System**: Sophisticated AI workflow with 35-step registration process
   - **Tool Ecosystem**: 14+ specialized tools for data validation, payment processing, and external integrations

2. **Frontend (`frontend/web/`)**
   - **Next.js Application**: React-based chat interface with real-time communication
   - **Environment Configuration**: Uses `NEXT_PUBLIC_API_URL` for backend connectivity
   - **Responsive Design**: Mobile-optimized registration flow

3. **MCP Server (`mcp_server/`)**
   - **Model Context Protocol**: External integrations server for OpenAI Responses API
   - **Airtable Integration**: Database operations through MCP protocol
   - **FastAPI-based**: RESTful API with streaming support

### Agent Architecture

The system implements a **two-tier agent architecture**:

1. **Orchestrator Agent (`urmston_town_agent/`)**
   - **Entry Point**: All chat requests initially handled here
   - **General Inquiries**: Club information, player lookups, team details
   - **Database Operations**: Direct Airtable access for queries
   - **Routing Decision**: Detects registration codes and routes to specialized agents

2. **Specialized Registration Agents (`registration_agent/`)**
   - **Triggered By**: Valid registration codes only
   - **100-Series**: Re-registration flow for existing players
   - **200-Series**: New registration flow with 35-step process
   - **No Return Path**: Once routed to registration, stays there for session
   - **Business Logic**: Age-based routing, sibling discounts, kit requirements, payment processing

### Key File Locations

- **Orchestrator Agent**: `backend/urmston_town_agent/`
  - `agents.py` - Base agent class with MCP/local modes
  - `responses.py` - AI integration with chat_loop_1
  - `chat_history.py` - Centralized session management
- **Registration Agents**: `backend/registration_agent/`
  - `registration_agents.py` - Specialized agent instances
  - `registration_routines.py` - 35-step workflow definitions
  - `routing_validation.py` - Code detection and validation
  - `responses_reg.py` - AI response processing
- **Main Router**: `backend/server.py` - Entry point and routing logic
- **Tool Ecosystem**: `backend/registration_agent/tools/`
- **Database Operations**: `backend/registration_agent/tools/airtable/`
- **Chat Interface**: `frontend/web/src/app/chat/`

## External Services Integration

- **OpenAI GPT-4.1**: AI model for all agents (required for MCP compatibility)
- **Airtable**: Primary database for registration data
- **GoCardless**: Direct debit payment processing
- **Twilio**: SMS notifications and payment links
- **AWS S3**: Photo upload and storage with HEIC conversion
- **Address Validation**: UK postcode and address verification

## Environment Configuration

### Backend Environment Variables
Create `backend/.env` with:
```
OPENAI_API_KEY=your_key_here
AIRTABLE_API_KEY=your_pat_token_here  # Personal Access Token starting with 'pat'
GOCARDLESS_API_KEY=your_key_here
GOCARDLESS_WEBHOOK_SECRET=your_secret_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=your_phone_here
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
GOOGLE_MAPS_API_KEY=your_key_here
USE_MCP=true
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
```

### Frontend Environment Variables
Create `frontend/web/.env.local` with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## AI Agent Workflow

The system implements a two-tier agent architecture with intelligent routing:

1. **Entry Point**: All requests go through orchestrator agent first
2. **Code Detection**: `validate_and_route_registration()` checks for registration codes
3. **Three-Way Routing**:
   - **No Code**: Continue with orchestrator agent (general chat)
   - **100-Series Code**: Route to re-registration agent
   - **200-Series Code**: Route to new registration agent (35-step workflow)
4. **Session Continuity**: History maintained across agent switches
5. **Tool Integration**: Each agent has specific tools for its purpose
6. **Error Handling**: Retry mechanisms with exponential backoff

## Key Features

- **Intelligent Validation**: 14 specialized validation tools
- **Payment Processing**: Complete GoCardless integration with SMS links
- **Photo Upload**: Async processing with S3 storage and HEIC conversion
- **Mobile Optimization**: Responsive design with timer-based UI feedback
- **Comprehensive Testing**: Automated test suites for all major workflows
- **Production Deployment**: AWS deployment with CloudFront distribution

## Current Branch Context

**Feature Branch**: `feature/agent-flow-integration`
- Working on OpenAI Responses API migration
- MCP server integration for external services
- Enhanced agent orchestration capabilities

## Development Notes

- The system uses FastAPI with async processing for photo uploads
- AI retry logic with exponential backoff handles OpenAI API failures
- Frontend uses polling for long-running operations (photo processing)
- Comprehensive logging and monitoring throughout the system
- Production deployment through AWS Elastic Beanstalk with CloudFront

## Important Architecture Notes

- **All requests initially hit the orchestrator agent** (`urmston_town_agent`)
- **Registration agents are only triggered by valid codes** - not directly accessible
- **The orchestrator handles all non-registration conversations**
- **Session history is centralized** - all agents share the same history system
- **MCP mode is production default** - local mode for development/testing
- **Model consistency** - All agents use GPT-4.1 for MCP compatibility