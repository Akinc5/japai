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
        border: "1px solid #e2e8f0",
        background: "#ffffff",
        borderRadius: 8,
        padding: "14px 18px",
        minWidth: 160,
        flex: "1 1 160px",
        boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
      }}
    >
      <div style={{ color: "#64748b", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5, fontWeight: 700 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, marginTop: 4, color: "#002b49" }}>{value}</div>
      {hint && <div style={{ color: "#94a3b8", fontSize: 12, marginTop: 2 }}>{hint}</div>}
    </div>
  );
}

function statusColor(status: string) {
  if (status === "succeeded") return { bg: "#ecfdf5", fg: "#047857", border: "#a7f3d0" };
  if (status === "failed") return { bg: "#fef2f2", fg: "#b91c1c", border: "#fecaca" };
  return { bg: "#f1f5f9", fg: "#475569", border: "#cbd5e1" };
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
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 1000, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            🔍 System Observability
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Full telemetry for every LLM invocation, agent latency, and deterministic audit trail.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", marginBottom: 14 }}>Error: {error}</div>}
      {!summary && !error && <p style={{ color: "#64748b" }}>Loading telemetry summary…</p>}

      {summary && (
        <>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
            <Stat label="Total calls" value={String(summary.total_calls)} hint="last 30 days" />
            <Stat
              label="Success rate"
              value={summary.success_rate === null ? "—" : `${(summary.success_rate * 100).toFixed(1)}%`}
              hint={`${summary.total_failed} failed`}
            />
            <Stat label="Agents active" value={String(summary.by_agent?.length || 0)} />
            <Stat
              label="Model Family"
              value={summary.by_model?.map((m) => m.model ?? "unknown").join(", ") || "Gemini / Claude"}
            />
          </div>

          <button
            onClick={() => load().catch((e) => setError(e.message))}
            style={{
              marginBottom: 20,
              padding: "8px 16px",
              background: "#ffffff",
              color: "#0066cc",
              border: "1px solid #cbd5e1",
              borderRadius: 6,
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            🔄 Refresh Telemetry
          </button>

          {/* By Agent Table */}
          <div
            style={{
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: 10,
              padding: "16px 20px",
              marginBottom: 24,
              boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
            }}
          >
            <h2 style={{ fontSize: 16, fontWeight: 800, color: "#002b49", margin: "0 0 12px" }}>
              Agent Telemetry &amp; Latencies
            </h2>
            <div style={{ overflowX: "auto" }}>
              <table style={{ borderCollapse: "collapse", fontSize: 13, width: "100%" }}>
                <thead>
                  <tr style={{ color: "#64748b", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
                    <th style={{ padding: "8px 12px 8px 0", fontWeight: 700 }}>Agent</th>
                    <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Calls</th>
                    <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Failed</th>
                    <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Success Rate</th>
                    <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Avg Latency</th>
                    <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Max Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(summary.by_agent) && summary.by_agent.map((a) => (
                    <tr key={a.agent_name} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "10px 12px 10px 0", fontWeight: 600, color: "#002b49" }}>{a.agent_name}</td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: "#334155" }}>{a.calls}</td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: a.failed > 0 ? "#dc2626" : "#64748b",
                          fontWeight: a.failed > 0 ? 700 : 400,
                        }}
                      >
                        {a.failed}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: "#047857", fontWeight: 600 }}>
                        {a.success_rate === null ? "—" : `${(a.success_rate * 100).toFixed(0)}%`}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: "#334155" }}>
                        {a.avg_latency_ms === null ? "—" : `${Math.round(a.avg_latency_ms)} ms`}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right", color: "#64748b" }}>
                        {a.max_latency_ms === null ? "—" : `${Math.round(a.max_latency_ms)} ms`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div
            style={{
              border: "1px solid #bfdbfe",
              background: "#eff6ff",
              borderRadius: 8,
              padding: "12px 16px",
              marginBottom: 24,
              fontSize: 13,
              color: "#1e40af",
            }}
          >
            <strong>Telemetry Note:</strong> All LLM invocations record end-to-end execution timestamps, model parameters, and raw policy outputs.
          </div>
        </>
      )}

      {/* Recent Calls Table */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: 10,
          padding: "16px 20px",
          boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
        }}
      >
        <h2 style={{ fontSize: 16, fontWeight: 800, color: "#002b49", margin: "0 0 12px" }}>
          Recent AI Invocations
        </h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", fontSize: 13, width: "100%" }}>
            <thead>
              <tr style={{ color: "#64748b", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>
                <th style={{ padding: "8px 12px 8px 0", fontWeight: 700 }}>Timestamp</th>
                <th style={{ padding: "8px 12px", fontWeight: 700 }}>Agent</th>
                <th style={{ padding: "8px 12px", fontWeight: 700 }}>Status</th>
                <th style={{ padding: "8px 12px", textAlign: "right", fontWeight: 700 }}>Latency</th>
                <th style={{ padding: "8px 12px", fontWeight: 700 }}>Model</th>
                <th style={{ padding: "8px 12px", fontWeight: 700 }}>Prompt Version</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(runs) && runs.map((r) => {
                const c = statusColor(r.status);
                return (
                  <tr key={r.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "10px 12px 10px 0", color: "#64748b", whiteSpace: "nowrap" }}>
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "10px 12px", fontWeight: 600, color: "#002b49" }}>{r.agent_name}</td>
                    <td style={{ padding: "10px 12px" }}>
                      <span
                        style={{
                          background: c.bg,
                          color: c.fg,
                          border: `1px solid ${c.border}`,
                          borderRadius: 4,
                          padding: "2px 8px",
                          fontSize: 11,
                          fontWeight: 700,
                        }}
                      >
                        {r.status}
                      </span>
                      {r.error_message && (
                        <div style={{ color: "#dc2626", fontSize: 11, marginTop: 3 }}>
                          {r.error_message.slice(0, 90)}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "10px 12px", textAlign: "right", color: "#334155" }}>
                      {r.latency_ms === null ? "—" : `${Math.round(r.latency_ms)} ms`}
                    </td>
                    <td style={{ padding: "10px 12px", color: "#64748b" }}>{r.model ?? "—"}</td>
                    <td style={{ padding: "10px 12px", color: "#64748b" }}>{r.prompt_version ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {runs && runs.length === 0 && <p style={{ color: "#64748b", padding: "1rem 0" }}>No LLM calls recorded yet.</p>}
        </div>
      </div>
    </main>
  );
}
