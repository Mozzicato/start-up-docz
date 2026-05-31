#!/bin/sh
# Start the FastAPI backend (internal) and the Next.js frontend (public).
set -e

# Backend on a fixed internal port; the frontend proxies /api/* to it.
cd /app/backend
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Frontend on the platform-provided $PORT (the public port).
cd /app/frontend
exec npx next start -p "${PORT:-3000}"
