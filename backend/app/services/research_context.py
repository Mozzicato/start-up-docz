import re
import urllib.parse

import httpx

from app.schemas import StartupIdeaRequest


_STOPWORDS = {
    "about",
    "after",
    "also",
    "around",
    "based",
    "build",
    "could",
    "daily",
    "demand",
    "enable",
    "faster",
    "first",
    "founder",
    "from",
    "have",
    "into",
    "market",
    "money",
    "needs",
    "platform",
    "startup",
    "student",
    "students",
    "their",
    "through",
    "users",
    "using",
    "with",
}


def _safe_get_json(
    client: httpx.Client, url: str, params: dict[str, str] | None = None
) -> dict | list | None:
    try:
        response = client.get(url, params=params)
        if response.status_code >= 400:
            return None
        return response.json()
    except (httpx.HTTPError, ValueError):
        return None


def _keyword_slice(text: str, limit: int = 6) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text.lower())
    picked: list[str] = []
    for word in words:
        if word in _STOPWORDS:
            continue
        if word not in picked:
            picked.append(word)
        if len(picked) >= limit:
            break
    return picked


def _country_context(client: httpx.Client, country_name: str) -> dict:
    payload = {
        "country": country_name,
        "country_code": None,
        "population": None,
        "gdp_current_usd": None,
        "gdp_year": None,
        "internet_penetration_percent": None,
        "internet_year": None,
    }

    country_data = _safe_get_json(
        client,
        f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country_name)}",
        params={"fields": "cca2,name,population"},
    )

    if isinstance(country_data, list) and country_data:
        top = country_data[0]
        payload["country"] = (
            top.get("name", {}).get("common") if isinstance(top.get("name"), dict) else country_name
        ) or country_name
        payload["country_code"] = top.get("cca2")
        payload["population"] = top.get("population")

    code = payload.get("country_code")
    if not isinstance(code, str) or len(code) != 2:
        return payload

    for indicator, value_key, year_key in [
        ("NY.GDP.MKTP.CD", "gdp_current_usd", "gdp_year"),
        ("IT.NET.USER.ZS", "internet_penetration_percent", "internet_year"),
    ]:
        wb_data = _safe_get_json(
            client,
            f"https://api.worldbank.org/v2/country/{code.lower()}/indicator/{indicator}",
            params={"format": "json", "per_page": "30"},
        )

        if not isinstance(wb_data, list) or len(wb_data) < 2 or not isinstance(wb_data[1], list):
            continue

        for row in wb_data[1]:
            if not isinstance(row, dict):
                continue
            value = row.get("value")
            if value is not None:
                payload[value_key] = value
                payload[year_key] = row.get("date")
                break

    return payload


def _wikipedia_briefs(client: httpx.Client, query: str, limit: int = 4) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen_titles: set[str] = set()

    search = _safe_get_json(
        client,
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "utf8": "1",
            "format": "json",
        },
    )

    if not isinstance(search, dict):
        return results

    items = search.get("query", {}).get("search", [])
    if not isinstance(items, list):
        return results

    for item in items:
        title = item.get("title") if isinstance(item, dict) else None
        if not isinstance(title, str) or title in seen_titles:
            continue

        seen_titles.add(title)
        page = _safe_get_json(
            client,
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}",
        )
        if not isinstance(page, dict):
            continue

        extract = page.get("extract")
        url = page.get("content_urls", {}).get("desktop", {}).get("page")
        if not isinstance(extract, str) or not extract.strip():
            continue

        results.append(
            {
                "title": title,
                "extract": extract.strip(),
                "url": url if isinstance(url, str) else f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}",
            }
        )

    return results


