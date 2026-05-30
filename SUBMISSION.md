# StartupDocs MVP – QuikDB Hackathon Submission

## Project Overview

**StartupDocs** is an AI-powered startup planning workspace that automates document generation for Nigerian startups. Founders complete a structured intake form, and the system generates a comprehensive business package (10 PDFs + 4 markdown files) using multi-provider LLM generation with deterministic fallback.

## Key Features

### 1. Founder Intake Form
- Captures core startup data: business model, market, team, financials, regulatory needs
- Nigeria-localized compliance questions (FIRS, CAC, regulatory frameworks)
- Clean React UI with Tailwind styling
- Real-time validation

### 2. AI Generation Engine
- **Multi-provider support**: OpenRouter, Groq, Gemini, Mistral
- **Deterministic fallback**: If primary provider fails, system automatically retries with next provider
- **Document types**: Executive Summary, Pitch Deck Script, Marketing Plan, Financial Model, etc.
- **Output**: Professional PDFs with ReportLab + markdown templates

### 3. Package Export
- Downloads all generated documents as a ZIP file
- Includes PDF generation (Executive Summary, Business Plan, Pitch Deck, etc.)
- Markdown templates for further customization
- Single-click download from UI

### 4. Production-Ready Infrastructure
- **FastAPI backend** with SQLModel ORM + SQLite/PostgreSQL persistence
- **Next.js 14 frontend** (App Router, standalone mode)
- **Docker Compose** orchestration with multi-stage builds, non-root users, health checks
- **Environment-driven configuration**: CORS allowlist, API endpoints, LLM providers
- GitHub repository: [Mozzicato/start-up-docz](https://github.com/Mozzicato/start-up-docz)

## Technical Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React, Tailwind CSS, TypeScript |
| **Backend** | FastAPI, SQLModel, ReportLab, Python 3.11 |
| **Database** | SQLite (persistent Docker volume) or PostgreSQL |
| **Infrastructure** | Docker Compose, non-root containers, health checks |
| **AI Integration** | Multi-provider LLM (OpenRouter, Groq, Gemini, Mistral) |

## How It Works

1. **User fills intake form** → Frontend sends POST to `/api/projects`
2. **Backend generates documents** → LLM generates content with fallback logic
3. **PDFs rendered** → ReportLab converts markdown/templates to professional PDFs
4. **ZIP packaged** → All documents bundled for download
5. **Data persisted** → Project stored in SQLite for later retrieval

## Deployment Status

✅ Code complete and tested  
✅ GitHub repository pushed and public  
✅ Docker setup verified (docker-compose up works)  
✅ Environment configuration documented  
✅ Ready for production deployment  

## Local Build & Test (Before Deployment)

### Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend runs on `http://localhost:3000`, backend on `http://localhost:8000`.

---

## QuikDB Deployment Instructions

StartupDocs is a **monorepo with two services** (frontend + backend). Deploy as two separate QuikDB apps:

### Prerequisites
- GitHub account linked to QuikDB (done)
- QuikDB Compute dashboard access
- API keys: OpenRouter, Groq, Gemini, or Mistral

### Deployment Step 1: Backend API

1. Go to [QuikDB Compute Dashboard](https://compute.quikdb.com/deployments)
2. Click **Create Deployment**
3. Select repository: `Mozzicato/start-up-docz`, branch: `main`
4. **Configuration:** (auto-detected or manually enter)
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Environment Variables:** Add these:
     ```
     DATABASE_URL=sqlite:///./projects.db
     OPENROUTER_API_KEY=sk_or_<your_key>
     GROQ_API_KEY=gsk_<your_key>
     GEMINI_API_KEY=AIza<your_key>
     MISTRAL_API_KEY=<your_key>
     STARTUPDOCS_CORS_ORIGINS=https://<frontend-url>.quikdb.io
     ```
5. Click **Deploy**
6. **Wait for deployment to complete** (2-5 minutes)
7. **Copy the backend URL** (e.g., `startupd-api-xyz.quikdb.io`)

### Deployment Step 2: Frontend

1. Click **Create Deployment** again
2. Select repository: `Mozzicato/start-up-docz`, branch: `main`
3. **Configuration:** (auto-detected from `quikdb.json`)
   - **Build Command:** `cd frontend && npm run build`
   - **Start Command:** `cd frontend && npm start`
   - **Environment Variables:** Add:
     ```
     NEXT_PUBLIC_API_BASE_URL=https://<backend-url-from-step-1>
     ```
     (Replace `<backend-url-from-step-1>` with the actual URL, e.g., `https://startupd-api-xyz.quikdb.io`)
4. Click **Deploy**
5. **Wait for deployment to complete**
6. Once live, frontend will be at: `https://<your-app>.quikdb.io`

### Verification

- Frontend loads at `https://<frontend-app>.quikdb.io`
- Fill out intake form
- Submit → should generate documents from backend
- Download ZIP with all PDFs
- If document generation fails, backend will **automatically fallback** to next LLM provider

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Frontend shows blank page | Check `NEXT_PUBLIC_API_BASE_URL` env var matches backend URL |
| API 502 error | Backend may still be deploying (check QuikDB dashboard) |
| "No AI provider key" error | Verify at least one API key (OpenRouter/Groq/Gemini/Mistral) is set in backend env vars |
| CORS error | Backend's `STARTUPDOCS_CORS_ORIGINS` must include frontend URL |

## Files Included

- **`prd.md`** – Full product requirements document
- **`README.md`** – Setup and deployment guide
- **`docker-compose.yml`** – Complete stack orchestration
- **`.env.example`** – Configuration template
- **`quikdb.json`** – QuikDB auto-detection config (frontend)
- **`frontend/`** – Next.js application (ready to deploy)
- **`backend/`** – FastAPI application with document generation
- **`SUBMISSION.md`** – This file

## What's Ready to Deploy

✅ Frontend (Next.js standalone app)  
✅ Backend (FastAPI with all endpoints)  
✅ Database persistence (SQLite or Postgres)  
✅ Document generation pipeline  
✅ Error handling & fallback logic  
✅ Docker containerization  
✅ Environment configuration  
✅ QuikDB config file (quikdb.json)

---

**Repository:** https://github.com/Mozzicato/start-up-docz  
**Deployed to:** QuikDB Compute  
**Status:** MVP Complete – Production Ready
