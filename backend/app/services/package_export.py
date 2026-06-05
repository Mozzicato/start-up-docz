import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas import StartupReportResponse

_ACCENT = colors.HexColor("#b45309")
_INK = colors.HexColor("#1f2937")
_MUTED = colors.HexColor("#6b7280")
_LINE = colors.HexColor("#e5e7eb")


def _pdf_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"], fontSize=26, leading=30,
            textColor=_INK, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle", parent=base["Normal"], fontSize=12, leading=16,
            textColor=_MUTED, spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"], fontSize=15, leading=19,
            textColor=_ACCENT, spaceBefore=16, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyTextX", parent=base["BodyText"], fontSize=10.5, leading=15,
            spaceAfter=8, textColor=_INK,
        ),
        "bullet": ParagraphStyle(
            "BulletX", parent=base["BodyText"], fontSize=10.5, leading=15,
            textColor=_INK,
        ),
    }


def _paragraphs(text: str, style: ParagraphStyle) -> list[Paragraph]:
    """Split free text into paragraphs on blank lines, XML-escaped for ReportLab."""
    blocks = [b.strip() for b in (text or "").split("\n\n") if b.strip()]
    if not blocks:
        blocks = [(text or "").strip() or "—"]
    return [Paragraph(escape(b).replace("\n", "<br/>"), style) for b in blocks]


def build_pdf_package(report: StartupReportResponse) -> bytes:
    """Render the full startup package as a styled, multi-section PDF (bytes)."""
    styles = _pdf_styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=22 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"{report.startup_name} Startup Package",
    )

    story: list = [
        Paragraph(escape(report.startup_name), styles["title"]),
        Paragraph("Startup Launch Package", styles["subtitle"]),
        HRFlowable(width="100%", thickness=1, color=_LINE),
        Spacer(1, 10),
        Paragraph("Executive Summary", styles["h2"]),
        *_paragraphs(report.summary, styles["body"]),
        Paragraph("Startup Readiness", styles["h2"]),
    ]

    r = report.readiness
    rows = [
        ["Metric", "Score"],
        ["Overall", f"{r.overall}/100"],
        ["Market Demand", f"{r.market_demand}/10"],
        ["Technical Feasibility", f"{r.technical_feasibility}/10"],
        ["Competition", f"{r.competition}/10"],
        ["Funding Potential", f"{r.funding_potential}/10"],
        ["Execution Complexity", f"{r.execution_complexity}/10"],
        ["Go-To-Market Readiness", f"{r.go_to_market_readiness}/10"],
    ]
    table = Table(rows, colWidths=[110 * mm, 40 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fdf6ec"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    story.append(Paragraph("Quality Assessment", styles["h2"]))
    story.extend(_paragraphs(f"Overall quality score: {report.quality_assessment.overall}/100", styles["body"]))
    if report.quality_assessment.issues:
        story.append(ListFlowable(
            [
                ListItem(Paragraph(escape(item), styles["bullet"]))
                for item in report.quality_assessment.issues
            ],
            bulletType="bullet", start="•", leftIndent=14,
        ))

    for heading, text in [
        ("Market Research", report.market_research),
        ("Competitor Analysis", report.competitor_analysis),
        ("Differentiation", report.differentiation),
        ("Feasibility Report", report.feasibility_report),
        ("Unit Economics", report.unit_economics),
    ]:
        story.append(Paragraph(heading, styles["h2"]))
        story.extend(_paragraphs(text, styles["body"]))

    for heading, items in [
        ("Product Roadmap", report.roadmap),
        ("Growth Experiments", report.growth_experiments),
        ("Risk Register", report.risk_register),
        ("Funding Opportunities", report.funding_opportunities),
        ("Launch Checklist", report.launch_checklist),
    ]:
        story.append(Paragraph(heading, styles["h2"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(escape(item), styles["bullet"])) for item in items],
            bulletType="bullet", start="•", leftIndent=14,
        ))

    if report.sources:
        story.append(Paragraph("Sources", styles["h2"]))
        story.append(ListFlowable(
            [ListItem(Paragraph(escape(item), styles["bullet"])) for item in report.sources],
            bulletType="bullet", start="•", leftIndent=14,
        ))

    doc.build(story)
    return buffer.getvalue()


def build_markdown_package(report: StartupReportResponse) -> str:
    roadmap = "\n".join([f"- {item}" for item in report.roadmap])
    growth_experiments = "\n".join([f"- {item}" for item in report.growth_experiments])
    risk_register = "\n".join([f"- {item}" for item in report.risk_register])
    funding = "\n".join([f"- {item}" for item in report.funding_opportunities])
    checklist = "\n".join([f"- {item}" for item in report.launch_checklist])
    sources = "\n".join([f"- {item}" for item in report.sources])
    quality_issues = "\n".join([f"- {item}" for item in report.quality_assessment.issues])

    return f"""# {report.startup_name} Startup Package

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

## Quality Assessment

- Overall: {report.quality_assessment.overall}/100

{quality_issues if quality_issues else "- No quality issues detected"}

## Market Research

{report.market_research}

## Competitor Analysis

{report.competitor_analysis}

## Differentiation

{report.differentiation}

## Feasibility Report

{report.feasibility_report}

## Unit Economics

{report.unit_economics}

## Product Roadmap

{roadmap}

## Growth Experiments

{growth_experiments}

## Risk Register

{risk_register}

## Funding Opportunities

{funding}

## Launch Checklist

{checklist}

## Sources

{sources if sources else "- No external sources captured"}
"""
