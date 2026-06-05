export type StartupIdeaRequest = {
  startup_name: string;
  idea: string;
  industry: string;
  country: string;
  target_audience: string;
  business_model: string;
  founder_mode: "mvp" | "vc" | "grant";
  budget_range_usd: number;
  timeline_months: number;
};

export type QualityAssessment = {
  overall: number;
  section_scores: Record<string, number>;
  issues: string[];
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
  differentiation: string;
  product_build_plan: string;
  feasibility_report: string;
  unit_economics: string;
  cac_model: string;
  team_and_execution_strategy: string;
  build_vs_buy: string;
  roadmap: string[];
  mvp_cost_breakdown: string[];
  tooling_stack: string[];
  incorporation_playbook: string[];
  legal_requirements: string[];
  growth_experiments: string[];
  risk_register: string[];
  funding_opportunities: string[];
  launch_checklist: string[];
  sources: string[];
  quality_assessment: QualityAssessment;
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

// Prefer same-origin API calls so deployments can use Next.js rewrites.
// Supports either a root backend URL (e.g. http://localhost:8000)
// or an explicit API URL (e.g. http://localhost:8000/api).
function normalizeApiBase(raw?: string): string {
  const fallback = "/api";
  const value = (raw || "").trim();
  if (!value) return fallback;

  const withoutTrailingSlash = value.replace(/\/+$/, "");
  if (withoutTrailingSlash === "/api") return "/api";
  if (withoutTrailingSlash.endsWith("/api")) return withoutTrailingSlash;
  return `${withoutTrailingSlash}/api`;
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_BASE_URL);

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, init);

    if (!res.ok) {
      throw new Error(`Request failed (${res.status}).`);
    }

    return res.json() as Promise<T>;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        "Network error: unable to reach the API. Check frontend API base URL/rewrite and backend availability."
      );
    }
    throw error;
  }
}

export function getProjectExportUrl(projectId: number): string {
  return `${API_BASE}/v1/projects/${projectId}/package.md`;
}

export function getProjectPdfUrl(projectId: number): string {
  return `${API_BASE}/v1/projects/${projectId}/package.pdf`;
}

export async function createStartupReport(
  payload: StartupIdeaRequest
): Promise<StartupReportResponse> {
  return requestJson<StartupReportResponse>("/v1/startup/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function createStartupProject(
  payload: StartupIdeaRequest
): Promise<StartupProjectResponse> {
  return requestJson<StartupProjectResponse>("/v1/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function listStartupProjects(): Promise<StartupProjectSummary[]> {
  return requestJson<StartupProjectSummary[]>("/v1/projects", { cache: "no-store" });
}

export async function getStartupProject(projectId: number): Promise<StartupProjectResponse> {
  return requestJson<StartupProjectResponse>(`/v1/projects/${projectId}`, {
    cache: "no-store"
  });
}
