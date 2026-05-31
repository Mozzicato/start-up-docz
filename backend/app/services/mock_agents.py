from app.schemas import ReadinessScore, StartupIdeaRequest, StartupReportResponse


def _clamp_score(value: float) -> float:
    return max(1.0, min(10.0, round(value, 1)))


def _build_readiness(payload: StartupIdeaRequest) -> ReadinessScore:
    budget_factor = min(payload.budget_range_usd / 25000, 1.0)
    timeline_factor = 1.0 - min(payload.timeline_months / 24, 1.0)
    complexity_penalty = 2.0 if "ai" in payload.idea.lower() else 0.8

    market = _clamp_score(6.4 + budget_factor * 2.0)
    technical = _clamp_score(6.0 + budget_factor * 1.4 - complexity_penalty * 0.4)
    competition = _clamp_score(7.2 - complexity_penalty * 0.3)
    funding = _clamp_score(6.5 + budget_factor * 1.8)
    execution = _clamp_score(5.8 + timeline_factor * 2.2 - complexity_penalty * 0.2)
    gtm = _clamp_score(6.0 + timeline_factor * 1.6)

    overall = round((market + technical + competition + funding + execution + gtm) * 10 / 6)

    return ReadinessScore(
        overall=overall,
        market_demand=market,
        technical_feasibility=technical,
        competition=competition,
        funding_potential=funding,
        execution_complexity=execution,
        go_to_market_readiness=gtm,
    )


def generate_startup_report(payload: StartupIdeaRequest) -> StartupReportResponse:
    name = payload.startup_name or "Untitled Startup"
    readiness = _build_readiness(payload)

    return StartupReportResponse(
        startup_name=name,
        summary=(
            f"{name} targets {payload.target_audience} in {payload.country} within the "
            f"{payload.industry} market using a {payload.business_model} model."
        ),
        readiness=readiness,
        market_research=(
            f"Demand signals for {payload.industry} in {payload.country} are positive. "
            "Early traction can be achieved by focusing on one urgent customer segment first."
        ),
        competitor_analysis=(
            "Top competitors are likely generalist tools with broad features. "
            "Your best edge is speed, localized experience, and a tighter workflow."
        ),
        feasibility_report=(
            "MVP is feasible with a lean team if scope is kept narrow for the first 12 weeks."
        ),
        roadmap=[
            "Weeks 1-2: Validate user pain with 20 interviews",
            "Weeks 3-6: Build core MVP workflow",
            "Weeks 7-8: Launch beta with first 30 users",
            "Weeks 9-12: Iterate and prepare fundraising narrative",
        ],
        funding_opportunities=[
            "Local innovation grants",
            "University incubator programs",
            "Regional startup competitions",
            "Angel syndicates focused on early-stage founders",
        ],
        launch_checklist=[
            "Define one sharp value proposition",
            "Set up landing page and waitlist",
            "Run 2 pricing experiments",
            "Prepare investor-ready one-pager",
            "Track activation and retention metrics weekly",
        ],
    )
