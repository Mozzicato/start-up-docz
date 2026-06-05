"""Country- and industry-aware "playbook" data: the concrete, hard-to-Google facts a
founder would otherwise spend days assembling — registration steps with real fees,
named tools with real prices, build-vs-hire economics, and live funding programmes.

Figures are realistic ranges as of early 2026 and are meant as planning anchors, not
legal/financial advice. Each playbook carries a `verify_note` reminding founders to
confirm current numbers with the primary source before they spend money.
"""

from __future__ import annotations

from app.schemas import StartupIdeaRequest

_VERIFY = (
    "Figures are planning estimates (early 2026). Confirm current fees on the official "
    "portal before paying — government and vendor pricing changes often."
)


def _is_nigeria(country: str) -> bool:
    return country.strip().lower() in {
        "nigeria",
        "ng",
        "federal republic of nigeria",
        "naija",
    }


def _industry_flags(payload: StartupIdeaRequest) -> dict[str, bool]:
    text = f"{payload.industry} {payload.idea} {payload.business_model}".lower()
    handles_money = any(
        token in text
        for token in ("fintech", "payment", "escrow", "wallet", "marketplace", "transaction", "lending", "remit")
    )
    is_ai = any(token in text for token in ("ai", "ml", "llm", "gpt", "agent", "model"))
    is_mobile = any(token in text for token in ("mobile", "app", "ios", "android"))
    return {"handles_money": handles_money, "is_ai": is_ai, "is_mobile": is_mobile}


# ---------------------------------------------------------------------------
# Nigeria playbook
# ---------------------------------------------------------------------------


def _nigeria_incorporation(flags: dict[str, bool]) -> list[str]:
    steps = [
        "Reserve your company name on the CAC Company Registration Portal (pre.cac.gov.ng) — "
        "fee ₦500, approved in ~1–2 working days. Have two name options ready.",
        "Register a Private Company Limited by Shares (LTD) yourself on the CAC portal: government "
        "filing is ~₦10,000 for share capital up to ₦1m, plus 0.75% stamp duty on share capital "
        "(₦7,500 on a ₦1m capital). DIY total lands around ₦20,000–₦35,000; an accredited agent or "
        "lawyer adds ₦30,000–₦150,000 but handles documents and CAC follow-up for you.",
        "Collect your Certificate of Incorporation, RC number, and the system-generated TIN "
        "(Tax Identification Number is now issued automatically at incorporation via FIRS/JTB — no "
        "separate fee).",
        "Register for VAT with FIRS (free) and file monthly even at ₦0; open a corporate bank "
        "account with the certificate, TIN, board resolution, and directors' IDs/BVN.",
        "Register as a data controller with the Nigeria Data Protection Commission (NDPC) under the "
        "NDPA 2023 — small startups file in the lower tier (roughly ₦10,000–₦100,000/yr depending on "
        "data volume) and must publish a privacy policy.",
    ]
    if flags["handles_money"]:
        steps.append(
            "Because you touch customer funds, obtain SCUML registration (free, via the EFCC SCUML "
            "portal) — banks ask for it before activating a business account that handles third-party "
            "money. Avoid needing a CBN payment licence (PSSP/PSP capital requirements run ₦100m–₦5bn) "
            "by settling through a licensed processor like Paystack or Flutterwave instead of holding "
            "funds yourself."
        )
    steps.append(
        "Optional but recommended: file a trademark on your name/logo via an accredited IP agent at the "
        "Trademarks Registry (~₦60,000–₦90,000 all-in, 6–18 months to certificate) to protect the brand."
    )
    return steps


def _nigeria_tooling(flags: dict[str, bool]) -> list[str]:
    stack = [
        "Domain: .com.ng ≈ ₦2,500/yr (Whogohost, QServers) or .com ≈ $10–13/yr (Namecheap, Porkbun).",
        "Frontend hosting: Vercel Hobby (free) for the MVP, Vercel Pro $20/mo once you need teams/analytics.",
        "Backend + database: Render Starter $7/mo or Railway ~$5–20/mo for the API; Supabase (Postgres + "
        "Auth + storage) free tier, then Pro $25/mo; Neon Postgres has a usable free tier too.",
        "Email: Resend (3k emails/mo free, then $20/mo) or Brevo (300/day free) for transactional mail.",
    ]
    stack.append(
        "Payments: Paystack charges 1.5% + ₦100 local (the ₦100 is waived under ₦2,500 and the fee is "
        "capped at ₦2,000), ~3.9% on international cards; Flutterwave is ~1.4% local. No monthly fee — "
        "you only pay per successful transaction."
    )
    if flags["is_mobile"] or flags["handles_money"]:
        stack.append(
            "OTP/SMS verification: Termii ≈ ₦2.40–₦3.50 per SMS, or use WhatsApp/email OTP to cut cost early."
        )
    if flags["is_ai"]:
        stack.append(
            "AI inference: start on free/cheap tiers — Gemini 1.5 Flash (generous free tier), OpenAI "
            "gpt-4o-mini (~$0.15 per 1M input tokens), or Claude Haiku — and only move to a frontier model "
            "for the few calls that truly need it. Budget $20–150/mo at MVP traffic."
        )
    stack.extend(
        [
            "Design: Figma (free) for UI, Canva Pro (~$13/mo) for marketing assets.",
            "Error monitoring + analytics: Sentry (free dev tier, $26/mo team) and PostHog (free up to 1M "
            "events/mo) so you can debug and measure activation without enterprise tooling.",
        ]
    )
    return stack


