# StartupDocs MVP — QuikDB Hackathon Submission

## Project Overview

**StartupDocs** is an AI-powered startup analysis workspace. A founder fills in a
short intake form (idea, industry, country, audience, business model, budget,
timeline) and the backend generates a structured startup package: an executive
summary, readiness scores, market research, competitor analysis, a feasibility
report, a roadmap, funding opportunities, and a launch checklist. The full
package can be exported as a single Markdown document.

## Key Features

- **Founder intake form** — clean Next.js + Tailwind UI, typed end-to-end.
- **Multi-provider LLM generation** — tries OpenRouter → Groq → Gemini → Mistral
  in a configurable order and uses the first that succeeds.
- **Deterministic fallback** — if every provider fails or no API keys are set,
  a built-in mock generator returns a complete, valid package so the app **always
  works**, even with zero configuration.
- **Markdown package export** — the whole report is downloadable as a single
  `.md` file via `/api/v1/projects/{id}/package.md`.
- **Persistence** — projects are stored via SQLModel (SQLite by default,
  Postgres-ready through `DATABASE_URL`).

## Technical Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, SQLModel, httpx, Pydantic v2, Python 3.12 |
| **Database** | SQLite (default) or any SQLAlchemy URL via `DATABASE_URL` |
| **AI** | OpenRouter, Groq, Gemini, Mistral (with deterministic fallback) |
| **Infra** | Docker + docker-compose, `quikdb.json` for QuikDB auto-detect |

## API Endpoints (backend)

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/health` | Health check |
| POST | `/api/v1/startup/report` | Generate a report (no persistence) |
| POST | `/api/v1/projects` | Generate + save a project |
| GET  | `/api/v1/projects` | List saved projects |
| GET  | `/api/v1/projects/{id}` | Fetch one project |
| GET  | `/api/v1/projects/{id}/package.md` | Export project as Markdown |

The frontend talks to these via `NEXT_PUBLIC_API_BASE_URL`.

---

## Local Build & Test

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm start                       # http://localhost:3000
```

Copy `.env.example` to `.env` and fill in any API keys you want to use. **No keys
are required** — without them the app uses the deterministic fallback generator.

---

## QuikDB Deployment

StartupDocs is a **monorepo with two services** (backend + frontend). You deploy
**two separate QuikDB deployments from the same repo/branch**
(`Mozzicato/start-up-docz`, `main`). Deploy the **backend first**, because the
frontend needs the backend's URL at build time.

`quikdb.json` (repo root) auto-fills the **frontend** commands. The backend
commands are entered manually in the QuikDB "Configuration" step.

### Step 1 — Deploy the Backend (API)

1. **Create Deployment** → select repo `Mozzicato/start-up-docz`, branch `main`.
2. In **Configuration**, enter:
   - **Build Command:** `cd backend && pip install -r requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables** — add these exact keys. Copy the four API-key
   *values* from your local `.env` file:
   ```
   STARTUPDOCS_CORS_ORIGINS=*
   GEMINI_API_KEY=<paste value from your .env>
   OPENROUTER_API_KEY=<paste value from your .env>
   GROQ_API_KEY=<paste value from your .env>
   MISTRAL_API_KEY=<paste value from your .env>
   ```
   - `STARTUPDOCS_CORS_ORIGINS=*` → type a literal `*`. (You can't know the
     frontend URL yet; `*` allows any origin. Tighten it in Step 3 if you want.)
   - **Do NOT add `DATABASE_URL`** — leave it out and the app uses SQLite
     automatically. Only set it if you have your own Postgres server.
   - The four API keys are **optional**. If you skip them, the app still works
     using its built-in fallback generator — it just won't call a real LLM.
   - You don't need `STARTUPDOCS_PROVIDER_ORDER` either; the default order is fine.
4. **Deploy**, wait until live, then **copy the backend URL**
   (e.g. `https://startupdocs-api-xyz.quikdb.io`). Verify `…/health` returns
   `{"status":"ok"}`.

### Step 2 — Deploy the Frontend

1. **Create Deployment** → same repo `Mozzicato/start-up-docz`, branch `main`.
2. **Configuration** is auto-detected from `quikdb.json`:
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Start Command:** `cd frontend && npx next start -p ${PORT:-3000}`
3. **Environment Variables** — set **before deploying** (Next.js inlines
   `NEXT_PUBLIC_*` at build time):
   ```
   NEXT_PUBLIC_API_BASE_URL=https://<backend-url-from-step-1>
   ```
4. **Deploy**, wait until live, then **copy the frontend URL**
   (e.g. `https://startupdocs-xyz.quikdb.io`).

### Step 3 — Lock down CORS (recommended)

Go back to the **backend** deployment, change
`STARTUPDOCS_CORS_ORIGINS` from `*` to your frontend URL
(`https://<frontend-url>`), and redeploy. This restricts the API to your
frontend instead of allowing any origin.

### Verification

- Open the frontend URL → fill the intake form → **Generate**.
- A report renders (LLM output if keys are set, otherwise the fallback package).
- Export downloads a `.md` file.

### Troubleshooting

| Symptom | Fix |
|--------|-----|
| Frontend can't reach API / CORS error | Backend `STARTUPDOCS_CORS_ORIGINS` must include the frontend URL (or be `*`). |
| Frontend calls `localhost:8000` | `NEXT_PUBLIC_API_BASE_URL` was not set **before** the frontend build; set it and rebuild. |
| API 502 right after deploy | Backend still starting — wait and retry. |
| Reports look generic/templated | No valid API key reached a provider, so the deterministic fallback was used. Add a working key. |

---

## Repository Contents

```
backend/
  app/
    main.py            # FastAPI app + routes + CORS
    db.py              # engine/session (DATABASE_URL-aware)
    models.py          # SQLModel tables
    schemas.py         # Pydantic request/response models
    repository.py      # CRUD helpers
    services/
      llm_provider.py        # OpenRouter/Groq/Gemini/Mistral clients
      report_generation.py   # provider order + fallback orchestration
      mock_agents.py         # deterministic fallback generator
      package_export.py      # Markdown package builder
  requirements.txt
  Dockerfile
frontend/
  app/                 # Next.js App Router (page.tsx, layout.tsx, globals.css)
  lib/api.ts           # typed API client (uses NEXT_PUBLIC_API_BASE_URL)
  package.json, tsconfig.json, next.config.mjs, tailwind/postcss config
  Dockerfile
quikdb.json            # QuikDB auto-detect config (frontend)
docker-compose.yml     # local two-service orchestration
.env.example           # configuration template
prd.md                 # product requirements
```

---

**Repository:** https://github.com/Mozzicato/start-up-docz
**Target platform:** QuikDB Compute
**Status:** MVP complete — source recovered, deploy-ready
