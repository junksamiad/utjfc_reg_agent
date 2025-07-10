# UTJFC Development Setup Guide
## Local Development Environment Setup & Server Commands

### Document Information
- **Purpose**: Complete setup guide for local development
- **Audience**: Developers setting up the project locally
- **Scope**: Frontend, backend, MCP server, and Docker configurations

---

## Table of Contents
1. [Initial Project Setup](#initial-project-setup)
2. [Backend Development](#backend-development)
3. [Frontend Development](#frontend-development)
4. [MCP Server](#mcp-server)
5. [Docker Development](#docker-development)
6. [Development URLs](#development-urls)
7. [Common Development Tasks](#common-development-tasks)

---

## Initial Project Setup

### Prerequisites
- **Python 3.11+**: For backend development
- **Node.js 18+**: For frontend development
- **Docker**: For containerized development (optional)
- **Git**: For version control

### Project Structure
```
utjfc_reg_agent/
├── backend/          # FastAPI backend
├── frontend/web/     # Next.js frontend
├── mcp_server/       # MCP integration server
└── system_docs/      # Documentation
```

---

## Backend Development

### Environment Setup

#### 1. Navigate to Backend Directory
```bash
cd backend
```

#### 2. Create Virtual Environment (First Time Only)
```bash
python -m venv .venv
```

#### 3. Activate Virtual Environment
```bash
source .venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Configure Environment Variables
```bash
# Copy example environment file
cp env.example .env

# Edit .env with your actual API keys
# Required variables:
# - OPENAI_API_KEY
# - AIRTABLE_API_KEY  
# - GOCARDLESS_ACCESS_TOKEN
# - TWILIO_ACCOUNT_SID
# - TWILIO_AUTH_TOKEN
```

### Starting the Backend Server

#### Recommended Command (with environment variables)
```bash
cd backend && source .venv/bin/activate && \
OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2) \
uvicorn server:app --reload --port 8000
```

#### Alternative (if .env is properly configured)
```bash
cd backend
source .venv/bin/activate
uvicorn server:app --reload --port 8000
```

#### Development Server Details
- **URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Auto-reload**: Enabled for development

---

## Frontend Development

### Environment Setup

#### 1. Navigate to Frontend Directory
```bash
cd frontend/web
```

#### 2. Install Dependencies
```bash
npm install
```

#### 3. Configure Environment Variables
```bash
# Create environment file
cp .env.example .env.local

# Edit .env.local with:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Starting the Frontend Server

#### Using npm
```bash
cd frontend/web
npm run dev
```

#### Using pnpm (preferred)
```bash
cd frontend/web
pnpm dev
```

#### Alternative package managers
```bash
# Using yarn
yarn dev

# Using bun
bun dev
```

#### Development Server Details
- **URL**: `http://localhost:3000`
- **Chat Interface**: `http://localhost:3000/chat`
- **Hot Reload**: Enabled for development
- **API Proxy**: Configured to proxy `/api/*` to backend

---

## MCP Server

### Local Development (Deprecated)

#### Setup (if running locally)
```bash
cd mcp_server
source .venv/bin/activate
python server.py
```

### Production MCP Server
The MCP server is now deployed on Replit:
- **URL**: `https://utjfc-mcp-server.replit.app/mcp`
- **Status**: Production ready
- **Usage**: Backend automatically connects to this URL

#### Backend Configuration
```bash
# In backend/.env file:
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
USE_MCP=true
```

---

## Docker Development

### Starting All Services

#### Start with Docker Compose
```bash
docker compose up
```

#### Rebuild After Changes
```bash
docker compose up --build
```

#### Force Rebuild (no cache)
```bash
docker-compose build --no-cache
docker compose up
```

### Individual Service Management

#### Rebuild Specific Service
```bash
# Rebuild frontend only
docker-compose build --no-cache frontend
docker-compose up -d --force-recreate frontend
```

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Stop Services
```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Docker Configuration Details
- **Backend Port**: 8000 (mapped to host)
- **Frontend Port**: 3000 (mapped to host)
- **Environment**: Uses docker-compose.yml configuration
- **Volumes**: Code changes reflected without rebuild

---

## Development URLs

### Local Development
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Chat Interface**: `http://localhost:3000/chat`

### External Services
- **MCP Server**: `https://utjfc-mcp-server.replit.app/mcp`
- **Production Frontend**: `https://urmstontownjfc.co.uk/chat/`
- **Production Backend**: `https://d1ahgtos8kkd8y.cloudfront.net/api/`

### Development Tunneling (ngrok)
If you need to expose your local development server:

#### Frontend Tunnel
```bash
# Install ngrok if not already installed
# Then expose frontend
ngrok http 3000
```

#### Backend Tunnel  
```bash
# Expose backend API
ngrok http 8000
```

**Historical ngrok URL**: `https://utjfc.ngrok.app` (no longer active)

---

## Common Development Tasks

### Backend Development Tasks

#### Update Dependencies
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

#### Run Tests
```bash
cd backend
source .venv/bin/activate
python -m pytest
```

#### Database Migrations (Airtable)
```bash
cd backend
source .venv/bin/activate
python registration_agent/tools/airtable/add_new_fields.py
```

#### Check Code Quality
```bash
cd backend
source .venv/bin/activate
flake8 .
black .
```

### Frontend Development Tasks

#### Update Dependencies
```bash
cd frontend/web
npm install
```

#### Build for Production
```bash
cd frontend/web
npm run build
```

#### Type Checking
```bash
cd frontend/web
npm run type-check
```

#### Linting
```bash
cd frontend/web
npm run lint
```

### Full Stack Development Workflow

#### 1. Start All Services
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && \
OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2) \
uvicorn server:app --reload --port 8000

# Terminal 2: Frontend  
cd frontend/web && pnpm dev
```

#### 2. Verify Services
- Backend health: `curl http://localhost:8000/health`
- Frontend: Open `http://localhost:3000/chat`
- Test integration: Send a chat message

#### 3. Development Testing
```bash
# Test backend endpoints
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "test", "session_id": "dev"}'

# Test file upload
curl -X POST http://localhost:8000/upload-async \
  -F "file=@test_photo.jpg" \
  -F "session_id=dev"
```

### Environment Management

#### Switching Between Environments

##### Development (Local)
```bash
# Backend: Uses local .env file
# Frontend: Uses .env.local with localhost API URL
# MCP: Uses production Replit server
```

##### Production Testing
```bash
# Frontend: Update .env.local
NEXT_PUBLIC_API_URL=https://d1ahgtos8kkd8y.cloudfront.net

# Backend: No changes needed (uses production services)
```

#### Environment Variables Checklist

##### Backend (.env)
- `OPENAI_API_KEY` - OpenAI API access
- `AIRTABLE_API_KEY` - Database access
- `GOCARDLESS_ACCESS_TOKEN` - Payment processing
- `TWILIO_ACCOUNT_SID` - SMS notifications
- `TWILIO_AUTH_TOKEN` - SMS authentication
- `AWS_ACCESS_KEY_ID` - S3 photo storage
- `AWS_SECRET_ACCESS_KEY` - S3 authentication

##### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API endpoint

### Troubleshooting Common Issues

#### Backend Won't Start
```bash
# Check virtual environment
which python  # Should point to .venv/bin/python

# Check dependencies
pip list

# Check environment variables
grep OPENAI_API_KEY .env
```

#### Frontend Build Errors
```bash
# Clear cache and rebuild
rm -rf .next
rm -rf node_modules
npm install
npm run dev
```

#### Docker Issues
```bash
# Clean Docker environment
docker compose down -v
docker system prune -f
docker compose up --build
```

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill processes if needed
kill -9 <PID>
```

---

## Conclusion

This development setup guide provides all the necessary commands and procedures for setting up and running the UTJFC registration system locally. The setup supports:

### Development Flexibility
- **Multiple package managers**: npm, pnpm, yarn, bun
- **Docker option**: Containerized development environment
- **Environment switching**: Easy local/production configuration

### Developer Experience
- **Hot reload**: Both frontend and backend auto-reload on changes
- **API documentation**: Built-in Swagger UI for backend
- **Type safety**: TypeScript for frontend development
- **Testing**: Built-in test commands and quality checks

### Production Alignment
- **Same stack**: Local development mirrors production environment
- **External services**: Uses production MCP server and external APIs
- **Environment parity**: Consistent configuration management

Follow these procedures for reliable local development that closely matches the production environment.