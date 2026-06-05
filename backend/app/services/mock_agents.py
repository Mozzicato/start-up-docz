from app.schemas import ReadinessScore, StartupIdeaRequest, StartupReportResponse
from app.services.startup_playbooks import country_playbook


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
    business_model = payload.business_model
    if business_model.strip().lower() in {"i dont know", "i don't know", "unknown", "n/a", "na"}:
        business_model = "Transaction-fee marketplace"

    summary_suffix = {
        "mvp": "Execution should prioritize speed-to-learning and repeat usage.",
        "vc": "Narrative should emphasize scale potential, category creation, and expansion economics.",
        "grant": "Narrative should emphasize inclusion outcomes and measurable social impact.",
    }.get(payload.founder_mode, "Execution should prioritize speed-to-learning and repeat usage.")

    playbook = country_playbook(payload)

    report = StartupReportResponse(
        startup_name=name,
        summary=(
            f"{name} targets {payload.target_audience} in {payload.country} within the "
            f"{payload.industry} market using a {business_model} model. "
            "The strongest near-term wedge is trust: faster matching + instant settlement + dispute safety. "
            f"{summary_suffix}"
        ),
        readiness=readiness,
        market_research=(
            f"Demand signals for {payload.industry} in {payload.country} are favorable when focused on one "
            "high-frequency use case first (for example, assignment support and campus errands). "
            "A practical top-down framing is TAM = all digitally active students, SAM = students at target "
            "campuses with repeat service need, and SOM = first 1-3 campuses in the first year. "
            "Winning channels are campus ambassadors, WhatsApp communities, and referral loops."
        ),
        competitor_analysis=(
            "Likely alternatives include freelance marketplaces and local social-channel deal flow. "
            "The gap is usually payment trust and fulfillment reliability for small student jobs. "
            "Your wedge should be escrow-backed instant payouts, identity verification, and campus-based trust scores."
        ),
        differentiation=(
            "Core differentiation should be trust infrastructure for micro-gigs: verified student profiles, "
            "escrow first, instant release after proof-of-work, and a campus reputation graph. This creates a "
            "defensible loop where better trust drives faster matches and lower disputes."
        ),
        product_build_plan=(
            "Architecture recommendation: Next.js frontend, FastAPI backend, Postgres + Redis queue, and a payment "
            "orchestration layer with webhook reconciliation. Build MVP in 4 slices: (1) profile + KYC-lite onboarding, "
            "(2) job posting and matching, (3) escrow hold/release flow, and (4) disputes + trust scoring. Start with "
            "manual operations for disputes, then automate after clear policy patterns emerge."
        ),
        feasibility_report=(
            "MVP is feasible in 8-12 weeks with a lean team if the first release is constrained to one campus, "
            "one payment corridor, and one dispute policy. Top risks: fraud, low repeat usage, and payout failures. "
            "Mitigation: KYC-lite checks, strict service categories, and real-time payment monitoring."
        ),
        unit_economics=(
            "Baseline model: 10-15% take-rate per completed job + optional instant payout fee. "
            "Track contribution margin per order = (take-rate + payout fee) - payment processing - support/dispute costs. "
            "Target break-even at campus level once repeat booking exceeds 35% and CAC payback is below 8 weeks."
        ),
        cac_model=(
            "CAC model by channel: CAC = (channel spend + ambassador incentives + onboarding ops) / activated users. "
            "Track separately for campus ambassadors, paid social, and referral loops. Initial CAC target: < $6 per "
            "activated student with payback in <= 8 weeks via repeat bookings and take-rate revenue."
        ),
        team_and_execution_strategy=(
            "Two viable paths: (1) vibe-code with one strong technical founder + part-time product designer for first "
            "6 weeks, then hire one backend engineer once payment volume rises; (2) hire a compact core team upfront "
            "(full-stack engineer, product designer, operations lead). Keep legal/compliance support fractional instead "
            "of full-time in MVP stage."
        ),
        build_vs_buy=playbook["build_vs_buy"],
        roadmap=[
            "Weeks 1-2: Interview 25 students and map top 3 urgent paid tasks",
            "Weeks 3-4: Build posting, matching, escrow hold, and release flow",
            "Weeks 5-6: Pilot in one campus with 50 active users and daily operations support",
            "Weeks 7-8: Launch referral program and reduce time-to-match below 30 minutes",
            "Weeks 9-10: Add trust score, dispute workflow, and seller quality controls",
            "Weeks 11-12: Expand to second campus and publish traction metrics",
        ],
        mvp_cost_breakdown=playbook["mvp_cost_breakdown"],
        tooling_stack=playbook["tooling_stack"],
        incorporation_playbook=playbook["incorporation_playbook"],
        legal_requirements=playbook["legal_requirements"],
        growth_experiments=[
            "Campus ambassador flywheel: recruit 10 ambassadors and measure referral conversion by hostel/faculty",
            "Category sequencing: test tutoring vs errands and keep the category with highest repeat booking",
            "Pricing A/B: compare flat take-rate vs dynamic take-rate by job size",
            "Trust badge rollout: measure dispute-rate reduction after verified-profile badge",
            "Retention trigger: send weekly job-match digest and track week-4 reactivation",
        ],
        risk_register=[
            "Fraud and fake job posts; mitigation: profile verification and payout hold rules",
            "Payment delays from processors; mitigation: multi-rail payout fallback and alerting",
            "Low liquidity in early supply; mitigation: seed providers via ambassador incentives",
            "Regulatory exposure in escrow-like flows; mitigation: legal review and licensed partner rails",
            "Trust erosion from unresolved disputes; mitigation: published SLA and escalation policy",
        ],
        funding_opportunities=playbook["funding_opportunities"],
        launch_checklist=[
            "Define one primary job-to-be-done and one ICP for first launch",
            "Implement escrow, payout alerts, and dispute SLA before scale",
            "Set up onboarding scripts for first 100 users and 20 task providers",
            "Run two pricing tests on take-rate and instant payout fee",
            "Track activation, repeat booking, dispute rate, and NPS weekly",
            "Publish a trust-and-safety policy page and support response standard",
        ],
        sources=[
            "https://data.worldbank.org",
            "https://restcountries.com",
            "https://www.upwork.com",
            "https://www.fiverr.com",
        ],
        quality_assessment={
            "overall": 82,
            "section_scores": {
                "market_research": 80,
                "competitor_analysis": 81,
                "differentiation": 84,
                "feasibility_report": 83,
                "unit_economics": 79,
                "roadmap": 86,
                "growth_experiments": 82,
                "risk_register": 81,
            },
            "issues": [
                "Fallback mode uses synthetic assumptions; validate with user interviews.",
            ],
        },
    )

    return report
