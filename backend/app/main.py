import os
import re

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.db import create_db_and_tables, get_session
from app.repository import create_project, get_project_by_id, list_projects
from app.schemas import (
    StartupIdeaRequest,
    StartupProjectResponse,
    StartupProjectSummary,
    StartupReportResponse,
)
from app.services.report_generation import generate_startup_report_with_fallback
from app.services.package_export import build_markdown_package, build_pdf_package

app = FastAPI(title="StartupDocs API", version="0.1.0")

# Initialize schema on app import so local runs and tests have tables available.
create_db_and_tables()

# Comma-separated list of allowed frontend origins. Defaults to local dev.
# In production set STARTUPDOCS_CORS_ORIGINS to your deployed frontend URL(s),
# e.g. "https://your-frontend.quikdb.io". Use "*" to allow any origin.
_cors_env = os.getenv("STARTUPDOCS_CORS_ORIGINS", "http://localhost:3000")
_cors_origins = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
_allow_all = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _cors_origins,
    # Credentials cannot be combined with a wildcard origin per the CORS spec.
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/startup/report", response_model=StartupReportResponse)
def create_startup_report(payload: StartupIdeaRequest) -> StartupReportResponse:
    return generate_startup_report_with_fallback(payload)


@app.post("/api/v1/projects", response_model=StartupProjectResponse)
def create_startup_project(payload: StartupIdeaRequest) -> StartupProjectResponse:
    report = generate_startup_report_with_fallback(payload)
    with get_session() as session:
        project = create_project(session, payload, report)
        return StartupProjectResponse(
            id=project.id or 0,
            startup_name=project.startup_name,
            industry=project.industry,
            country=project.country,
            created_at=project.created_at,
            report=report,
        )


@app.get("/api/v1/projects", response_model=list[StartupProjectSummary])
def get_startup_projects() -> list[StartupProjectSummary]:
    with get_session() as session:
        projects = list_projects(session)
        return [
            StartupProjectSummary(
                id=project.id or 0,
                startup_name=project.startup_name,
                industry=project.industry,
                country=project.country,
                readiness_overall=project.readiness_overall,
                created_at=project.created_at,
            )
            for project in projects
        ]


@app.get("/api/v1/projects/{project_id}", response_model=StartupProjectResponse)
def get_startup_project(project_id: int) -> StartupProjectResponse:
    with get_session() as session:
        project = get_project_by_id(session, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        report = StartupReportResponse.model_validate(project.report_payload)
        return StartupProjectResponse(
            id=project.id or 0,
            startup_name=project.startup_name,
            industry=project.industry,
            country=project.country,
            created_at=project.created_at,
            report=report,
        )


@app.get("/api/v1/projects/{project_id}/package.md", response_class=PlainTextResponse)
def export_startup_project_markdown(project_id: int) -> str:
    with get_session() as session:
        project = get_project_by_id(session, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        report = StartupReportResponse.model_validate(project.report_payload)
        return build_markdown_package(report)


@app.get("/api/v1/projects/{project_id}/package.pdf")
def export_startup_project_pdf(project_id: int) -> Response:
    with get_session() as session:
        project = get_project_by_id(session, project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        report = StartupReportResponse.model_validate(project.report_payload)
        pdf_bytes = build_pdf_package(
            report,
            industry=project.industry,
            country=project.country,
            founder_mode=getattr(project, "founder_mode", "") or "",
        )
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", report.startup_name).strip("-") or "startup"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}-startup-package.pdf"'
            },
        )
