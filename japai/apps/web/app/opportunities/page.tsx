"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  fetchBrands,
  fetchOpportunities,
  generateCampaign,
  CampaignResult,
  Opportunity,
} from "@/lib/api";

function ScoreBreakdown({ o }: { o: Opportunity }) {
  const b = o.score_breakdown;
  if (!b) return null;
  const rows = [
    ["Competitor mentions", b.competitor_mentions, `×10`, b.competitor_mentions_points],
    ["Recency weight", b.recency_weight, `×20`, b.recency_points],
    ["Coverage match", b.coverage_match, `×30`, b.coverage_points],
  ] as const;

  return (
    <div style={{ marginTop: 10, fontSize: 13, background: "#f8fafc", padding: 12, borderRadius: 6, border: "1px solid #e2e8f0" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {rows.map(([label, signal, weight, points]) => (
            <tr key={label}>
              <td style={{ padding: "3px 0", color: "#64748b" }}>{label}</td>
              <td style={{ padding: "3px 6px", textAlign: "right", color: "#0f172a" }}>{signal}</td>
              <td style={{ padding: "3px 6px", color: "#94a3b8" }}>{weight}</td>
              <td style={{ padding: "3px 6px", textAlign: "right", fontWeight: 600, color: "#0066cc" }}>= {points}</td>
            </tr>
          ))}
          <tr style={{ borderTop: "1px solid #cbd5e1" }}>
            <td style={{ padding: "5px 0", fontWeight: 700, color: "#002b49" }}>Total Score</td>
            <td />
            <td />
            <td style={{ padding: "5px 6px", textAlign: "right", fontWeight: 800, color: "#0066cc" }}>
              {b.raw_total}
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ color: "#64748b", marginTop: 6, fontSize: 11 }}>
        {b.formula}
        {b.matched_keywords && b.matched_keywords.length > 0 && <> · matched: {b.matched_keywords.join(", ")}</>}
      </div>
    </div>
  );
}

export default function OpportunitiesPage() {
  const [brandId, setBrandId] = useState<string | null>(null);
  const [items, setItems] = useState<Opportunity[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [result, setResult] = useState<CampaignResult | null>(null);

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
    fetchOpportunities(brandId)
      .then(setItems)
      .catch((e) => setError(e.message));
  }, [brandId]);

  async function onGenerate(id: string) {
    setBusy(id);
    setError(null);
    setResult(null);
    try {
      const res = await generateCampaign(id);
      setResult(res);
      if (brandId) setItems(await fetchOpportunities(brandId));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 900, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            💡 Market Opportunities
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Deterministic trend scoring derived from competitor intelligence &amp; research.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", marginBottom: 14 }}>Error: {error}</div>}

      {result && (
        <div
          style={{
            border: "1px solid #a7f3d0",
            background: "#ecfdf5",
            borderRadius: 8,
            padding: "14px 18px",
            marginBottom: 20,
            color: "#047857",
          }}
        >
          <strong>Campaign created: {result.campaign_name}</strong>
          <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
            {result.assets.map((a) => (
              <li key={a.content_version_id}>
                {a.content_format} ({a.platform}) — {a.risk_level}, status {a.status}{" "}
                {a.status === "submitted_for_review" && (
                  <Link href={`/review/${a.content_version_id}`} style={{ color: "#0066cc", fontWeight: 600 }}>open in review →</Link>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!items && !error && <p style={{ color: "#64748b" }}>Loading opportunities…</p>}
      {items && items.length === 0 && (
        <div style={{ background: "#ffffff", padding: "2rem", textAlign: "center", borderRadius: 8, border: "1px solid #e2e8f0", color: "#64748b" }}>
          No suggested opportunities on file.
        </div>
      )}

      {items?.map((o) => (
        <div
          key={o.opportunity_id}
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 8,
            padding: "16px 18px",
            marginBottom: 14,
            background: "#ffffff",
            boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <strong style={{ fontSize: "1.1rem", color: "#002b49" }}>{o.title}</strong>
            <span style={{ fontSize: 20, fontWeight: 800, color: "#0066cc" }}>{o.score}</span>
          </div>
          <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>Type: {o.opportunity_type}</div>
          {o.rationale && <p style={{ margin: "8px 0", color: "#334155", fontSize: 14 }}>{o.rationale}</p>}
          {o.suggested_angle && (
            <p style={{ color: "#0066cc", fontStyle: "italic", margin: "0 0 8px", fontSize: 13 }}>
              Angle: {o.suggested_angle}
            </p>
          )}
          <ScoreBreakdown o={o} />
          <button
            disabled={busy !== null}
            onClick={() => onGenerate(o.opportunity_id)}
            style={{
              marginTop: 12,
              padding: "8px 16px",
              borderRadius: 6,
              background: busy === o.opportunity_id ? "#94a3b8" : "#0066cc",
              color: "white",
              fontWeight: 700,
              fontSize: 13,
              border: "none",
              cursor: busy === o.opportunity_id ? "not-allowed" : "pointer",
            }}
          >
            {busy === o.opportunity_id ? "Generating Campaign…" : "⚡ Generate Campaign Assets"}
          </button>
        </div>
      ))}
    </main>
  );
}
