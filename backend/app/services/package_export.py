import io
from datetime import datetime, timezone
from functools import partial
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas import StartupReportResponse

# ---------------------------------------------------------------------------
# Palette (warm "studio" theme, matched to the web app accent)
# ---------------------------------------------------------------------------
_ACCENT = colors.HexColor("#B45309")      # amber
_ACCENT_DARK = colors.HexColor("#7C3A06")
_INK = colors.HexColor("#1F2937")
_MUTED = colors.HexColor("#6B7280")
_LINE = colors.HexColor("#E7E0D2")
_CREAM = colors.HexColor("#FBF6EC")        # callout / table fill
_CREAM_ALT = colors.HexColor("#F4EADA")
_GOOD = colors.HexColor("#15803D")
_WARN = colors.HexColor("#C2410C")
_BAD = colors.HexColor("#B91C1C")
_PAPER = colors.HexColor("#FFFDF8")

_PAGE_W, _PAGE_H = A4
_MARGIN = 18 * mm


def _bar_color(fraction: float) -> colors.Color:
    if fraction >= 0.7:
        return _GOOD
    if fraction >= 0.45:
        return _ACCENT
    return _BAD


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def _pdf_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle(
            "Eyebrow", parent=base["Normal"], fontSize=8.5, leading=12,
            textColor=_ACCENT, fontName="Helvetica-Bold",
            spaceAfter=2, tracking=2,
        ),
        "h2": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"], fontSize=14.5, leading=18,
            textColor=_INK, fontName="Helvetica-Bold", spaceBefore=2, spaceAfter=2,
        ),
        "h2num": ParagraphStyle(
            "SectionNumber", parent=base["Heading2"], fontSize=14.5, leading=18,
            textColor=_ACCENT, fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "BodyTextX", parent=base["BodyText"], fontSize=10.2, leading=15.5,
            spaceAfter=7, textColor=_INK,
        ),
        "callout": ParagraphStyle(
            "Callout", parent=base["BodyText"], fontSize=10.2, leading=15.5,
            spaceAfter=6, textColor=_INK,
        ),
        "bullet": ParagraphStyle(
            "BulletX", parent=base["BodyText"], fontSize=10.2, leading=14.5,
            textColor=_INK,
        ),
        "kv_key": ParagraphStyle(
            "KvKey", parent=base["BodyText"], fontSize=9.6, leading=13,
            textColor=_ACCENT_DARK, fontName="Helvetica-Bold",
        ),
        "kv_val": ParagraphStyle(
            "KvVal", parent=base["BodyText"], fontSize=9.6, leading=13,
            textColor=_INK,
        ),
        "step": ParagraphStyle(
            "Step", parent=base["BodyText"], fontSize=9.8, leading=14,
            textColor=_INK,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=8.6, leading=12,
            textColor=_MUTED,
        ),
    }


# The built-in PDF fonts use WinAnsi (CP1252) encoding, which lacks a few symbols common
# in our content (Naira sign, approx sign, arrows). Map them to safe equivalents and drop
# anything else outside CP1252 so nothing renders as a "tofu" box.
_PDF_SUBS = {
    "₦": "NGN ",  # ₦
    "≈": "~",      # ≈
    "→": "->",     # →
    "₣": "FCFA ",  # ₣ (CFA-ish)
    " ": " ",      # non-breaking space
    " ": " ",
    " ": " ",
}


def _clean(text: str) -> str:
    if not text:
        return text or ""
    for src, dst in _PDF_SUBS.items():
        text = text.replace(src, dst)
    # Final guard: anything still outside CP1252 (which Helvetica supports) becomes "?".
    return text.encode("cp1252", "replace").decode("cp1252")


def _esc(text: str) -> str:
    return escape(_clean(text))


def _para_blocks(text: str, style: ParagraphStyle) -> list[Paragraph]:
    text = _clean(text)
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [text.strip() or "—"]
    return [Paragraph(escape(b).replace("\n", "<br/>"), style) for b in blocks]


