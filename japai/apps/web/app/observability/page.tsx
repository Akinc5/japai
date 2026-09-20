"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  AiRunRow,
  ObservabilitySummary,
  fetchAiRuns,
  fetchObservabilitySummary,
} from "@/lib/api";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div
      style={{
        border: "1px solid #333",
        borderRadius: 8,
        padding: "12px 16px",
        minWidth: 150,
        flex: "1 1 150px",
      }}
    >
      <div style={{ color: "#888", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, marginTop: 4 }}>{value}</div>
      {hint && <div style={{ color: "#777", fontSize: 12 }}>{hint}</div>}
    </div>
  );
}

function statusColor(status: string) {
  if (status === "succeeded") return { bg: "#14532d", fg: "#bbf7d0" };
  if (status === "failed") return { bg: "#7f1d1d", fg: "#fecaca" };
  return { bg: "#374151", fg: "#e5e7eb" };
}

export default function ObservabilityPage() {
  const [summary, setSummary] = useState<ObservabilitySummary | null>(null);
  const [runs, setRuns] = useState<AiRunRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const [s, r] = await Promise.all([fetchObservabilitySummary(720), fetchAiRuns(50)]);
    setSummary(s);
    setRuns(r.runs);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: "2rem", maxWidth: 1000, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 4 }}>Observability</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Every LLM call this system has made, logged to <code>ai_runs</code> since Phase 2.{" "}
        <Link href="/review">Review queue</Link>
      </p>

      {error && <p style={{ color: "#991b1b" }}>Error: {error}</p>}
      {!summary && !error && <p>Loading…</p>}

      {summary && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
            {/* 30 days matches the fetchObservabilitySummary(720) call above;
                the API's own default window is 24h, so these must stay in step. */}
            <Stat label="Total calls" value={String(summary.total_calls)} hint="last 30 days" />
            <Stat
              label="Success rate"
              value={summary.success_rate === null ? "—" : `${(summary.success_rate * 100).toFixed(1)}%`}
              hint={`${summary.total_failed} failed`}
            />
            <Stat label="Agents" value={String(summary.by_agent.length)} />
            <Stat
              label="Models"
              value={summary.by_model.map((m) => m.model ?? "unknown").join(", ") || "—"}
            />
          </div>

          <button onClick={() => load().catch((e) => setError(e.message))} style={{ marginBottom: 18 }}>
            Refresh
          </button>

          <h2 style={{ fontSize: 18, marginBottom: 8 }}>By agent</h2>
          <div style={{ overflowX: "auto", marginBottom: 24 }}>
            <table style={{ borderCollapse: "collapse", fontSize: 14, width: "100%" }}>
              <thead>
                <tr style={{ color: "#888", textAlign: "left" }}>
                  <th style={{ padding: "6px 12px 6px 0" }}>Agent</th>
                  <th style={{ padding: "6px 12px", textAlign: "right" }}>Calls</th>
                  <th style={{ padding: "6px 12px", textAlign: "right" }}>Failed</th>
                  <th style={{ padding: "6px 12px", textAlign: "right" }}>Success</th>
                  <th style={{ padding: "6px 12px", textAlign: "right" }}>Avg latency</th>
                  <th style={{ padding: "6px 12px", textAlign: "right" }}>Max latency</th>
                </tr>
              </thead>
              <tbody>
                {summary.by_agent.map((a) => (
                  <tr key={a.agent_name} style={{ borderTop: "1px solid #333" }}>
                    <td style={{ padding: "6px 12px 6px 0" }}>{a.agent_name}</td>
                    <td style={{ padding: "6px 12px", textAlign: "right" }}>{a.calls}</td>
                    <td
                      style={{
                        padding: "6px 12px",
                        textAlign: "right",
                        color: a.failed > 0 ? "#fca5a5" : "#666",
                      }}
                    >
                      {a.failed}
                    </td>
                    <td style={{ padding: "6px 12px", textAlign: "right" }}>
                      {a.success_rate === null ? "—" : `${(a.success_rate * 100).toFixed(0)}%`}
                    </td>
                    <td style={{ padding: "6px 12px", textAlign: "right" }}>
                      {a.avg_latency_ms === null ? "—" : `${Math.round(a.avg_latency_ms)} ms`}
                    </td>
                    <td style={{ padding: "6px 12px", textAlign: "right", color: "#999" }}>
                      {a.max_latency_ms === null ? "—" : `${Math.round(a.max_latency_ms)} ms`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div
            style={{
              border: "1px solid #3f3f46",
              background: "#18181b",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 22,
              fontSize: 13,
              color: "#a1a1aa",
            }}
          >
            <strong>What isn’t here:</strong> token counts and cost are{" "}
            <em>not recorded</em> — <code>llm_client</code> has never captured them, so this page
            cannot show them ({summary.not_logged.join(", ")}). Latency is computed from{" "}
            <code>completed_at − started_at</code>, not stored as a column.
          </div>
        </>
      )}

      <h2 style={{ fontSize: 18, marginBottom: 8 }}>Recent calls</h2>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", fontSize: 13, width: "100%" }}>
          <thead>
            <tr style={{ color: "#888", textAlign: "left" }}>
              <th style={{ padding: "6px 12px 6px 0" }}>When</th>
              <th style={{ padding: "6px 12px" }}>Agent</th>
              <th style={{ padding: "6px 12px" }}>Status</th>
              <th style={{ padding: "6px 12px", textAlign: "right" }}>Latency</th>
              <th style={{ padding: "6px 12px" }}>Model</th>
              <th style={{ padding: "6px 12px" }}>Prompt</th>
            </tr>
          </thead>
          <tbody>
            {runs?.map((r) => {
              const c = statusColor(r.status);
              return (
                <tr key={r.id} style={{ borderTop: "1px solid #2a2a2a" }}>
                  <td style={{ padding: "6px 12px 6px 0", color: "#999", whiteSpace: "nowrap" }}>
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "6px 12px" }}>{r.agent_name}</td>
                  <td style={{ padding: "6px 12px" }}>
                    <span
                      style={{
                        background: c.bg,
                        color: c.fg,
                        borderRadius: 4,
                        padding: "1px 7px",
                        fontSize: 12,
                      }}
                    >
                      {r.status}
                    </span>
                    {r.error_message && (
                      <div style={{ color: "#fca5a5", fontSize: 12, marginTop: 2 }}>
                        {r.error_message.slice(0, 90)}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "6px 12px", textAlign: "right" }}>
                    {r.latency_ms === null ? "—" : `${Math.round(r.latency_ms)} ms`}
                  </td>
                  <td style={{ padding: "6px 12px", color: "#999" }}>{r.model ?? "—"}</td>
                  <td style={{ padding: "6px 12px", color: "#999" }}>{r.prompt_version ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {runs && runs.length === 0 && <p>No LLM calls recorded yet.</p>}
      </div>
    </main>
  );
}