def _generic_incorporation(country: str, flags: dict[str, bool]) -> list[str]:
    steps = [
        f"Choose a legal structure and register with the company registrar in {country} (in most "
        "markets a private limited company; in the US a Delaware C-Corp via Stripe Atlas at $500 + state "
        "fees is the venture-default). Budget $50–$800 in government and filing fees depending on country.",
        "Obtain your company number/certificate and a tax identification number from the national tax "
        "authority, then register for sales tax/VAT/GST if your model requires it.",
        "Open a business bank account (or use Mercury/Brex/Wise Business for online-first banking) with the "
        "incorporation certificate, tax ID, and director identification.",
        "Publish a privacy policy and register/comply with the local data-protection regime (GDPR in the "
        "EU/UK, CCPA in California, or the national equivalent) before collecting personal data.",
    ]
    if flags["handles_money"]:
        steps.append(
            "Because you handle customer funds, route money through a licensed processor (Stripe, Adyen, "
            "or a local PSP) rather than holding balances yourself, and check whether money-transmitter / "
            "e-money licensing applies in your jurisdiction."
        )
    steps.append(
        "Optional: file a trademark on your brand with the national IP office (e.g. USPTO ~$250–$350 per "
        "class) to protect the name once you have early traction."
    )
    return steps


def _generic_tooling(flags: dict[str, bool]) -> list[str]:
    stack = [
        "Domain: ~$10–13/yr (Namecheap, Cloudflare Registrar, Porkbun).",
        "Frontend hosting: Vercel or Netlify (free Hobby tier, ~$20/mo Pro).",
        "Backend + database: Render ($7/mo), Railway ($5–20/mo), or Fly.io; Supabase or Neon Postgres "
        "(free tier, then ~$25/mo).",
        "Email: Resend (free 3k/mo, $20/mo) or Postmark for transactional mail.",
        "Payments: Stripe at 2.9% + $0.30 per card charge (no monthly fee) is the default for online "
        "businesses; use a local PSP where Stripe isn't supported.",
    ]
    if flags["is_ai"]:
        stack.append(
            "AI inference: begin on cheap tiers — Gemini Flash, OpenAI gpt-4o-mini (~$0.15/1M input tokens), "
            "or Claude Haiku — and reserve frontier models for calls that need them. Budget $20–150/mo early."
        )
    stack.extend(
        [
            "Design: Figma (free) plus Canva Pro (~$13/mo).",
            "Monitoring + analytics: Sentry (free dev tier) and PostHog (free to 1M events/mo).",
        ]
    )
    return stack


def _build_vs_buy(payload: StartupIdeaRequest, flags: dict[str, bool]) -> str:
    nigeria = _is_nigeria(payload.country)
    if nigeria:
        dev_line = (
            "Hiring in Nigeria: a junior engineer runs ₦150k–₦350k/month, mid-level ₦400k–₦900k/month, and "
            "senior ₦1m–₦2.5m/month; a local dev shop will quote ₦3m–₦15m ($2k–$10k) for a full MVP. "
            "Freelancers on Upwork bill ~$15–$40/hr locally."
        )
        verdict = (
            "Recommended path for a lean Nigerian MVP: vibe-code the first version yourself, then hire one "
            "mid-level engineer (≈₦600k/month) once payment volume justifies reliability work. Keep "
            "legal/compliance fractional, not full-time, until after launch."
        )
    else:
        dev_line = (
            "Hiring: a freelance full-stack engineer bills ~$25–$80/hr (offshore) or $80–$150/hr "
            "(US/EU); a salaried mid-level engineer is ~$60k–$120k/yr; an agency MVP build typically runs "
            "$15k–$60k."
        )
        verdict = (
            "Recommended path for a lean MVP: vibe-code and ship the first version yourself to validate "
            "demand, then hire one experienced engineer once you have real usage and the cost of bugs rises."
        )
    return (
        "Three ways to build the MVP, cheapest to most expensive in cash:\n\n"
        "1) Vibe-code it yourself (founder + AI tools). Tooling is ~$40–$80/month — Cursor Pro ($20/mo), "
        "v0 or Lovable ($20–25/mo), GitHub Copilot ($10/mo) — and you can reach a working prototype in "
        "6–10 weeks with near-zero labour cash. Trade-off: it costs your time and accrues technical debt, "
        "so plan a refactor before you scale.\n\n"
        "2) Hire a developer or freelancer. " + dev_line + " You get reliability and speed but burn "
        "real cash monthly, so only commit once the idea is validated.\n\n"
        "3) Use an agency / dev shop for a fixed-scope build. Fastest to a polished product, but the most "
        "expensive and you don't retain the in-house knowledge.\n\n" + verdict
    )


