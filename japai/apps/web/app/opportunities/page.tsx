"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  fetchBrands,
  fetchOpportunities,
  generateOpportunities,
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
    <div style={{ marginTop: 12, fontSize: 13, background: "#f8fafc", padding: "12px 14px", borderRadius: 8, border: "1px solid #e2e8f0" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {rows.map(([label, signal, weight, points]) => (
            <tr key={label}>
              <td style={{ padding: "4px 0", color: "#64748b" }}>{label}</td>
              <td style={{ padding: "4px 6px", textAlign: "right", color: "#0f172a", fontWeight: 600 }}>{signal}</td>
              <td style={{ padding: "4px 6px", color: "#94a3b8" }}>{weight}</td>
              <td style={{ padding: "4px 6px", textAlign: "right", fontWeight: 700, color: "#0066cc" }}>= {points}</td>
            </tr>
          ))}
          <tr style={{ borderTop: "1px solid #cbd5e1" }}>
            <td style={{ padding: "6px 0", fontWeight: 700, color: "#002b49" }}>Total Score</td>
            <td />
            <td />
            <td style={{ padding: "6px 6px", textAlign: "right", fontWeight: 800, color: "#0066cc", fontSize: 14 }}>
              {b.raw_total}
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ color: "#64748b", marginTop: 8, fontSize: 11, lineHeight: 1.4 }}>
        <strong>Formula:</strong> {b.formula}
        {b.matched_keywords && b.matched_keywords.length > 0 && (
          <div style={{ marginTop: 4 }}>
            <strong>Keywords:</strong> {b.matched_keywords.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

export default function OpportunitiesPage() {
  const [brands, setBrands] = useState<any[]>([]);
  const [brandId, setBrandId] = useState<string | null>(null);
  const [items, setItems] = useState<Opportunity[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [result, setResult] = useState<CampaignResult | null>(null);

  useEffect(() => {
    fetchBrands()
      .then((bs) => {
        setBrands(bs);
        const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
        if (jade) setBrandId(jade.brand_id);
      })
      .catch((e) => {
        console.warn("fetchBrands error:", e);
      });
  }, []);

  async function loadOpportunities(id: string) {
    try {
      const opps = await fetchOpportunities(id);
      setItems(opps);
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (!brandId) return;
    setItems(null);
    setError(null);
    setResult(null);
    loadOpportunities(brandId);
  }, [brandId]);

  async function onDiscover() {
    if (!brandId) return;
    setDiscovering(true);
    setError(null);
    setResult(null);
    try {
      const generated = await generateOpportunities(brandId);
      if (generated && generated.length > 0) {
        setItems(generated);
      } else {
        await loadOpportunities(brandId);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setDiscovering(false);
    }
  }

  async function onGenerate(id: string) {
    setBusy(id);
    setError(null);
    setResult(null);
    try {
      const res = await generateCampaign(id);
      setResult(res);
      if (brandId) await loadOpportunities(brandId);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 950, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            💡 Market Opportunities
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Deterministic trend &amp; competitor gap scoring derived from regulatory intelligence &amp; research.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      {/* Brand Selector Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {brands.map((b) => (
            <button
              key={b.brand_id}
              onClick={() => setBrandId(b.brand_id)}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: brandId === b.brand_id ? "1.5px solid #0066cc" : "1px solid #cbd5e1",
                background: brandId === b.brand_id ? "#0066cc" : "#ffffff",
                color: brandId === b.brand_id ? "#ffffff" : "#334155",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: 13,
                transition: "all 0.15s ease",
              }}
            >
              {b.name}
            </button>
          ))}
        </div>

        <button
          onClick={onDiscover}
          disabled={discovering || !brandId}
          style={{
            padding: "9px 18px",
            borderRadius: 6,
            background: discovering ? "#94a3b8" : "#0284c7",
            color: "white",
            fontWeight: 700,
            fontSize: 13,
            border: "none",
            cursor: discovering ? "not-allowed" : "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            boxShadow: "0 2px 4px rgba(2, 132, 199, 0.2)",
          }}
        >
          {discovering ? "Discovering Opportunities…" : "⚡ Discover Market Opportunities"}
        </button>
      </div>

      {error && (
        <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "12px 16px", borderRadius: 8, border: "1px solid #fecaca", marginBottom: 16 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div
          style={{
            border: "1px solid #a7f3d0",
            background: "#ecfdf5",
            borderRadius: 8,
            padding: "16px 20px",
            marginBottom: 20,
            color: "#047857",
            boxShadow: "0 2px 5px rgba(4, 120, 87, 0.08)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <strong style={{ fontSize: "1.05rem" }}>🎉 Campaign Created: {result.campaign_name}</strong>
            <span style={{ fontSize: 12, background: "#d1fae5", padding: "3px 8px", borderRadius: 4, fontWeight: 700 }}>
              {result.assets.length} Assets Generated
            </span>
          </div>
          <ul style={{ margin: "10px 0 0", paddingLeft: 20, fontSize: 13, lineHeight: 1.6 }}>
            {result.assets.map((a) => (
              <li key={a.content_version_id}>
                <strong>{a.content_format.replace(/_/g, " ").toUpperCase()}</strong> ({a.platform}) — Risk:{" "}
                <span style={{ fontWeight: 700 }}>{a.risk_level.toUpperCase()}</span>, Status: {a.status}{" "}
                {a.content_version_id && (
                  <Link href={`/review/${a.content_version_id}`} style={{ color: "#0066cc", fontWeight: 700, marginLeft: 6 }}>
                    Open in Human Review Queue →
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!items && !error && (
        <div style={{ padding: "3rem 1rem", textAlign: "center", color: "#64748b" }}>
          <p style={{ margin: 0, fontSize: 14 }}>Loading opportunities from intelligence database…</p>
        </div>
      )}

      {items && items.length === 0 && (
        <div
          style={{
            background: "#ffffff",
            padding: "3rem 2rem",
            textAlign: "center",
            borderRadius: 10,
            border: "1px dashed #cbd5e1",
            color: "#64748b",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: 10 }}>📡</div>
          <h3 style={{ margin: "0 0 8px", color: "#002b49", fontSize: "1.2rem", fontWeight: 700 }}>
            No opportunities generated yet for this brand
          </h3>
          <p style={{ margin: "0 0 1.5rem", fontSize: "0.95rem", color: "#64748b", maxWidth: 500, marginLeft: "auto", marginRight: "auto" }}>
            Run the Opportunity Discovery Engine to scan research signals, competitor gaps, and regulatory changes to score actionable campaigns.
          </p>
          <button
            onClick={onDiscover}
            disabled={discovering}
            style={{
              padding: "10px 22px",
              borderRadius: 6,
              background: discovering ? "#94a3b8" : "#0066cc",
              color: "white",
              fontWeight: 700,
              fontSize: 14,
              border: "none",
              cursor: discovering ? "not-allowed" : "pointer",
              boxShadow: "0 2px 4px rgba(0, 102, 204, 0.2)",
            }}
          >
            {discovering ? "Running AI Discovery..." : "⚡ Run Opportunity Discovery Engine"}
          </button>
        </div>
      )}

      {items?.map((o) => (
        <div
          key={o.opportunity_id}
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 10,
            padding: "18px 20px",
            marginBottom: 16,
            background: "#ffffff",
            boxShadow: "0 1px 4px rgba(0, 43, 73, 0.05)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span
                  style={{
                    background: "#e0f2fe",
                    color: "#0369a1",
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                  }}
                >
                  {o.opportunity_type || "Market Gap"}
                </span>
                <span
                  style={{
                    background: o.status === "executed" ? "#dcfce7" : "#f1f5f9",
                    color: o.status === "executed" ? "#15803d" : "#475569",
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                >
                  {o.status}
                </span>
              </div>
              <h3 style={{ margin: "4px 0 6px", fontSize: "1.2rem", fontWeight: 700, color: "#002b49" }}>
                {o.title}
              </h3>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 24, fontWeight: 900, color: "#0066cc", lineHeight: 1 }}>{o.score}</div>
              <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600, marginTop: 2 }}>PRIORITY SCORE</div>
            </div>
          </div>

          {o.rationale && (
            <p style={{ margin: "8px 0", color: "#334155", fontSize: 14, lineHeight: 1.5 }}>
              {o.rationale}
            </p>
          )}

          {o.suggested_angle && (
            <div
              style={{
                background: "#f0f9ff",
                borderLeft: "3px solid #0284c7",
                padding: "8px 12px",
                borderRadius: "0 6px 6px 0",
                margin: "10px 0",
                fontSize: 13,
                color: "#0369a1",
              }}
            >
              <strong>Suggested Angle:</strong> {o.suggested_angle}
            </div>
          )}

          {o.suggested_formats && o.suggested_formats.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "10px 0" }}>
              <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, alignSelf: "center" }}>Formats:</span>
              {o.suggested_formats.map((fmt) => (
                <span
                  key={fmt}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #cbd5e1",
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    color: "#334155",
                    fontWeight: 600,
                  }}
                >
                  {fmt}
                </span>
              ))}
            </div>
          )}

          <ScoreBreakdown o={o} />

          <div style={{ marginTop: 14, display: "flex", justifyContent: "flex-end" }}>
            <button
              disabled={busy !== null}
              onClick={() => onGenerate(o.opportunity_id)}
              style={{
                padding: "9px 18px",
                borderRadius: 6,
                background: busy === o.opportunity_id ? "#94a3b8" : "#0066cc",
                color: "white",
                fontWeight: 700,
                fontSize: 13,
                border: "none",
                cursor: busy === o.opportunity_id ? "not-allowed" : "pointer",
                boxShadow: "0 2px 4px rgba(0, 102, 204, 0.2)",
              }}
            >
              {busy === o.opportunity_id ? "Generating Campaign Assets…" : "⚡ Generate Campaign Assets"}
            </button>
          </div>
        </div>
      ))}
    </main>
  );
}
