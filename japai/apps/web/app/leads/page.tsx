"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  fetchLeads,
  generateLeads,
  fetchLiveSingaporeBusinesses,
  Lead,
  LeadOutreach,
  LiveOsmBusiness,
} from "@/lib/api";

const COMPONENT_LABELS: Record<string, string> = {
  category_match: "Category match",
  size_fit: "Size fit",
  location_match: "Location match",
  signal_bonus: "Signal bonus",
};

function OutreachBadge({ outreach }: { outreach: LeadOutreach | null }) {
  if (!outreach) {
    return <span style={{ color: "#888", fontSize: 13 }}>No outreach drafted</span>;
  }

  const palette: Record<string, { bg: string; fg: string; label: string }> = {
    submitted_for_review: { bg: "#78350f", fg: "#fde68a", label: "Pending review" },
    approved: { bg: "#14532d", fg: "#bbf7d0", label: "Approved" },
    rejected: { bg: "#7f1d1d", fg: "#fecaca", label: "Rejected by compliance" },
    draft: { bg: "#1e3a5f", fg: "#bfdbfe", label: "Draft" },
  };
  const style = palette[outreach.status] ?? { bg: "#374151", fg: "#e5e7eb", label: outreach.status };

  return (
    <span style={{ display: "inline-flex", gap: 8, alignItems: "center", fontSize: 13 }}>
      <span
        style={{
          background: style.bg,
          color: style.fg,
          borderRadius: 4,
          padding: "2px 8px",
          fontWeight: 600,
        }}
      >
        {style.label}
      </span>
      {outreach.risk_level && <span style={{ color: "#999" }}>risk: {outreach.risk_level}</span>}
      {outreach.status === "submitted_for_review" && (
        <Link href={`/review/${outreach.content_version_id}`}>open in review →</Link>
      )}
    </span>
  );
}

