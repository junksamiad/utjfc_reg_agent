*** ngrok ***

https://utjfc.ngrok.app

*** frontend / backend start ***

*** backend ***

cd /Users/leehayton/Cursor\ Projects/utjfc_reg_agent && cd backend && source .venv/bin/activate && uvicorn server:app --reload --port 8000

*** USE THIS TO START BACKEND ***
source .venv/bin/activate && OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2) uvicorn server:app --reload --port 8000

** cd backend && source .venv/bin/activate && OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d'=' -f2) uvicorn server:app --reload --port 8000 **

|||||

cd backend

source .venv/bin/activate

uvicorn server:app --reload --port 8000

*** frontend ***

cd frontend/web

pnpm dev

-----

*** docker ***

When running in Docker, use Docker Compose file to start both servers:

docker compose up

Or to rebuild after changes:

docker compose up --build
docker-compose build --no-cache frontend
docker-compose up -d --force-recreate frontend

To see logs:
docker-compose logs -f (to follow).

To stop services:

docker compose down 
docker compose down -v


*** mcp server ***

cd mcp_server

source .venv/bin/activate

python server.py

now deployed on Replit @ https://utjfc-mcp-server.replit.app/mcp

-----

*** initialise ***

pip install -r requirements.txt
python -m venv .venv