def _nigeria_mvp_costs(flags: dict[str, bool]) -> list[str]:
    return [
        "Company registration + compliance setup (CAC LTD, NDPC, privacy policy): ₦60,000–₦200,000 "
        "one-off (≈$40–$130), lower if you do CAC yourself.",
        "Build the MVP: ~$0–$120/mo in tools if you vibe-code it yourself, vs ₦3m–₦15m ($2k–$10k) for an "
        "agency, vs ~₦600k/mo to hire one mid-level engineer.",
        "Infrastructure + SaaS (hosting, database, email, monitoring): $25–$120/mo combined while small.",
        "Payments: no upfront cost — Paystack/Flutterwave take ~1.5% per transaction; budget against GMV, "
        "not as a fixed line.",
        "Launch + pilot acquisition (campus ambassadors, content, small paid tests): ₦200,000–₦1,500,000 "
        "($150–$1,000) for the first cohort.",
        "Buffer (15–20%) for re-builds, support, and the surprises every first launch hits.",
    ]


def _generic_mvp_costs(flags: dict[str, bool]) -> list[str]:
    return [
        "Company registration + compliance setup: $50–$800 one-off depending on jurisdiction (Stripe Atlas "
        "Delaware C-Corp is $500 + state fees).",
        "Build the MVP: ~$40–$120/mo in tools if you vibe-code it yourself, vs $15k–$60k for an agency, vs "
        "~$6k–$10k/mo to hire one experienced engineer.",
        "Infrastructure + SaaS (hosting, database, email, monitoring): $25–$150/mo combined while small.",
        "Payments: no upfront cost — Stripe/local PSP take ~2.9% + $0.30 per charge; budget against revenue.",
        "Launch + early acquisition (content, community, small paid tests): $300–$3,000 for the first cohort.",
        "Buffer (15–20%) for re-builds, support, and first-launch surprises.",
    ]


# ---------------------------------------------------------------------------
# Funding programmes (named, with real check sizes / cadence)
# ---------------------------------------------------------------------------


def _nigeria_funding(founder_mode: str) -> list[str]:
    grant = [
        "Tony Elumelu Foundation Entrepreneurship Programme: $5,000 non-dilutive seed + 12 weeks training + "
        "mentorship; applications open annually (~January) at tefconnect.com.",
        "Google for Startups Black Founders Fund (Africa): up to $150,000 non-dilutive cash + ~$200,000 in "
        "cloud credits; annual cohort.",
        "GIZ Make-IT in Africa / AfDB youth & innovation challenge funds: grants and acceleration for "
        "impact-aligned ventures.",
        "Bank of Industry (BOI) and CBN youth/SME intervention loans: low-interest facilities for "
        "registered Nigerian businesses.",
        "FG digital programmes (3MTT, NITDA) and Nigeria Startup Act labelling, which unlocks tax and "
        "regulatory incentives once you're a registered, labelled startup.",
    ]
    vc = [
        "Microtraction: ~$25,000 pre-seed (rolling applications) — a strong first institutional cheque for "
        "Nigerian founders.",
        "Ventures Platform: pre-seed/seed cheques typically $100k–$500k into African startups.",
        "Future Africa, LoftyInc, Voltron Capital, GreenHouse Capital: active early-stage funds and "
        "syndicates writing $50k–$500k.",
        "Y Combinator: $500,000 standard deal, two batches a year — realistic for ambitious African teams "
        "(Paystack, Flutterwave precedent).",
        "Startupbootcamp AfriTech / Techstars: equity accelerators with ~$15k–$120k plus distribution and "
        "investor access.",
    ]
    mvp = [
        "Tony Elumelu Foundation: $5,000 non-dilutive — ideal to fund a pilot without giving up equity.",
        "University innovation grants and campus incubators (e.g. CcHub, Roar Nigeria Hub): small grants "
        "plus distribution to your first users.",
        "Microtraction: ~$25,000 pre-seed once you can show early retention and transaction volume.",
        "Google for Startups Black Founders Fund: up to $150,000 non-dilutive once you have a working "
        "product and traction.",
        "Regional pitch competitions (GITEX, AfricArena, bank-sponsored challenges): visibility, validation, "
        "and small prize cheques.",
    ]
    return {"grant": grant, "vc": vc, "mvp": mvp}.get(founder_mode, mvp)


