"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
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
    <div style={{ marginTop: 10, fontSize: 13 }}>
      <div style={{ color: "#777", marginBottom: 4 }}>
        Derived from (avg {insight.derived_from?.primary_metric ?? "engagement_rate"} by {dim}):
      </div>
      <table style={{ borderCollapse: "collapse" }}>
        <tbody>
          {rows.map((r) => (
            <tr key={r.bucket}>
              <td style={{ padding: "2px 12px 2px 0", color: "#999" }}>{r.bucket}</td>
              <td style={{ padding: "2px 8px", textAlign: "right" }}>{r.avg_engagement_rate}%</td>
              <td style={{ padding: "2px 8px", color: "#777" }}>n={r.posts}</td>
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
    fetch(`${API_BASE_URL}/brands`)
      .then((r) => r.json())
      .then((bs) => {
        if (Array.isArray(bs)) {
          const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
          if (jade) setBrandId(jade.brand_id);
          else setError("No brands found");
        } else {
          setError("Failed to load brands from API");
        }
      })
      .catch((e) => setError(e.message));
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
    <main style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 4 }}>Performance Insights</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Patterns found in engagement data, fed back into content generation. See the{" "}
        <Link href="/review">review queue</Link>.
      </p>

      <div
        style={{
          border: "1px solid #7f1d1d",
          background: "#1c0a0a",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 18,
          fontSize: 13,
          color: "#fecaca",
        }}
      >
        <strong>⚠ Simulated data — these are not real engagement numbers.</strong>
        <div style={{ marginTop: 4 }}>
          {data?.simulated_note ??
            "All engagement data in this system is fabricated seed data (analytics.is_simulated = true). No real performance data exists."}{" "}
          Nothing has ever been posted to a real platform — the publishing worker runs in
          simulation mode. The analysis loop is real; the inputs are invented.
        </div>
      </div>

      {error && <p style={{ color: "#991b1b" }}>Error: {error}</p>}

      <button onClick={onAnalyze} disabled={busy || !brandId} style={{ marginBottom: 18 }}>
        {busy ? "Analyzing… (1 LLM call)" : "Run Analysis"}
      </button>

      {!data && !error && <p>Loading…</p>}
      {data && data.insights.length === 0 && (
        <p>
          No insights yet. Seed simulated analytics, then click “Run Analysis” or POST
          /optimization/analyze.
        </p>
      )}

      {data?.insights.map((insight) => (
        <div
          key={insight.insight_id}
          style={{
            border: "1px solid #333",
            borderRadius: 8,
            padding: "14px 16px",
            marginBottom: 14,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <strong>{insight.insight_text}</strong>
            <span
              style={{
                fontSize: 12,
                color: "#bbb",
                background: "#27272a",
                borderRadius: 4,
                padding: "2px 8px",
                whiteSpace: "nowrap",
                marginLeft: 12,
              }}
            >
              {TYPE_LABELS[insight.insight_type ?? ""] ?? insight.insight_type}
            </span>
          </div>

          {insight.supporting_metric && (
            <div style={{ marginTop: 8, fontSize: 14 }}>
              <span style={{ color: "#888" }}>Supporting metric: </span>
              <code style={{ color: "#86efac" }}>{insight.supporting_metric}</code>
            </div>
          )}

          {insight.recommendation && (
            <p
              style={{
                margin: "8px 0 0",
                paddingLeft: 10,
                borderLeft: "2px solid #444",
                color: "#ddd",
              }}
            >
              <strong style={{ color: "#999" }}>Recommendation: </strong>
              {insight.recommendation}
            </p>
          )}

          <EvidenceTable insight={insight} />
        </div>
      ))}
    </main>
  );
}