# ---------------------------------------------------------------------------
# Custom flowables
# ---------------------------------------------------------------------------
class _ScoreBars(Flowable):
    """Horizontal score bars for the readiness metrics."""

    def __init__(self, rows: list[tuple[str, float, float]]):
        super().__init__()
        self.rows = rows
        self._row_h = 24
        self.width = 0
        self.height = len(rows) * self._row_h

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        self.height = len(self.rows) * self._row_h
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        label_w = 150
        value_w = 52
        track_x = label_w
        track_w = self.width - label_w - value_w
        track_h = 9

        for i, (label, value, maxv) in enumerate(self.rows):
            y = self.height - (i + 1) * self._row_h + (self._row_h - track_h) / 2
            ty = y + track_h + 1  # text baseline alignment helper

            frac = max(0.0, min(1.0, value / maxv if maxv else 0))

            c.setFillColor(_INK)
            c.setFont("Helvetica", 9.2)
            c.drawString(0, y, label)

            # track
            c.setFillColor(_CREAM_ALT)
            c.roundRect(track_x, y - 1, track_w, track_h, 2, fill=1, stroke=0)
            # fill
            c.setFillColor(_bar_color(frac))
            fill_w = max(3, track_w * frac)
            c.roundRect(track_x, y - 1, fill_w, track_h, 2, fill=1, stroke=0)

            # value
            c.setFillColor(_INK)
            c.setFont("Helvetica-Bold", 9.2)
            val_txt = f"{value:g}/{maxv:g}"
            c.drawRightString(self.width, y, val_txt)
            _ = ty


def _ring(c, cx, cy, radius, fraction, value_text, label):
    """Donut gauge drawn on a canvas."""
    frac = max(0.0, min(1.0, fraction))
    # base ring
    c.setFillColor(colors.Color(1, 1, 1, alpha=0.22))
    c.circle(cx, cy, radius, fill=1, stroke=0)
    # progress wedge
    c.setFillColor(colors.white)
    c.wedge(cx - radius, cy - radius, cx + radius, cy + radius, 90, -360 * frac, fill=1, stroke=0)
    # inner cut-out (donut hole) — accent band color
    c.setFillColor(_ACCENT)
    c.circle(cx, cy, radius * 0.66, fill=1, stroke=0)
    # number
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(cx, cy - 4, value_text)
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx, cy - 18, label)


