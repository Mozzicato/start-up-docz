"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createStartupProject,
  getStartupProject,
  getProjectExportUrl,
  getProjectPdfUrl,
  listStartupProjects,
  StartupProjectSummary,
  StartupReportResponse
} from "../lib/api";

type FormState = {
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

const initialState: FormState = {
  startup_name: "",
  idea: "",
  industry: "",
  country: "",
  target_audience: "",
  business_model: "SaaS",
  founder_mode: "mvp",
  budget_range_usd: 10000,
  timeline_months: 6
};

export default function HomePage() {
  const [form, setForm] = useState<FormState>(initialState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<StartupReportResponse | null>(null);
  const [savedProjects, setSavedProjects] = useState<StartupProjectSummary[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [activeProjectId, setActiveProjectId] = useState<number | null>(null);

  async function refreshProjects() {
    setIsLoadingProjects(true);
    try {
      const projects = await listStartupProjects();
      setSavedProjects(projects);
    } catch {
      // Keep the current generated report visible even if listing fails.
    } finally {
      setIsLoadingProjects(false);
    }
  }

  useEffect(() => {
    void refreshProjects();
  }, []);

  const readinessStats = useMemo(() => {
    if (!report) return [];
    return [
      ["Overall", `${report.readiness.overall}/100`],
      ["Market", `${report.readiness.market_demand}/10`],
      ["Technical", `${report.readiness.technical_feasibility}/10`],
      ["Funding", `${report.readiness.funding_potential}/10`]
    ];
  }, [report]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await createStartupProject(form);
      setActiveProjectId(result.id);
      setReport(result.report);
      await refreshProjects();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Request failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onLoadProject(projectId: number) {
    setError(null);
    setActiveProjectId(projectId);
    try {
      const project = await getStartupProject(projectId);
      setReport(project.report);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load project.");
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-5 pb-16 pt-10 text-ink">
      <section className="fade-in mb-8 rounded-3xl border border-[#d9cfbd] bg-card/95 p-8 shadow-panel">
        <p className="mb-3 inline-block rounded-full bg-[#f0e8db] px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-muted">
          Startup Planning Studio
        </p>
        <h1 className="font-display text-4xl leading-tight md:text-6xl">
          Build your startup launch package in minutes
        </h1>
        <p className="mt-4 max-w-3xl text-base text-muted md:text-lg">
          StartupDocs interviews you, evaluates feasibility, and generates a launch-ready
          startup document pack.
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <form
          onSubmit={onSubmit}
          className="fade-in rounded-3xl border border-[#d9cfbd] bg-card/95 p-6 shadow-panel"
        >
          <h2 className="font-display text-3xl">Founder Intake</h2>
          <p className="mb-6 mt-2 text-sm text-muted">Step 1: Tell us about your startup idea.</p>

          <div className="grid gap-4">
            <Input
              label="Startup Name"
              value={form.startup_name}
              onChange={(value) => setForm((s) => ({ ...s, startup_name: value }))}
              placeholder="NovaChain"
            />

            <TextArea
              label="Startup Idea"
              value={form.idea}
              onChange={(value) => setForm((s) => ({ ...s, idea: value }))}
              placeholder="Describe what you are building, who it is for, and why now."
            />

            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Industry"
                value={form.industry}
                onChange={(value) => setForm((s) => ({ ...s, industry: value }))}
                placeholder="Fintech"
              />
              <Input
                label="Country"
                value={form.country}
                onChange={(value) => setForm((s) => ({ ...s, country: value }))}
                placeholder="Nigeria"
              />
            </div>

            <Input
              label="Target Audience"
              value={form.target_audience}
              onChange={(value) => setForm((s) => ({ ...s, target_audience: value }))}
              placeholder="University students and early professionals"
            />

            <SelectInput
              label="Founder Mode"
              value={form.founder_mode}
              onChange={(value) =>
                setForm((s) => ({ ...s, founder_mode: value as FormState["founder_mode"] }))
              }
              options={[
                { value: "mvp", label: "Lean MVP" },
                { value: "vc", label: "VC Narrative" },
                { value: "grant", label: "Grant / Impact" }
              ]}
            />

            <div className="grid gap-4 md:grid-cols-3">
              <Input
                label="Business Model"
                value={form.business_model}
                onChange={(value) => setForm((s) => ({ ...s, business_model: value }))}
                placeholder="SaaS"
              />
              <NumberInput
                label="Budget (USD)"
                value={form.budget_range_usd}
                onChange={(value) => setForm((s) => ({ ...s, budget_range_usd: value }))}
              />
              <NumberInput
                label="Timeline (months)"
                value={form.timeline_months}
                onChange={(value) => setForm((s) => ({ ...s, timeline_months: value }))}
              />
            </div>
          </div>

          {error ? <p className="mt-4 text-sm font-semibold text-red-700">{error}</p> : null}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-accent px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-accentDark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Generating startup package..." : "Generate and Save Package"}
          </button>
        </form>

        <aside className="fade-in space-y-5">
          <div className="rounded-3xl border border-[#d9cfbd] bg-card/95 p-6 shadow-panel">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-2xl">Recent Projects</h2>
              <button
                type="button"
                className="rounded-lg border border-[#cdbfa9] px-3 py-1 text-xs font-semibold uppercase tracking-widest text-muted hover:bg-[#f4ead9]"
                onClick={() => void refreshProjects()}
              >
                Refresh
              </button>
            </div>

            {isLoadingProjects ? (
              <p className="text-sm text-muted">Loading projects...</p>
            ) : savedProjects.length === 0 ? (
              <p className="text-sm text-muted">No saved projects yet.</p>
            ) : (
              <ul className="space-y-2">
                {savedProjects.map((project) => (
                  <li key={project.id}>
                    <button
                      type="button"
                      onClick={() => void onLoadProject(project.id)}
                      className={`w-full rounded-xl border px-3 py-2 text-left transition ${
                        activeProjectId === project.id
                          ? "border-accent bg-[#f8e7dc]"
                          : "border-[#d4c9b5] bg-[#fff8ed] hover:bg-[#f6ecdd]"
                      }`}
                    >
                      <p className="font-semibold">{project.startup_name}</p>
                      <p className="text-xs text-muted">
                        {project.industry} · {project.country} · {project.readiness_overall}/100
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-3xl border border-[#d9cfbd] bg-card/95 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-3xl">Generated Output</h2>
              {activeProjectId ? (
                <div className="flex items-center gap-2">
                  <a
                    href={getProjectPdfUrl(activeProjectId)}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg bg-accent px-3 py-2 text-xs font-semibold uppercase tracking-widest text-white transition hover:bg-accentDark"
                  >
                    Download PDF
                  </a>
                  <a
                    href={getProjectExportUrl(activeProjectId)}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg border border-[#cdbfa9] px-3 py-2 text-xs font-semibold uppercase tracking-widest text-muted hover:bg-[#f4ead9]"
                  >
                    .md
                  </a>
                </div>
              ) : null}
            </div>

            {!report ? (
              <div className="mt-6 rounded-2xl border border-dashed border-[#cabca7] bg-[#f7f1e6] p-5 text-sm text-muted">
                Submit the intake form to preview market research, feasibility, roadmap, and
                readiness score.
              </div>
            ) : (
              <div className="mt-5 space-y-4 text-sm fade-in">
                <h3 className="font-display text-2xl">{report.startup_name}</h3>
                <p>{report.summary}</p>

                <div className="grid grid-cols-2 gap-3">
                  {readinessStats.map(([label, value]) => (
                    <div key={label} className="rounded-xl bg-[#f7efe1] p-3">
                      <p className="text-xs uppercase tracking-widest text-muted">{label}</p>
                      <p className="font-semibold text-lg">{value}</p>
                    </div>
                  ))}
                </div>

                <article className="rounded-xl bg-[#f6ecdc] p-3">
                  <h4 className="text-xs uppercase tracking-widest text-muted">Quality Score</h4>
                  <p className="mt-1 font-semibold text-lg">
                    {report.quality_assessment?.overall ?? 0}/100
                  </p>
                  {report.quality_assessment?.issues?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-4">
                      {report.quality_assessment.issues.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-1 text-sm">All sections passed quality thresholds.</p>
                  )}
                </article>

                <InfoBlock title="Market Research" text={report.market_research} />
                <InfoBlock title="Competitor Analysis" text={report.competitor_analysis} />
                <InfoBlock title="Differentiation" text={report.differentiation} />
                <InfoBlock title="Feasibility" text={report.feasibility_report} />
                <InfoBlock title="Unit Economics" text={report.unit_economics} />
                <ListBlock title="Roadmap" items={report.roadmap} />
                <ListBlock title="Growth Experiments" items={report.growth_experiments} />
                <ListBlock title="Risk Register" items={report.risk_register} />
                <ListBlock title="Funding Opportunities" items={report.funding_opportunities} />
                <ListBlock title="Launch Checklist" items={report.launch_checklist} />
                {report.sources?.length ? <ListBlock title="Sources" items={report.sources} /> : null}
              </div>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <input
        className="w-full rounded-xl border border-[#c9bda9] bg-[#fffaf2] px-3 py-2 text-sm outline-none ring-accent transition focus:ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  placeholder
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <textarea
        rows={4}
        className="w-full rounded-xl border border-[#c9bda9] bg-[#fffaf2] px-3 py-2 text-sm outline-none ring-accent transition focus:ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function NumberInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <input
        type="number"
        className="w-full rounded-xl border border-[#c9bda9] bg-[#fffaf2] px-3 py-2 text-sm outline-none ring-accent transition focus:ring"
        value={value}
        onChange={(e) => onChange(Number(e.target.value || 0))}
      />
    </label>
  );
}

function SelectInput({
  label,
  value,
  onChange,
  options
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="grid gap-2 text-sm font-medium">
      {label}
      <select
        className="w-full rounded-xl border border-[#c9bda9] bg-[#fffaf2] px-3 py-2 text-sm outline-none ring-accent transition focus:ring"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function InfoBlock({ title, text }: { title: string; text: string }) {
  return (
    <article className="rounded-xl bg-[#f6ecdc] p-3">
      <h4 className="text-xs uppercase tracking-widest text-muted">{title}</h4>
      <p className="mt-1">{text}</p>
    </article>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <article className="rounded-xl bg-[#f6ecdc] p-3">
      <h4 className="text-xs uppercase tracking-widest text-muted">{title}</h4>
      <ul className="mt-2 list-disc space-y-1 pl-4">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}
