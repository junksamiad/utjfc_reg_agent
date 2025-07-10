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
python3 test_photo_upload.py

# Backend MCP flow test
python3 test_backend_mcp_flow.py

# S3 photo cleanup
python3 cleanup_test_photos.py
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

### Registration Agent System

The system uses a sophisticated AI agent architecture:

- **Routing Logic**: Automatic detection of registration codes (100-series for re-registration, 200-series for new registration)
- **Dual Agent Types**: 
  - `re_registration_agent`: Handles returning players
  - `new_registration_agent`: Handles new players with full 35-step workflow
- **Business Logic**: Age-based routing, sibling discounts, kit requirements, payment processing

### Key File Locations

- **Agent Definitions**: `backend/registration_agent/registration_agents.py`
- **35-Step Workflow**: `backend/registration_agent/registration_routines.py`
- **AI Response Processing**: `backend/registration_agent/responses_reg.py`
- **Tool Ecosystem**: `backend/registration_agent/tools/`
- **Database Operations**: `backend/registration_agent/tools/airtable/`
- **Chat Interface**: `frontend/web/src/app/chat/`

## External Services Integration

- **OpenAI GPT-4**: AI agent processing
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
AIRTABLE_PAT=your_token_here
GOCARDLESS_TOKEN=your_token_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
```

### Frontend Environment Variables
Create `frontend/web/.env.local` with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## AI Agent Workflow

The system implements a 35-step registration process with intelligent routing:

1. **Code Detection**: Regex pattern matching for registration codes
2. **Agent Selection**: Route to appropriate agent based on code type
3. **Conversational Flow**: Step-by-step data collection with validation
4. **Tool Integration**: Automated validation, payment processing, and data storage
5. **Error Handling**: Retry mechanisms with exponential backoff for AI failures

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