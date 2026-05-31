import json
import os
import re
from typing import Iterable

from app.schemas import StartupIdeaRequest, StartupReportResponse
from app.services.llm_provider import LLMProviderError, call_provider
from app.services.mock_agents import generate_startup_report


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


def _build_prompt(payload: StartupIdeaRequest) -> str:
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
        "feasibility_report": "string",
        "roadmap": ["string", "string", "string", "string"],
        "funding_opportunities": ["string", "string", "string", "string"],
        "launch_checklist": ["string", "string", "string", "string", "string"],
    }

    return (
        "Generate a startup analysis package as strict JSON only. "
        "Do not include explanations, markdown, or code fences.\n\n"
        f"Founder input:\n{payload.model_dump_json(indent=2)}\n\n"
        "Output schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Constraints:\n"
        "- Keep each section concise and practical for MVP founders.\n"
        "- Ensure readiness values are realistic and internally consistent.\n"
        "- If startup_name is empty, use 'Untitled Startup'.\n"
    )


def _try_providers(payload: StartupIdeaRequest, providers: Iterable[str]) -> StartupReportResponse:
    prompt = _build_prompt(payload)
    last_error = "Unknown provider error"

    for provider in providers:
        try:
            raw = call_provider(provider, prompt)
            parsed = json.loads(_extract_json_block(raw))
            return StartupReportResponse.model_validate(parsed)
        except (LLMProviderError, ValueError, json.JSONDecodeError) as err:
            last_error = f"{provider}: {err}"
            continue

    raise RuntimeError(last_error)


def generate_startup_report_with_fallback(payload: StartupIdeaRequest) -> StartupReportResponse:
    try:
        return _try_providers(payload, _provider_order())
    except RuntimeError:
        return generate_startup_report(payload)