def _competitor_hints(industry: str, idea: str, country: str) -> list[dict[str, str]]:
    text = f"{industry} {idea}".lower()
    hints: list[dict[str, str]] = []

    if "gig" in text or "freelance" in text or "job" in text:
        hints.extend(
            [
                {
                    "name": "Upwork",
                    "positioning": "Global freelance marketplace with strong trust and payment rails",
                    "url": "https://www.upwork.com",
                },
                {
                    "name": "Fiverr",
                    "positioning": "Productized micro-services marketplace with fixed-price task catalogs",
                    "url": "https://www.fiverr.com",
                },
                {
                    "name": "TaskRabbit",
                    "positioning": "On-demand local task marketplace focused on rapid fulfillment",
                    "url": "https://www.taskrabbit.com",
                },
            ]
        )

    if "fintech" in text or "payment" in text or "escrow" in text:
        hints.extend(
            [
                {
                    "name": "Paystack",
                    "positioning": "Nigeria-focused payment rails and merchant tools",
                    "url": "https://paystack.com",
                },
                {
                    "name": "Flutterwave",
                    "positioning": "Pan-African payment infrastructure for collections and disbursements",
                    "url": "https://flutterwave.com",
                },
                {
                    "name": "OPay",
                    "positioning": "Consumer payments app with dense local transaction usage",
                    "url": "https://www.opayweb.com",
                },
            ]
        )

    if not hints:
        hints.append(
            {
                "name": f"Top local incumbents in {country}",
                "positioning": "Use local app-store rankings and LinkedIn signals to shortlist direct alternatives",
                "url": "https://www.linkedin.com",
            }
        )

    # Keep list concise and unique by name.
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for hint in hints:
        key = hint["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(hint)
        if len(unique) >= 5:
            break

    return unique


def _localized_sources(country: str) -> list[dict[str, str]]:
    c = country.strip().lower()
    if c in {"nigeria", "ng", "federal republic of nigeria"}:
        return [
            {
                "title": "National Bureau of Statistics (Nigeria)",
                "url": "https://nigerianstat.gov.ng",
                "note": "Official socioeconomic indicators",
            },
            {
                "title": "Central Bank of Nigeria",
                "url": "https://www.cbn.gov.ng",
                "note": "Payments, monetary and financial-system indicators",
            },
            {
                "title": "NITDA",
                "url": "https://nitda.gov.ng",
                "note": "Digital economy and technology policy updates",
            },
            {
                "title": "Nigerian Communications Commission",
                "url": "https://www.ncc.gov.ng",
                "note": "Connectivity and telecom market data",
            },
        ]
    return []


def build_research_context(payload: StartupIdeaRequest) -> dict:
    keyword_query = " ".join(_keyword_slice(payload.idea, limit=5))
    queries = [
        f"{payload.industry} {payload.country} market",
        f"{payload.target_audience} {payload.country}",
    ]
    if keyword_query:
        queries.append(f"{payload.country} {keyword_query}")

    context = {
        "country_profile": {},
        "market_signals": [],
        "competitor_hints": _competitor_hints(payload.industry, payload.idea, payload.country),
        "sources": [
            {
                "title": "World Bank Open Data",
                "url": "https://data.worldbank.org",
                "note": "Country macro and digital-adoption indicators",
            },
            {
                "title": "Rest Countries",
                "url": "https://restcountries.com",
                "note": "Country metadata",
            },
            *_localized_sources(payload.country),
        ],
    }

    try:
        with httpx.Client(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": "StartupDocs/1.0 (research context generator)"},
        ) as client:
            context["country_profile"] = _country_context(client, payload.country)

            for query in queries:
                briefs = _wikipedia_briefs(client, query, limit=3)
                for brief in briefs:
                    if len(context["market_signals"]) >= 7:
                        break
                    context["market_signals"].append(brief)
                    context["sources"].append(
                        {
                            "title": brief["title"],
                            "url": brief["url"],
                            "note": "Wikipedia summary used for market context",
                        }
                    )
                if len(context["market_signals"]) >= 7:
                    break
    except httpx.HTTPError:
        # Keep deterministic competitor hints and base sources even if network fails.
        pass

    return context