def _generic_funding(founder_mode: str) -> list[str]:
    grant = [
        "Government innovation and SME grant programmes in your country (search the national "
        "innovation/SME agency) — non-dilutive and worth the paperwork.",
        "Corporate and foundation grants aligned to your impact area (often $5k–$50k + mentorship).",
        "University and incubator grants if you have an academic or research angle.",
        "Climate / inclusion / development-finance challenge funds where your outcomes fit the mandate.",
        "Revenue-based financing (Pipe, Capchase) once you have predictable recurring revenue.",
    ]
    vc = [
        "Y Combinator: $500,000 standard deal, two batches a year — the global pre-seed benchmark.",
        "Techstars: ~$120,000 for ~6–9% plus a 3-month accelerator and investor network.",
        "Antler, Entrepreneur First: build-from-zero programmes that back founders pre-product.",
        "Regional pre-seed micro-VCs and angel syndicates (AngelList, local angel networks): $50k–$500k.",
        "Strategic / corporate VC if a larger player benefits from your distribution or data.",
    ]
    mvp = [
        "Accelerators (YC, Techstars, regional equivalents): cash + distribution + investor access.",
        "Angel syndicates and AngelList rolling funds once you show early retention.",
        "Non-dilutive grants and pitch-competition prizes to extend runway before raising.",
        "Friends-and-family / pre-seed SAFE to fund the first 6–9 months of build and pilot.",
        "Revenue-based financing later, once take-rate or subscription revenue is predictable.",
    ]
    return {"grant": grant, "vc": vc, "mvp": mvp}.get(founder_mode, mvp)


def _nigeria_legal(flags: dict[str, bool]) -> list[str]:
    items = [
        "Incorporate with CAC (Private Company Limited by Shares) and keep the certificate, RC number, and "
        "TIN on file — required for banking, payments, and most grants.",
        "NDPA 2023 compliance: register as a data controller with the NDPC, publish a privacy policy, get "
        "user consent, and store data lawfully.",
        "Consumer-facing Terms of Service, refund/dispute policy, and clear SLAs (the FCCPC enforces "
        "consumer-protection rules).",
        "Tax obligations: file VAT monthly with FIRS, remit Company Income Tax, and handle PAYE once you "
        "have employees.",
    ]
    if flags["handles_money"]:
        items.append(
            "Funds handling: complete SCUML registration and settle through a CBN-licensed processor "
            "(Paystack/Flutterwave) so you don't trip money-transmission licensing yourself."
        )
    items.append(
        "Protect IP: register your trademark, and put founder/IP-assignment and contractor agreements in "
        "place so the company owns the code and brand."
    )
    return items


def _generic_legal(country: str, flags: dict[str, bool]) -> list[str]:
    items = [
        f"Incorporate with the company registrar in {country} and obtain your company number and tax ID.",
        "Data protection: comply with the applicable regime (GDPR/UK GDPR, CCPA, or national law), publish "
        "a privacy policy, and capture lawful consent.",
        "Consumer-facing Terms of Service, refund/dispute policy, and clear service-level commitments.",
        "Tax registration and filing (VAT/GST/sales tax and corporate income tax) plus payroll once you "
        "hire.",
    ]
    if flags["handles_money"]:
        items.append(
            "Funds handling: settle through a licensed processor (Stripe/Adyen/local PSP) and check whether "
            "money-transmitter or e-money licensing applies before holding balances."
        )
    items.append(
        "Protect IP with a trademark filing and founder/contractor IP-assignment agreements so the company "
        "owns the code and brand."
    )
    return items


def country_playbook(payload: StartupIdeaRequest) -> dict:
    """Return concrete, country-aware planning data with real fees, prices and programmes."""
    flags = _industry_flags(payload)
    nigeria = _is_nigeria(payload.country)

    return {
        "verify_note": _VERIFY,
        "incorporation_playbook": (
            _nigeria_incorporation(flags) if nigeria else _generic_incorporation(payload.country, flags)
        ),
        "tooling_stack": _nigeria_tooling(flags) if nigeria else _generic_tooling(flags),
        "build_vs_buy": _build_vs_buy(payload, flags),
        "legal_requirements": (
            _nigeria_legal(flags) if nigeria else _generic_legal(payload.country, flags)
        ),
        "mvp_cost_breakdown": _nigeria_mvp_costs(flags) if nigeria else _generic_mvp_costs(flags),
        "funding_opportunities": (
            _nigeria_funding(payload.founder_mode) if nigeria else _generic_funding(payload.founder_mode)
        ),
    }
