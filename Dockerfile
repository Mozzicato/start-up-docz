# Single-container build for QuikDB: Next.js frontend + FastAPI backend.
# The frontend (public) proxies /api/* to the backend on 127.0.0.1:8000,
# so there is one public port, one URL, and no CORS to configure.

# ---------- Stage 1: build the Next.js frontend ----------
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Same-origin: the browser calls /api/... which Next proxies to the backend.
ENV NEXT_PUBLIC_API_BASE_URL=""
RUN npm run build

# ---------- Stage 2: runtime with Python + Node ----------
FROM node:20-slim
WORKDIR /app

# Python for the FastAPI backend
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r backend/requirements.txt

# Application code
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend ./frontend

COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# QuikDB injects $PORT; Next listens on it, backend stays internal on 8000.
ENV PORT=3000
CMD ["./start.sh"]
