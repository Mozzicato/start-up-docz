export type StartupIdeaRequest = {
  startup_name: string;
  idea: string;
  industry: string;
  country: string;
  target_audience: string;
  business_model: string;
  budget_range_usd: number;
  timeline_months: number;
};

export type StartupReportResponse = {
  startup_name: string;
  summary: string;
  readiness: {
    overall: number;
    market_demand: number;
    technical_feasibility: number;
    competition: number;
    funding_potential: number;
    execution_complexity: number;
    go_to_market_readiness: number;
  };
  market_research: string;
  competitor_analysis: string;
  feasibility_report: string;
  roadmap: string[];
  funding_opportunities: string[];
  launch_checklist: string[];
};

export type StartupProjectSummary = {
  id: number;
  startup_name: string;
  industry: string;
  country: string;
  readiness_overall: number;
  created_at: string;
};

export type StartupProjectResponse = {
  id: number;
  startup_name: string;
  industry: string;
  country: string;
  created_at: string;
  report: StartupReportResponse;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getProjectExportUrl(projectId: number): string {
  return `${API_BASE}/api/v1/projects/${projectId}/package.md`;
}

export function getProjectPdfUrl(projectId: number): string {
  return `${API_BASE}/api/v1/projects/${projectId}/package.pdf`;
}

export async function createStartupReport(
  payload: StartupIdeaRequest
): Promise<StartupReportResponse> {
  const res = await fetch(`${API_BASE}/api/v1/startup/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error("Failed to generate startup report.");
  }

  return res.json();
}

export async function createStartupProject(
  payload: StartupIdeaRequest
): Promise<StartupProjectResponse> {
  const res = await fetch(`${API_BASE}/api/v1/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error("Failed to create startup project.");
  }

  return res.json();
}

export async function listStartupProjects(): Promise<StartupProjectSummary[]> {
  const res = await fetch(`${API_BASE}/api/v1/projects`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to list projects.");
  }

  return res.json();
}

export async function getStartupProject(projectId: number): Promise<StartupProjectResponse> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
    cache: "no-store"
  });

  if (!res.ok) {
    throw new Error("Failed to load project.");
  }

  return res.json();
}
