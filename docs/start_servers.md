
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


*** backend ***

cd backend

source .venv/bin/activate

uvicorn server:app --reload --port 8000


*** mcp server ***

cd mcp_server

source .venv/bin/activate

python server.py

-----

now deployed on Replit @ https://utjfc-mcp-server.replit.app/mcp


*** frontend ***

cd frontend/web

pnpm dev


*** initialise ***

pip install -r requirements.txt
python -m venv .venv