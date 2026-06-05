from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class QualityAssessment(BaseModel):
    overall: int = 0
    section_scores: dict[str, int] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)


class StartupIdeaRequest(BaseModel):
    startup_name: str | None = Field(default=None, max_length=120)
    idea: str = Field(min_length=20, max_length=3000)
    industry: str = Field(min_length=2, max_length=80)
    country: str = Field(min_length=2, max_length=80)
    target_audience: str = Field(min_length=4, max_length=240)
    business_model: str = Field(min_length=3, max_length=120)
    founder_mode: Literal["mvp", "vc", "grant"] = "mvp"
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
    differentiation: str = ""
    product_build_plan: str = ""
    feasibility_report: str
    unit_economics: str = ""
    cac_model: str = ""
    team_and_execution_strategy: str = ""
    roadmap: list[str]
    mvp_cost_breakdown: list[str] = Field(default_factory=list)
    legal_requirements: list[str] = Field(default_factory=list)
    growth_experiments: list[str] = Field(default_factory=list)
    risk_register: list[str] = Field(default_factory=list)
    funding_opportunities: list[str]
    launch_checklist: list[str]
    sources: list[str] = Field(default_factory=list)
    quality_assessment: QualityAssessment = Field(default_factory=QualityAssessment)


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
