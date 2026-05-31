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

## QuikDB Deployment (single combined container)

QuikDB builds an app by detecting the stack at the **repo root**. Because this is
a monorepo (`frontend/` + `backend/`), the root has no single detectable stack —
so the project ships a **root `Dockerfile`** that builds *both* services into one
image. The Next.js frontend is the public service and proxies `/api/*` to the
FastAPI backend on an internal port, so there is **one deployment, one URL, and
no CORS to configure**.

### Deploy

1. **Create Deployment** → select repo `Mozzicato/start-up-docz`, branch `main`.
2. QuikDB detects the root `Dockerfile` and builds it. If the form asks for
   commands:
   - **Build Command:** leave empty (the `Dockerfile` builds everything).
   - **Start Command:** `./start.sh` (this is also the Dockerfile's default).
3. **Environment Variables** — all **optional**. Add any LLM keys you have
   (copy the values from your local `.env`):
   ```
   GEMINI_API_KEY=<paste value from your .env>
   OPENROUTER_API_KEY=<paste value from your .env>
   GROQ_API_KEY=<paste value from your .env>
   MISTRAL_API_KEY=<paste value from your .env>
   ```
   - You do **not** set `NEXT_PUBLIC_API_BASE_URL` — the frontend calls the
     backend on the same origin via `/api`.
   - You do **not** set `STARTUPDOCS_CORS_ORIGINS` or `DATABASE_URL`.
   - With no keys, the app still works using its built-in deterministic
     generator (it just won't call a real LLM).
4. **Deploy**, wait until live, open the URL.

### Verification

- Open the deployment URL → fill the intake form → **Generate**.
- A report renders (LLM output if keys are set, otherwise the fallback package).
- Export downloads a `.md` file.
- `…/api/v1/projects` and `…/health` (proxied) respond with JSON.

### Troubleshooting

| Symptom | Fix |
|--------|-----|
| `unsupported app type: unknown` | QuikDB didn't pick up the root `Dockerfile`. Make sure the deployment branch is `main` and the `Dockerfile` is at the repo root (it is). |
| API calls 502 right after deploy | Backend still starting inside the container — wait a few seconds and retry. |
| Reports look generic/templated | No valid API key reached a provider, so the deterministic fallback was used. Add a working key and redeploy. |

### Alternative: two separate deployments

If you prefer (or QuikDB adds per-service root directories), you can instead put
the **frontend** and **backend** in two separate repos — each repo's root then
has a detectable stack (`package.json` / `requirements.txt`). In that case set
`NEXT_PUBLIC_API_BASE_URL` on the frontend to the backend's URL and
`STARTUPDOCS_CORS_ORIGINS` on the backend to the frontend's URL. The single
combined container above avoids all of that and is the recommended path.

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
Dockerfile             # root: builds frontend + backend into one image
start.sh               # root: launches backend (internal) + frontend (public)
quikdb.json            # QuikDB deploy config
docker-compose.yml     # local two-service orchestration
.env.example           # configuration template
prd.md                 # product requirements
```

---

**Repository:** https://github.com/Mozzicato/start-up-docz
**Target platform:** QuikDB Compute
**Status:** MVP complete — source recovered, deploy-ready
