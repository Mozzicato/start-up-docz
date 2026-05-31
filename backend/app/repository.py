from sqlmodel import Session, desc, select

from app.models import StartupProject
from app.schemas import StartupIdeaRequest, StartupReportResponse


def create_project(
    session: Session, payload: StartupIdeaRequest, report: StartupReportResponse
) -> StartupProject:
    project = StartupProject(
        startup_name=report.startup_name,
        industry=payload.industry,
        country=payload.country,
        readiness_overall=report.readiness.overall,
        report_payload=report.model_dump(mode="json"),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session, limit: int = 15) -> list[StartupProject]:
    statement = select(StartupProject).order_by(desc(StartupProject.created_at)).limit(limit)
    return list(session.exec(statement))


def get_project_by_id(session: Session, project_id: int) -> StartupProject | None:
    return session.get(StartupProject, project_id)