# ---------------------------------------------------------------------------
# Page chrome (cover + running header/footer)
# ---------------------------------------------------------------------------
def _draw_cover(canvas, doc, report: StartupReportResponse, meta: dict):
    canvas.saveState()
    # paper background
    canvas.setFillColor(_PAPER)
    canvas.rect(0, 0, _PAGE_W, _PAGE_H, fill=1, stroke=0)

    band_h = 250
    band_y = _PAGE_H - band_h
    canvas.setFillColor(_ACCENT)
    canvas.rect(0, band_y, _PAGE_W, band_h, fill=1, stroke=0)
    # thin darker base line of band
    canvas.setFillColor(_ACCENT_DARK)
    canvas.rect(0, band_y, _PAGE_W, 4, fill=1, stroke=0)

    left = _MARGIN
    # eyebrow
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.85))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(left, band_y + band_h - 46, "S T A R T U P   L A U N C H   P A C K A G E")

    # startup name — shrink to fit
    name = _clean(report.startup_name or "Untitled Startup")
    size = 40
    max_w = _PAGE_W - 2 * left - 150
    while size > 20 and stringWidth(name, "Helvetica-Bold", size) > max_w:
        size -= 1
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", size)
    canvas.drawString(left, band_y + band_h - 96, name)

    # tagline
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.9))
    canvas.setFont("Helvetica", 11)
    canvas.drawString(
        left, band_y + band_h - 122,
        "Founder-grade research, costs, and a launch plan — built in minutes.",
    )

    # meta chips
    chips = [meta["industry"], meta["country"], meta["mode"], meta["date"]]
    cx = left
    canvas.setFont("Helvetica-Bold", 8.5)
    for chip in chips:
        if not chip:
            continue
        chip = _clean(chip)
        w = stringWidth(chip, "Helvetica-Bold", 8.5) + 18
        canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.16))
        canvas.roundRect(cx, band_y + 26, w, 18, 9, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.drawString(cx + 9, band_y + 31, chip)
        cx += w + 8

    # readiness ring (over the band, right side)
    _ring(
        canvas,
        _PAGE_W - left - 56,
        band_y + band_h - 86,
        52,
        report.readiness.overall / 100.0,
        str(report.readiness.overall),
        "READINESS",
    )

    # "What's inside" panel
    panel_x = left
    panel_w = _PAGE_W - 2 * left
    panel_h = 162
    panel_y = band_y - 30 - panel_h
    canvas.setFillColor(_CREAM)
    canvas.setStrokeColor(_LINE)
    canvas.roundRect(panel_x, panel_y, panel_w, panel_h, 10, fill=1, stroke=1)

    canvas.setFillColor(_ACCENT_DARK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(panel_x + 20, panel_y + panel_h - 26, "WHAT'S INSIDE THIS PACKAGE")

    inside = [
        "Market research, sizing & competitor wedge",
        "Build plan: vibe-code vs hire vs agency",
        "MVP cost breakdown with real vendor prices",
        "Company registration & compliance steps",
        "Tooling stack with live pricing",
        "Named grants & investors with check sizes",
        "Unit economics, CAC model & 12-week roadmap",
        "Risk register & launch checklist",
    ]
    canvas.setFont("Helvetica", 9.4)
    col_x = [panel_x + 22, panel_x + panel_w / 2 + 12]
    for idx, item in enumerate(inside):
        col = idx % 2
        row = idx // 2
        iy = panel_y + panel_h - 50 - row * 24
        canvas.setFillColor(_ACCENT)
        canvas.circle(col_x[col] + 3, iy + 3, 2.4, fill=1, stroke=0)
        canvas.setFillColor(_INK)
        canvas.drawString(col_x[col] + 12, iy, item)

    # highlight stat cards
    r = report.readiness
    cards = [
        ("MARKET DEMAND", f"{r.market_demand:g}/10"),
        ("FUNDING POTENTIAL", f"{r.funding_potential:g}/10"),
        ("GO-TO-MARKET", f"{r.go_to_market_readiness:g}/10"),
    ]
    gap = 14
    card_w = (panel_w - 2 * gap) / 3
    card_h = 78
    card_y = panel_y - 26 - card_h
    for i, (clabel, cvalue) in enumerate(cards):
        cxp = panel_x + i * (card_w + gap)
        canvas.setFillColor(_PAPER)
        canvas.setStrokeColor(_LINE)
        canvas.roundRect(cxp, card_y, card_w, card_h, 8, fill=1, stroke=1)
        canvas.setFillColor(_ACCENT)
        canvas.roundRect(cxp, card_y, 4, card_h, 2, fill=1, stroke=0)
        canvas.setFillColor(_MUTED)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(cxp + 16, card_y + card_h - 24, clabel)
        canvas.setFillColor(_INK)
        canvas.setFont("Helvetica-Bold", 26)
        canvas.drawString(cxp + 16, card_y + 20, cvalue)

    # footer note
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(left, 38, "Generated by StartupDocs — your AI startup advisor.")
    canvas.drawRightString(_PAGE_W - left, 38, meta["date"])
    canvas.setStrokeColor(_LINE)
    canvas.line(left, 50, _PAGE_W - left, 50)
    canvas.restoreState()


def _draw_chrome(canvas, doc, report: StartupReportResponse):
    canvas.saveState()
    canvas.setFillColor(_PAPER)
    canvas.rect(0, 0, _PAGE_W, _PAGE_H, fill=1, stroke=0)

    # header
    name = _clean(report.startup_name or "Untitled Startup")
    canvas.setFillColor(_ACCENT)
    canvas.rect(_MARGIN, _PAGE_H - _MARGIN + 8, 22, 3, fill=1, stroke=0)
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(_MARGIN + 28, _PAGE_H - _MARGIN + 7, name.upper())
    canvas.drawRightString(_PAGE_W - _MARGIN, _PAGE_H - _MARGIN + 7, "STARTUP LAUNCH PACKAGE")
    canvas.setStrokeColor(_LINE)
    canvas.line(_MARGIN, _PAGE_H - _MARGIN + 2, _PAGE_W - _MARGIN, _PAGE_H - _MARGIN + 2)

    # footer
    canvas.setStrokeColor(_LINE)
    canvas.line(_MARGIN, _MARGIN - 6, _PAGE_W - _MARGIN, _MARGIN - 6)
    canvas.setFillColor(_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(_MARGIN, _MARGIN - 16, "StartupDocs")
    canvas.drawRightString(_PAGE_W - _MARGIN, _MARGIN - 16, f"Page {doc.page - 1}")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------
class _SectionCounter:
    def __init__(self):
        self.n = 0

    def next(self) -> str:
        self.n += 1
        return f"{self.n:02d}"


def _heading(counter: _SectionCounter, title: str, styles) -> KeepTogether:
    num = counter.next()
    head = Table(
        [[Paragraph(num, styles["h2num"]), Paragraph(escape(title), styles["h2"])]],
        colWidths=[26, None],
        hAlign="LEFT",
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return KeepTogether([
        Spacer(1, 12),
        head,
        HRFlowable(width="100%", thickness=2, color=_ACCENT, spaceBefore=2, spaceAfter=8),
    ])


def _narrative_section(counter, title, text, styles) -> list:
    return [_heading(counter, title, styles), *_para_blocks(text, styles["body"])]


def _bullet_section(counter, title, items, styles, ordered=False) -> list:
    if not items:
        items = ["—"]
    rows = [ListItem(Paragraph(_esc(item), styles["bullet"])) for item in items]
    if ordered:
        flow = ListFlowable(
            rows, bulletType="1", start=1, bulletFormat="%s.",
            bulletColor=_ACCENT, bulletFontName="Helvetica-Bold",
            leftIndent=18, bulletFontSize=10,
        )
    else:
        flow = ListFlowable(
            rows, bulletType="bullet", start="•",
            bulletColor=_ACCENT, bulletFontName="Helvetica-Bold",
            leftIndent=16, bulletFontSize=9,
        )
    return [_heading(counter, title, styles), flow]


def _callout_section(counter, title, text, styles) -> list:
    inner = _para_blocks(text, styles["callout"])
    box = Table([[inner]], colWidths=["100%"])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _CREAM),
        ("BOX", (0, 0), (-1, -1), 0.75, _LINE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, _ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [_heading(counter, title, styles), box]


def _kv_table_section(counter, title, items, styles) -> list:
    """Render 'Label: detail' lines as a two-column table; plain lines span both."""
    data = []
    for item in items or ["—"]:
        if ": " in item:
            key, val = item.split(": ", 1)
        else:
            key, val = "", item
        data.append([Paragraph(_esc(key), styles["kv_key"]), Paragraph(_esc(val), styles["kv_val"])])

    table = Table(data, colWidths=[52 * mm, None], hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), _CREAM),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_CREAM, _PAPER]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, _LINE),
        ("BOX", (0, 0), (-1, -1), 0.6, _LINE),
        ("LINEAFTER", (0, 0), (0, -1), 0.6, _LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    table.setStyle(TableStyle(style))
    return [_heading(counter, title, styles), table]


def _readiness_section(counter, report, styles) -> list:
    r = report.readiness
    rows = [
        ("Market Demand", r.market_demand, 10),
        ("Technical Feasibility", r.technical_feasibility, 10),
        ("Competition", r.competition, 10),
        ("Funding Potential", r.funding_potential, 10),
        ("Execution Complexity", r.execution_complexity, 10),
        ("Go-To-Market Readiness", r.go_to_market_readiness, 10),
    ]
    intro = Paragraph(
        f"<b>Overall readiness: {r.overall}/100.</b> Scores below weight market pull, build "
        "difficulty, competitive heat, and funding access. Treat anything under 6/10 as a focus area.",
        styles["body"],
    )
    return [_heading(counter, "Startup Readiness", styles), intro, Spacer(1, 4), _ScoreBars(rows)]


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------
_MODE_LABELS = {"mvp": "Lean MVP", "vc": "VC Narrative", "grant": "Grant / Impact"}


def build_pdf_package(
    report: StartupReportResponse,
    *,
    industry: str = "",
    country: str = "",
    founder_mode: str = "",
) -> bytes:
    """Render the full startup package as a polished, multi-section PDF (bytes)."""
    styles = _pdf_styles()
    buffer = io.BytesIO()

    meta = {
        "industry": industry.strip(),
        "country": country.strip(),
        "mode": _MODE_LABELS.get(founder_mode.strip().lower(), ""),
        "date": datetime.now(timezone.utc).strftime("%d %b %Y"),
    }

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=_MARGIN + 6 * mm,
        bottomMargin=_MARGIN,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        title=f"{report.startup_name} Startup Package",
        author="StartupDocs",
    )

    content_w = _PAGE_W - 2 * _MARGIN
    cover_frame = Frame(_MARGIN, _MARGIN, content_w, _PAGE_H - 2 * _MARGIN, id="cover")
    main_frame = Frame(
        _MARGIN, _MARGIN, content_w, _PAGE_H - 2 * _MARGIN - 6 * mm, id="main"
    )

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame],
                     onPage=partial(_draw_cover, report=report, meta=meta)),
        PageTemplate(id="Main", frames=[main_frame],
                     onPage=partial(_draw_chrome, report=report)),
    ])

    counter = _SectionCounter()
    # Cover page is drawn entirely by the Cover template's onPage hook; switch to the Main
    # template and break so all subsequent content uses the running header/footer chrome.
    story: list = [NextPageTemplate("Main"), PageBreak()]

    story += _narrative_section(counter, "Executive Summary", report.summary, styles)
    story += _readiness_section(counter, report, styles)
    story += _narrative_section(counter, "Market Research", report.market_research, styles)
    story += _narrative_section(counter, "Competitor Analysis", report.competitor_analysis, styles)
    story += _narrative_section(counter, "Differentiation & Defensibility", report.differentiation, styles)
    story += _narrative_section(counter, "Product Build Plan", report.product_build_plan, styles)
    story += _callout_section(
        counter, "How To Build It: Vibe-Code vs Hire vs Agency", report.build_vs_buy, styles
    )
    story += _narrative_section(counter, "Feasibility", report.feasibility_report, styles)
    story += _narrative_section(counter, "Unit Economics", report.unit_economics, styles)
    story += _narrative_section(counter, "Customer Acquisition (CAC) Model", report.cac_model, styles)
    story += _narrative_section(
        counter, "Team & Execution Strategy", report.team_and_execution_strategy, styles
    )
    story += _bullet_section(counter, "12-Week Product Roadmap", report.roadmap, styles, ordered=True)
    story += _kv_table_section(counter, "MVP Cost Breakdown", report.mvp_cost_breakdown, styles)
    story += _kv_table_section(counter, "Tooling & Stack (with pricing)", report.tooling_stack, styles)
    story += _bullet_section(
        counter, "Company Registration Playbook", report.incorporation_playbook, styles, ordered=True
    )
    story += _bullet_section(counter, "Legal & Compliance Requirements", report.legal_requirements, styles)
    story += _bullet_section(counter, "Growth Experiments", report.growth_experiments, styles)
    story += _bullet_section(counter, "Risk Register", report.risk_register, styles)
    story += _bullet_section(
        counter, "Funding Opportunities (named, with check sizes)", report.funding_opportunities, styles
    )
    story += _bullet_section(counter, "Launch Checklist", report.launch_checklist, styles)

    if report.sources:
        story += _bullet_section(counter, "Sources", report.sources, styles)

    # quality + disclaimer footer block
    qa = report.quality_assessment
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.6, color=_LINE, spaceAfter=6))
    story.append(Paragraph(
        f"Document quality score: <b>{qa.overall}/100</b>. "
        "This package is AI-generated planning material — verify fees, legal steps, and grant "
        "details with the official source before you spend money or file anything.",
        styles["small"],
    ))

    doc.build(story)
    return buffer.getvalue()


