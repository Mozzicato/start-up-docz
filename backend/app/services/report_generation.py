import json
import os
import re
from typing import Iterable

from app.schemas import QualityAssessment, StartupIdeaRequest, StartupReportResponse
from app.services.llm_provider import LLMProviderError, call_provider
from app.services.mock_agents import generate_startup_report
from app.services.research_context import build_research_context
from app.services.startup_playbooks import country_playbook


def _provider_order() -> list[str]:
    order = os.getenv("STARTUPDOCS_PROVIDER_ORDER", "openrouter,groq,gemini,mistral")
    return [name.strip() for name in order.split(",") if name.strip()]


def _extract_json_block(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return text[start : end + 1]


def _normalized_payload(payload: StartupIdeaRequest) -> StartupIdeaRequest:
    data = payload.model_dump()
    model = (data.get("business_model") or "").strip().lower()
    unknown_models = {"i dont know", "i don't know", "unknown", "n/a", "na", "none"}

    if model in unknown_models:
        idea = (data.get("idea") or "").lower()
        if "marketplace" in idea or "connect" in idea or "student" in idea:
            data["business_model"] = "Transaction-fee marketplace"
        elif "subscription" in idea or "saas" in idea:
            data["business_model"] = "SaaS subscription"
        else:
            data["business_model"] = "Hybrid: transaction fee + premium plans"

    return StartupIdeaRequest.model_validate(data)


def _build_prompt(payload: StartupIdeaRequest, research_context: dict, playbook: dict) -> str:
    mode_guidance = {
        "mvp": "Prioritize speed-to-learning, small-team execution, and early retention proof.",
        "vc": "Prioritize venture-scale narrative, expansion strategy, and durable network effects.",
        "grant": "Prioritize measurable social impact, inclusion outcomes, and accountability metrics.",
    }

    schema = {
        "startup_name": "string",
        "summary": "string",
        "readiness": {
            "overall": "integer 0-100",
            "market_demand": "number 1-10",
            "technical_feasibility": "number 1-10",
            "competition": "number 1-10",
            "funding_potential": "number 1-10",
            "execution_complexity": "number 1-10",
            "go_to_market_readiness": "number 1-10",
        },
        "market_research": "string",
        "competitor_analysis": "string",
        "differentiation": "string",
        "product_build_plan": "string",
        "feasibility_report": "string",
        "unit_economics": "string",
        "cac_model": "string",
        "team_and_execution_strategy": "string",
        "build_vs_buy": "string",
        "roadmap": ["string", "string", "string", "string", "string", "string"],
        "mvp_cost_breakdown": ["string", "string", "string", "string", "string"],
        "tooling_stack": ["string", "string", "string", "string", "string"],
        "incorporation_playbook": ["string", "string", "string", "string", "string"],
        "legal_requirements": ["string", "string", "string", "string", "string"],
        "growth_experiments": ["string", "string", "string", "string", "string"],
        "risk_register": ["string", "string", "string", "string", "string"],
        "funding_opportunities": ["string", "string", "string", "string", "string"],
        "launch_checklist": ["string", "string", "string", "string", "string", "string"],
        "sources": ["string", "string", "string"],
        "quality_assessment": {
            "overall": "integer 0-100",
            "section_scores": {"market_research": "integer 0-100"},
            "issues": ["string"],
        },
    }

    return (
        "Generate a founder-grade startup analysis package as strict JSON only. "
        "Do not include explanations, markdown, or code fences.\n\n"
        f"Founder mode: {payload.founder_mode}\n"
        f"Mode guidance: {mode_guidance.get(payload.founder_mode, mode_guidance['mvp'])}\n\n"
        f"Founder input:\n{payload.model_dump_json(indent=2)}\n\n"
        f"Research context (use as evidence):\n{json.dumps(research_context, indent=2)}\n\n"
        "Verified local playbook (REAL fees, vendor prices, and funding programmes for this country — "
        "reuse these exact numbers/names and expand on them; do not water them down to generic advice):\n"
        f"{json.dumps(playbook, indent=2)}\n\n"
        "Output schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Constraints — write like a senior analyst who already did days of primary research:\n"
        "- Be specific and quantified. Every cost must carry a real number or tight range with its "
        "currency; every tool/vendor/grant must be named; vague phrasing ('affordable', 'some fees') is a "
        "failure.\n"
        "- market_research must include demand drivers, TAM/SAM/SOM assumptions WITH numbers, and a "
        "go-to-market implication.\n"
        "- competitor_analysis must name 3+ concrete competitors, note their pricing/positioning, and "
        "explain your wedge.\n"
        "- differentiation must explain defensibility and why incumbents will struggle to copy quickly.\n"
        "- product_build_plan must explain architecture, feature slices, and the implementation approach.\n"
        "- build_vs_buy must compare (1) vibe-coding it yourself with named AI tools and their monthly "
        "prices, (2) hiring a developer/freelancer with real local salary or hourly rates, and (3) an "
        "agency build with a real price range — then give a clear recommendation.\n"
        "- incorporation_playbook must be an ordered, do-this-then-that list of the EXACT registration "
        "steps for the stated country, each with the responsible body, the real fee, and a rough timeline "
        "(for Nigeria: CAC name reservation/registration, TIN, NDPC, SCUML if handling money, etc.).\n"
        "- tooling_stack must name real services (hosting, database, payments, email, AI, monitoring) with "
        "their real prices or free tiers.\n"
        "- mvp_cost_breakdown must be line items with real cost ranges that tie back to the tooling and "
        "build choices above.\n"
        "- legal_requirements must list concrete, country-specific legal/compliance obligations.\n"
        "- funding_opportunities must NAME real programmes/funds/accelerators with their check sizes and "
        "(where known) application cadence — not abstract categories.\n"
        "- unit_economics needs a revenue equation and margin drivers; cac_model needs a formula, channel "
        "assumptions, and a payback target; growth_experiments need a success metric each; risk_register "
        "needs owner-level mitigations; launch_checklist must be execution-ready and testable; roadmap "
        "must be milestone-based with measurable outputs.\n"
        "- Use inline citations like [1], [2] in narrative sections when possible.\n"
        "- Populate sources with 3-8 concrete links used as evidence.\n"
        "- Ensure readiness values are realistic and internally consistent.\n"
        "- If startup_name is empty, use 'Untitled Startup'.\n"
    )


def _score_narrative(text: str, min_words: int = 65) -> int:
    words = re.findall(r"\b\w+\b", text or "")
    word_count = len(words)
    score = min(100, int((word_count / max(min_words, 1)) * 70) + 20)
    if "[" in text and "]" in text:
        score += 8
    if any(token in (text or "").lower() for token in ["tam", "sam", "som", "mitigation", "assumption"]):
        score += 7
    return max(0, min(score, 100))


def _score_list(items: list[str], min_items: int, min_avg_words: int = 6) -> int:
    if not items:
        return 0
    avg_words = sum(len(re.findall(r"\b\w+\b", item)) for item in items) / len(items)
    length_score = min(100, int((len(items) / max(min_items, 1)) * 70) + 20)
    detail_bonus = min(10, int((avg_words / max(min_avg_words, 1)) * 10))
    return max(0, min(length_score + detail_bonus, 100))


def _assess_quality(report: StartupReportResponse) -> QualityAssessment:
    scores = {
        "market_research": _score_narrative(report.market_research),
        "competitor_analysis": _score_narrative(report.competitor_analysis),
        "differentiation": _score_narrative(report.differentiation, min_words=45),
        "product_build_plan": _score_narrative(report.product_build_plan, min_words=70),
        "feasibility_report": _score_narrative(report.feasibility_report, min_words=50),
        "unit_economics": _score_narrative(report.unit_economics, min_words=45),
        "cac_model": _score_narrative(report.cac_model, min_words=40),
        "team_and_execution_strategy": _score_narrative(report.team_and_execution_strategy, min_words=40),
        "build_vs_buy": _score_narrative(report.build_vs_buy, min_words=70),
        "roadmap": _score_list(report.roadmap, min_items=6),
        "mvp_cost_breakdown": _score_list(report.mvp_cost_breakdown, min_items=5),
        "tooling_stack": _score_list(report.tooling_stack, min_items=5),
        "incorporation_playbook": _score_list(report.incorporation_playbook, min_items=4),
        "legal_requirements": _score_list(report.legal_requirements, min_items=5),
        "growth_experiments": _score_list(report.growth_experiments, min_items=5),
        "risk_register": _score_list(report.risk_register, min_items=5),
        "funding_opportunities": _score_list(report.funding_opportunities, min_items=5),
        "launch_checklist": _score_list(report.launch_checklist, min_items=6),
        "sources": _score_list(report.sources, min_items=4, min_avg_words=1),
    }

    issues: list[str] = []
    for section, score in scores.items():
        if score < int(os.getenv("STARTUPDOCS_SECTION_SCORE_TARGET", "72")):
            issues.append(f"{section} needs more specificity, evidence, or detail")

    overall = int(sum(scores.values()) / len(scores)) if scores else 0
    return QualityAssessment(overall=overall, section_scores=scores, issues=issues)


def _build_revision_prompt(
    payload: StartupIdeaRequest,
    research_context: dict,
    playbook: dict,
    prior_report: StartupReportResponse,
) -> str:
    quality = prior_report.quality_assessment
    return (
        "Revise the startup package as strict JSON only. Keep schema exactly the same.\n\n"
        f"Founder mode: {payload.founder_mode}\n"
        f"Founder input:\n{payload.model_dump_json(indent=2)}\n\n"
        f"Research context:\n{json.dumps(research_context, indent=2)}\n\n"
        "Verified local playbook (reuse these real fees, vendor prices, and named funding programmes):\n"
        f"{json.dumps(playbook, indent=2)}\n\n"
        f"Current draft JSON:\n{prior_report.model_dump_json(indent=2)}\n\n"
        f"Quality issues to fix:\n{json.dumps(quality.issues, indent=2)}\n\n"
        "Requirements:\n"
        "- Replace any generic line with a specific one: real numbers/currency, named vendors, named "
        "competitors, named funding programmes with check sizes.\n"
        "- Improve weak sections with concrete assumptions, metrics, and citations.\n"
        "- Preserve strong sections but improve coherence across the document.\n"
    )


def _ensure_quality(
    report: StartupReportResponse,
    payload: StartupIdeaRequest,
    research_context: dict,
    playbook: dict,
) -> StartupReportResponse:
    if len(report.roadmap) < 6:
        report.roadmap = [
            "Week 1-2: Run 25 customer interviews and validate the top 3 pain points",
            "Week 3-4: Build and test the first transaction flow with escrow and payout",
            "Week 5-6: Launch a closed beta with at least 50 students in one campus",
            "Week 7-8: Improve activation funnel and reduce failed transactions below 2%",
            "Week 9-10: Expand to 2 additional campuses and onboard campus ambassadors",
            "Week 11-12: Prepare investor update with retention, GMV, and unit-economics snapshot",
        ]

    # Prefer the verified country playbook (real fees, vendors, named programmes) whenever the
    # model left these thin or generic.
    if len(report.funding_opportunities) < 5:
        report.funding_opportunities = playbook["funding_opportunities"]

    if len(report.mvp_cost_breakdown) < 5:
        report.mvp_cost_breakdown = playbook["mvp_cost_breakdown"]

    if len(report.tooling_stack) < 5:
        report.tooling_stack = playbook["tooling_stack"]

    if len(report.incorporation_playbook) < 4:
        report.incorporation_playbook = playbook["incorporation_playbook"]

    if len(report.legal_requirements) < 5:
        report.legal_requirements = playbook["legal_requirements"]

    if not report.build_vs_buy.strip():
        report.build_vs_buy = playbook["build_vs_buy"]

    if len(report.growth_experiments) < 5:
        report.growth_experiments = [
            "Test ambassador referral loop and target >20% referred signup share",
            "Test two pricing structures and keep the one with higher contribution margin",
            "Test trust badge and aim for >25% lower dispute rate",
            "Test onboarding flow and improve first-job completion rate above 60%",
            "Test reactivation messaging and lift week-4 retention by at least 10 points",
        ]

    if len(report.risk_register) < 5:
        report.risk_register = [
            "Fraud risk; mitigation: stronger verification and payout guardrails",
            "Liquidity risk; mitigation: focused launch in one campus with seeded supply",
            "Payment reliability risk; mitigation: fallback payout rails and alerting",
            "Compliance risk; mitigation: legal review and regulated payment partners",
            "Reputation risk; mitigation: strict dispute SLA and transparent policy",
        ]

    if len(report.launch_checklist) < 6:
        report.launch_checklist = [
            "Define one sharp ICP and one urgent job-to-be-done",
            "Ship escrow and payout reliability alerts before paid acquisition",
            "Recruit first 20 supply-side users with manual onboarding",
            "Track activation, repeat booking, and dispute resolution time weekly",
            "Run two pricing experiments on take-rate and instant-payout fee",
            "Prepare legal and trust policy pages for student and parent confidence",
        ]

    if not report.sources:
        source_urls: list[str] = []
        for source in research_context.get("sources", []):
            if not isinstance(source, dict):
                continue
            url = source.get("url")
            if isinstance(url, str) and url not in source_urls:
                source_urls.append(url)
        report.sources = source_urls[:8]

    if "[" not in report.market_research and report.sources:
        report.market_research = f"{report.market_research}\n\nEvidence links: [1] {report.sources[0]}"

    if not report.differentiation.strip():
        report.differentiation = (
            "Defensibility comes from trust data, dispute-resolution quality, and campus-level liquidity loops. "
            "As these improve, the marketplace becomes faster and safer than generic alternatives."
        )

    if not report.unit_economics.strip():
        report.unit_economics = (
            "Revenue = completed jobs x average order value x take-rate, plus instant payout fees. "
            "Primary margin levers are failed-payment rate, support burden, and repeat booking share."
        )

    if not report.product_build_plan.strip():
        report.product_build_plan = (
            "Build MVP in four slices: onboarding + trust, posting/matching, payment hold/release, and disputes. "
            "Use a thin backend service layer first, keep operations semi-manual, and automate only repeated workflows."
        )

    if not report.cac_model.strip():
        report.cac_model = (
            "CAC = (paid acquisition + ambassador incentives + onboarding ops) / activated users by channel. "
            "Track CAC by campus and target payback in under 8 weeks."
        )

    if not report.team_and_execution_strategy.strip():
        report.team_and_execution_strategy = (
            "Founder-led build is faster for iteration in first 6 weeks; hiring improves reliability once payment "
            "volume grows. Use a hybrid path with one technical founder plus fractional specialists."
        )

    if not report.summary.strip():
        report.summary = (
            f"{report.startup_name} addresses a measurable gap for {payload.target_audience} in "
            f"{payload.country} with a {payload.business_model} model and near-term MVP path."
        )

    report.quality_assessment = _assess_quality(report)

    return report


def _try_providers(payload: StartupIdeaRequest, providers: Iterable[str]) -> StartupReportResponse:
    normalized_payload = _normalized_payload(payload)
    research_context = build_research_context(normalized_payload)
    playbook = country_playbook(normalized_payload)
    prompt = _build_prompt(normalized_payload, research_context, playbook)
    last_error = "Unknown provider error"
    score_target = int(os.getenv("STARTUPDOCS_QUALITY_SCORE_TARGET", "78"))
    best_report: StartupReportResponse | None = None

    for provider in providers:
        try:
            raw = call_provider(provider, prompt)
            parsed = json.loads(_extract_json_block(raw))
            report = StartupReportResponse.model_validate(parsed)
            report = _ensure_quality(report, normalized_payload, research_context, playbook)

            if report.quality_assessment.overall >= score_target and not report.quality_assessment.issues:
                return report

            revision_prompt = _build_revision_prompt(
                normalized_payload, research_context, playbook, report
            )
            revised_raw = call_provider(provider, revision_prompt)
            revised_parsed = json.loads(_extract_json_block(revised_raw))
            revised_report = StartupReportResponse.model_validate(revised_parsed)
            revised_report = _ensure_quality(
                revised_report, normalized_payload, research_context, playbook
            )

            better = revised_report
            if report.quality_assessment.overall > revised_report.quality_assessment.overall:
                better = report

            if better.quality_assessment.overall >= score_target:
                return better

            if not best_report or better.quality_assessment.overall > best_report.quality_assessment.overall:
                best_report = better
        except (LLMProviderError, ValueError, json.JSONDecodeError) as err:
            last_error = f"{provider}: {err}"
            continue

    if best_report:
        return best_report

    raise RuntimeError(last_error)


def generate_startup_report_with_fallback(payload: StartupIdeaRequest) -> StartupReportResponse:
    # Never surface a 500 to the founder: any failure in the live LLM path (provider error,
    # malformed JSON, network/research-context hiccup, etc.) degrades to the deterministic
    # mock document, which is itself enriched with the verified country playbook.
    try:
        return _try_providers(payload, _provider_order())
    except Exception as err:  # noqa: BLE001 - intentional broad fallback for resilience
        import logging

        logging.getLogger("startupdocs").warning(
            "LLM report path failed (%s); using mock fallback.", err
        )
        return generate_startup_report(payload)
