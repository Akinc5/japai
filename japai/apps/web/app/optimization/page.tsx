"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  fetchBrands,
  fetchInsights,
  runAnalysis,
  InsightsResponse,
  PerformanceInsight,
} from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  angle: "Content angle",
  hook_style: "Hook style",
  platform: "Platform",
  volume: "Volume",
  other: "Other",
};

function EvidenceTable({ insight }: { insight: PerformanceInsight }) {
  const groups = insight.derived_from?.groups;
  const dim = insight.insight_type ?? "";
  const rows = groups?.[dim];
  if (!rows || rows.length === 0) return null;

  return (
    <div style={{ marginTop: 10, fontSize: 13, background: "#f8fafc", padding: 12, borderRadius: 6, border: "1px solid #e2e8f0" }}>
      <div style={{ color: "#64748b", marginBottom: 6, fontWeight: 600 }}>
        Derived from (avg {insight.derived_from?.primary_metric ?? "engagement_rate"} by {dim}):
      </div>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {rows.map((r) => (
            <tr key={r.bucket}>
              <td style={{ padding: "3px 0", color: "#334155" }}>{r.bucket}</td>
              <td style={{ padding: "3px 8px", textAlign: "right", fontWeight: 700, color: "#0066cc" }}>{r.avg_engagement_rate}%</td>
              <td style={{ padding: "3px 8px", color: "#94a3b8", textAlign: "right" }}>n={r.posts}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function OptimizationPage() {
  const [brandId, setBrandId] = useState<string | null>(null);
  const [data, setData] = useState<InsightsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchBrands()
      .then((bs) => {
        const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
        if (jade) setBrandId(jade.brand_id);
      })
      .catch((e) => {
        console.warn("fetchBrands error:", e);
      });
  }, []);

  useEffect(() => {
    if (!brandId) return;
    fetchInsights(brandId).then(setData).catch((e) => setError(e.message));
  }, [brandId]);

  async function onAnalyze() {
    if (!brandId) return;
    setBusy(true);
    setError(null);
    try {
      await runAnalysis(brandId);
      setData(await fetchInsights(brandId));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 900, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            📈 Performance Insights &amp; Copy Loops
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Engagement feedback patterns distilled into actionable prompt directives.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", marginBottom: 14 }}>Error: {error}</div>}

      <button
        onClick={onAnalyze}
        disabled={busy || !brandId}
        style={{
          marginBottom: 18,
          padding: "9px 18px",
          borderRadius: 6,
          background: busy ? "#94a3b8" : "#0066cc",
          color: "white",
          fontWeight: 700,
          border: "none",
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        {busy ? "Analyzing Copy Patterns…" : "⚡ Run Engagement Analysis"}
      </button>

      {!data && !error && <p style={{ color: "#64748b" }}>Loading insights…</p>}
      {data && data.insights.length === 0 && (
        <div style={{ background: "#ffffff", padding: "2rem", textAlign: "center", borderRadius: 8, border: "1px solid #e2e8f0", color: "#64748b" }}>
          No insights on file. Click &quot;Run Engagement Analysis&quot; to synthesize patterns.
        </div>
      )}

      {data?.insights.map((insight) => (
        <div
          key={insight.insight_id}
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 8,
            padding: "16px 18px",
            marginBottom: 14,
            background: "#ffffff",
            boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 8 }}>
            <strong style={{ fontSize: "1.05rem", color: "#002b49" }}>{insight.insight_text}</strong>
            <span
              style={{
                fontSize: 11,
                color: "#0066cc",
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: 4,
                padding: "2px 8px",
                fontWeight: 700,
              }}
            >
              {TYPE_LABELS[insight.insight_type ?? ""] ?? insight.insight_type}
            </span>
          </div>

          {insight.supporting_metric && (
            <div style={{ marginTop: 8, fontSize: 13, color: "#64748b" }}>
              Supporting metric: <strong style={{ color: "#0066cc" }}>{insight.supporting_metric}</strong>
            </div>
          )}

          {insight.recommendation && (
            <p
              style={{
                margin: "10px 0 0",
                paddingLeft: 10,
                borderLeft: "3px solid #0066cc",
                color: "#334155",
                fontSize: 13,
                background: "#f8fafc",
                padding: "8px 10px",
                borderRadius: "0 4px 4px 0",
              }}
            >
              <strong style={{ color: "#002b49" }}>Prompt Directive: </strong>
              {insight.recommendation}
            </p>
          )}

          <EvidenceTable insight={insight} />
        </div>
      ))}
    </main>
  );
}