def build_markdown_package(report: StartupReportResponse) -> str:
    def _list(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- —"

    quality_issues = (
        "\n".join(f"- {item}" for item in report.quality_assessment.issues)
        or "- No quality issues detected"
    )
    sources = "\n".join(f"- {item}" for item in report.sources) or "- No external sources captured"

    return f"""# {report.startup_name} — Startup Launch Package

> Founder-grade research, costs, and a launch plan. AI-generated planning material — verify fees,
> legal steps, and grant details with the official source before spending money.

## Executive Summary

{report.summary}

## Startup Readiness

- Overall: {report.readiness.overall}/100
- Market Demand: {report.readiness.market_demand}/10
- Technical Feasibility: {report.readiness.technical_feasibility}/10
- Competition: {report.readiness.competition}/10
- Funding Potential: {report.readiness.funding_potential}/10
- Execution Complexity: {report.readiness.execution_complexity}/10
- Go-To-Market Readiness: {report.readiness.go_to_market_readiness}/10

## Market Research

{report.market_research}

## Competitor Analysis

{report.competitor_analysis}

## Differentiation & Defensibility

{report.differentiation}

## Product Build Plan

{report.product_build_plan}

## How To Build It: Vibe-Code vs Hire vs Agency

{report.build_vs_buy}

## Feasibility

{report.feasibility_report}

## Unit Economics

{report.unit_economics}

## Customer Acquisition (CAC) Model

{report.cac_model}

## Team & Execution Strategy

{report.team_and_execution_strategy}

## 12-Week Product Roadmap

{_list(report.roadmap)}

## MVP Cost Breakdown

{_list(report.mvp_cost_breakdown)}

## Tooling & Stack (with pricing)

{_list(report.tooling_stack)}

## Company Registration Playbook

{_list(report.incorporation_playbook)}

## Legal & Compliance Requirements

{_list(report.legal_requirements)}

## Growth Experiments

{_list(report.growth_experiments)}

## Risk Register

{_list(report.risk_register)}

## Funding Opportunities (named, with check sizes)

{_list(report.funding_opportunities)}

## Launch Checklist

{_list(report.launch_checklist)}

## Sources

{sources}

## Quality Assessment

- Overall: {report.quality_assessment.overall}/100

{quality_issues}
"""