function ScoreBreakdown({ lead }: { lead: Lead }) {
  const b = lead.score_breakdown;
  if (!b) return null;

  return (
    <div style={{ marginTop: 10, fontSize: 13 }}>
      <table style={{ borderCollapse: "collapse" }}>
        <tbody>
          {Object.entries(b.components).map(([name, comp]) => (
            <tr key={name}>
              <td style={{ padding: "2px 12px 2px 0", color: "#999" }}>
                {COMPONENT_LABELS[name] ?? name}
              </td>
              <td style={{ padding: "2px 6px", textAlign: "right" }}>{comp.value}</td>
              <td style={{ padding: "2px 6px", color: "#777" }}>×{comp.weight}</td>
              <td style={{ padding: "2px 6px", textAlign: "right" }}>= {comp.points}</td>
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
      <div style={{ color: "#777", marginTop: 4 }}>{b.formula}</div>
    </div>
  );
}

export default function LeadsPage() {
  const [brands, setBrands] = useState<any[]>([]);
  const [brandId, setBrandId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"pipeline" | "osm_live">("pipeline");
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [osmResults, setOsmResults] = useState<LiveOsmBusiness[]>([]);
  const [osmLoading, setOsmLoading] = useState(false);
  const [formula, setFormula] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE_URL}/brands`)
      .then((r) => r.json())
      .then((bs) => {
        if (Array.isArray(bs)) {
          setBrands(bs);
          const jade = bs.find((b: any) => b.slug === "jade") ?? bs[0];
          if (jade) setBrandId(jade.brand_id);
          else setError("No brands found");
        } else {
          setError("Failed to load brands from API");
        }
      })
      .catch((e) => setError(e.message));
  }, []);

  async function load(id: string) {
    const res = await fetchLeads(id);
    setLeads(res.leads);
    setFormula(res.formula);
  }

  async function loadOsm(id: string) {
    setOsmLoading(true);
    try {
      const res = await fetchLiveSingaporeBusinesses(id, 12);
      setOsmResults(res.results || []);
    } catch (e: any) {
      setError("OSM query failed: " + e.message);
    } finally {
      setOsmLoading(false);
    }
  }

  useEffect(() => {
    if (!brandId) return;
    if (activeTab === "pipeline") {
      load(brandId).catch((e) => setError(e.message));
    } else {
      loadOsm(brandId);
    }
  }, [brandId, activeTab]);

  async function onGenerate() {
    if (!brandId) return;
    setBusy(true);
    setError(null);
    try {
      await generateLeads(brandId, 3);
      await load(brandId);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ padding: "2.5rem", maxWidth: 950, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ marginBottom: 4, color: "#f8fafc" }}>🎯 Lead Discovery & Scoring</h1>
          <p style={{ color: "#94a3b8", marginTop: 0 }}>
            Live Singapore business prospecting + deterministic fit scoring + compliance-checked outreach.
          </p>
        </div>
        <Link href="/" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Back to OS Hub
        </Link>
      </header>

      {/* Brand Selector */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "1.5rem" }}>
        {brands.map((b) => (
          <button
            key={b.brand_id}
            onClick={() => setBrandId(b.brand_id)}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: brandId === b.brand_id ? "2px solid #38bdf8" : "1px solid #334155",
              background: brandId === b.brand_id ? "#0f172a" : "#1e293b",
              color: "#f8fafc",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {b.name}
          </button>
        ))}
      </div>

      {/* Tab Switcher */}
      <div style={{ display: "flex", borderBottom: "1px solid #334155", marginBottom: "1.5rem" }}>
        <button
          onClick={() => setActiveTab("pipeline")}
          style={{
            padding: "10px 20px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "pipeline" ? "3px solid #38bdf8" : "none",
            color: activeTab === "pipeline" ? "#38bdf8" : "#94a3b8",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          📊 Scored Pipeline & Outreach
        </button>
        <button
          onClick={() => setActiveTab("osm_live")}
          style={{
            padding: "10px 20px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "osm_live" ? "3px solid #38bdf8" : "none",
            color: activeTab === "osm_live" ? "#38bdf8" : "#94a3b8",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          🗺️ Live Singapore OSM Discovery
        </button>
      </div>

      {error && <p style={{ color: "#ef4444", background: "#450a0a", padding: "10px", borderRadius: "6px" }}>Error: {error}</p>}

      {/* TAB 1: Pipeline */}
      {activeTab === "pipeline" && (
        <>
          <div
            style={{
              border: "1px solid #78350f",
              background: "#1c1206",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 18,
              fontSize: 13,
              color: "#fde68a",
            }}
          >
            <strong>Deterministic Arithmetic Scoring:</strong> Prospects are scored via explicit formula without hallucinated numbers. Outreach drafts go through the 4-step compliance gate before human review.
          </div>

          <button
            onClick={onGenerate}
            disabled={busy || !brandId}
            style={{
              marginBottom: 18,
              padding: "10px 20px",
              borderRadius: 6,
              background: "#4f46e5",
              color: "white",
              fontWeight: 700,
              border: "none",
              cursor: "pointer",
            }}
          >
            {busy ? "Generating… (3 LLM calls)" : "⚡ Generate Scored Leads + Outreach"}
          </button>

          {formula && (
            <p style={{ color: "#94a3b8", fontSize: 13, marginTop: 0 }}>
              Scoring Formula: <code>{formula}</code>
            </p>
          )}

          {!leads && !error && <p style={{ color: "#94a3b8" }}>Loading leads…</p>}

          {leads?.map((lead) => (
            <div
              key={lead.lead_id}
              style={{
                border: "1px solid #334155",
                background: "#1e293b",
                borderRadius: 8,
                padding: "14px 16px",
                marginBottom: 14,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <strong style={{ fontSize: "1.1rem", color: "#f8fafc" }}>{lead.company_name}</strong>
                <span style={{ fontSize: 20, fontWeight: 700, color: "#38bdf8" }}>{lead.fit_score}</span>
              </div>
              <div style={{ color: "#94a3b8", fontSize: 13, marginTop: 4 }}>
                {lead.category} · {lead.location}
                {lead.employee_count !== null && <> · {lead.employee_count} staff</>} · source:{" "}
                <code>{lead.source}</code>
              </div>
              <div style={{ marginTop: 8 }}>
                <OutreachBadge outreach={lead.outreach} />
              </div>
              {lead.outreach?.body_preview && (
                <p
                  style={{
                    color: "#cbd5e1",
                    fontSize: 13,
                    fontStyle: "italic",
                    margin: "8px 0 0",
                    borderLeft: "2px solid #38bdf8",
                    paddingLeft: 10,
                  }}
                >
                  &quot;{lead.outreach.body_preview}…&quot;
                </p>
              )}
              <ScoreBreakdown lead={lead} />
            </div>
          ))}
        </>
      )}

      {/* TAB 2: Live OpenStreetMap Singapore */}
      {activeTab === "osm_live" && (
        <div>
          <div
            style={{
              border: "1px solid #0369a1",
              background: "#082f49",
              borderRadius: 8,
              padding: "10px 14px",
              marginBottom: 18,
              fontSize: 13,
              color: "#bae6fd",
            }}
          >
            <strong>🌐 Live OpenStreetMap (Singapore):</strong> Real commercial entities discovered in Singapore for this vertical. (Sharveswar submission integration).
          </div>

          {osmLoading ? (
            <div style={{ color: "#94a3b8", padding: "2rem", textAlign: "center" }}>
              Querying Singapore Overpass nodes for commercial entities...
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
              {osmResults.map((biz) => (
                <div
                  key={biz.id}
                  style={{
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "14px",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#f8fafc", fontSize: "1rem", marginBottom: 4 }}>
                    {biz.name}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#38bdf8", marginBottom: 6 }}>
                    🏢 {biz.category}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#cbd5e1", marginBottom: 4 }}>
                    📍 {biz.address}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: 8 }}>
                    📞 {biz.phone}
                  </div>
                  {biz.website && (
                    <a
                      href={biz.website}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: "0.75rem", color: "#38bdf8" }}
                    >
                      🔗 {biz.website}
                    </a>
                  )}
                  <div style={{ marginTop: 10 }}>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        background: "#0f172a",
                        color: "#94a3b8",
                        padding: "2px 6px",
                        borderRadius: "4px",
                      }}
                    >
                      Source: {biz.source}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
