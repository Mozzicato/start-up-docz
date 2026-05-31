from app.schemas import StartupReportResponse


def build_markdown_package(report: StartupReportResponse) -> str:
    roadmap = "\n".join([f"- {item}" for item in report.roadmap])
    funding = "\n".join([f"- {item}" for item in report.funding_opportunities])
    checklist = "\n".join([f"- {item}" for item in report.launch_checklist])

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

## Market Research

{report.market_research}

## Competitor Analysis

{report.competitor_analysis}

## Feasibility Report

{report.feasibility_report}

## Product Roadmap

{roadmap}

## Funding Opportunities

{funding}

## Launch Checklist

{checklist}
"""
