from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class StartupProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    startup_name: str = Field(index=True)
    industry: str
    country: str
    readiness_overall: int
    report_payload: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
