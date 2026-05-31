from pydantic import BaseModel, Field
from datetime import datetime


class StartupIdeaRequest(BaseModel):
    startup_name: str | None = Field(default=None, max_length=120)
    idea: str = Field(min_length=20, max_length=3000)
    industry: str = Field(min_length=2, max_length=80)
    country: str = Field(min_length=2, max_length=80)
    target_audience: str = Field(min_length=4, max_length=240)
    business_model: str = Field(min_length=3, max_length=120)
    budget_range_usd: int = Field(ge=0)
    timeline_months: int = Field(ge=1, le=60)


class ReadinessScore(BaseModel):
    overall: int
    market_demand: float
    technical_feasibility: float
    competition: float
    funding_potential: float
    execution_complexity: float
    go_to_market_readiness: float


class StartupReportResponse(BaseModel):
    startup_name: str
    summary: str
    readiness: ReadinessScore
    market_research: str
    competitor_analysis: str
    feasibility_report: str
    roadmap: list[str]
    funding_opportunities: list[str]
    launch_checklist: list[str]


class StartupProjectSummary(BaseModel):
    id: int
    startup_name: str
    industry: str
    country: str
    readiness_overall: int
    created_at: datetime


class StartupProjectResponse(BaseModel):
    id: int
    startup_name: str
    industry: str
    country: str
    created_at: datetime
    report: StartupReportResponse
