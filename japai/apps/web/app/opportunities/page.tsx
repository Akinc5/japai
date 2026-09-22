"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
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
    <div style={{ marginTop: 10, fontSize: 13 }}>
      <table style={{ borderCollapse: "collapse" }}>
        <tbody>
          {rows.map(([label, signal, weight, points]) => (
            <tr key={label}>
              <td style={{ padding: "2px 12px 2px 0", color: "#999" }}>{label}</td>
              <td style={{ padding: "2px 6px", textAlign: "right" }}>{signal}</td>
              <td style={{ padding: "2px 6px", color: "#777" }}>{weight}</td>
              <td style={{ padding: "2px 6px", textAlign: "right" }}>= {points}</td>
            </tr>
          ))}
          <tr style={{ borderTop: "1px solid #444" }}>
            <td style={{ padding: "4px 12px 2px 0" }}>
              <strong>Total</strong>
            </td>
            <td />
            <td />
            <td style={{ padding: "4px 6px 2px", textAlign: "right" }}>
              <strong>{b.raw_total}</strong>
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ color: "#777", marginTop: 4 }}>
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
    fetch(`${API_BASE_URL}/brands`)
      .then((r) => r.json())
      .then((bs) => {
        const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
        if (jade) setBrandId(jade.brand_id);
        else setError("No brands found");
      })
      .catch((e) => setError(e.message));
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
    <main style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 4 }}>Opportunities</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Scored deterministically from competitor research. Every number below is the
        actual input to the score — <Link href="/review">go to review queue</Link>.
      </p>

      {error && <p style={{ color: "#991b1b" }}>Error: {error}</p>}

      {result && (
        <div
          style={{
            border: "1px solid #166534",
            background: "#052e16",
            borderRadius: 8,
            padding: "12px 16px",
            marginBottom: 20,
          }}
        >
          <strong>Campaign created: {result.campaign_name}</strong>
          <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
            {result.assets.map((a) => (
              <li key={a.content_version_id}>
                {a.content_format} ({a.platform}) — {a.risk_level}, status {a.status}{" "}
                {a.status === "submitted_for_review" && (
                  <Link href={`/review/${a.content_version_id}`}>open in review →</Link>
                )}
              </li>
            ))}
          </ul>
          {result.brief_compliance_warnings && result.brief_compliance_warnings.length > 0 && (
            <p style={{ color: "#fca5a5", marginBottom: 0 }}>
              Brief compliance warnings:{" "}
              {result.brief_compliance_warnings.map((w) => `${w.field}: "${w.term}"`).join("; ")}
            </p>
          )}
        </div>
      )}

      {!items && !error && <p>Loading…</p>}
      {items && items.length === 0 && (
        <p>No suggested opportunities. Run research, then POST /opportunities/generate.</p>
      )}

      {items?.map((o) => (
        <div
          key={o.opportunity_id}
          style={{ border: "1px solid #333", borderRadius: 8, padding: "14px 16px", marginBottom: 14 }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <strong>{o.title}</strong>
            <span style={{ fontSize: 20, fontWeight: 700 }}>{o.score}</span>
          </div>
          <div style={{ color: "#888", fontSize: 13 }}>{o.opportunity_type}</div>
          {o.rationale && <p style={{ marginBottom: 6 }}>{o.rationale}</p>}
          {o.suggested_angle && (
            <p style={{ color: "#bbb", fontStyle: "italic", margin: "0 0 6px" }}>
              Angle: {o.suggested_angle}
            </p>
          )}
          <div style={{ fontSize: 13, color: "#999" }}>
            Formats: {o.suggested_formats.join(", ")} · {o.source_chunk_ids.length} source chunk(s)
          </div>
          <ScoreBreakdown o={o} />
          <button
            disabled={busy !== null}
            onClick={() => onGenerate(o.opportunity_id)}
            style={{ marginTop: 12 }}
          >
            {busy === o.opportunity_id ? "Generating…" : "Generate Campaign"}
          </button>
        </div>
      ))}
    </main>
  );
}
