"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  fetchBrands,
  fetchLeads,
  generateLeads,
  fetchLiveSingaporeBusinesses,
  Lead,
  OutreachDraft,
  LiveOsmBusiness,
} from "@/lib/api";

const COMPONENT_LABELS: Record<string, string> = {
  category: "Business category match",
  size: "Company size (employees)",
  location: "Location relevance",
  signals: "Active intent signals",
};

function OutreachBadge({ outreach }: { outreach: OutreachDraft | null }) {
  if (!outreach) {
    return <span style={{ color: "#94a3b8", fontSize: 12 }}>no draft</span>;
  }
  const statusColors: Record<string, { bg: string; fg: string; border: string }> = {
    pending_review: { bg: "#fffbeb", fg: "#b45309", border: "#fde68a" },
    approved: { bg: "#ecfdf5", fg: "#047857", border: "#a7f3d0" },
    rejected: { bg: "#fef2f2", fg: "#b91c1c", border: "#fecaca" },
  };
  const style = statusColors[outreach.status] ?? { bg: "#f1f5f9", fg: "#475569", border: "#cbd5e1" };

  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
      <span
        style={{
          background: style.bg,
          color: style.fg,
          border: `1px solid ${style.border}`,
          padding: "2px 8px",
          borderRadius: 4,
          fontSize: 11,
          fontWeight: 700,
        }}
      >
        draft: {outreach.status}
      </span>
      {outreach.content_version_id && (
        <Link href={`/review/${outreach.content_version_id}`} style={{ color: "#0066cc", fontSize: 12, fontWeight: 600 }}>
          open in review →
        </Link>
      )}
    </span>
  );
}

function ScoreBreakdown({ lead }: { lead: Lead }) {
  const b = lead.score_breakdown;
  if (!b) return null;

  return (
    <div style={{ marginTop: 10, fontSize: 13, background: "#f8fafc", padding: 12, borderRadius: 6, border: "1px solid #e2e8f0" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <tbody>
          {Object.entries(b.components).map(([name, comp]) => (
            <tr key={name}>
              <td style={{ padding: "3px 0", color: "#64748b" }}>
                {COMPONENT_LABELS[name] ?? name}
              </td>
              <td style={{ padding: "3px 6px", textAlign: "right", color: "#0f172a" }}>{comp.value}</td>
              <td style={{ padding: "3px 6px", color: "#94a3b8" }}>×{comp.weight}</td>
              <td style={{ padding: "3px 6px", textAlign: "right", fontWeight: 600, color: "#0066cc" }}>= {comp.points}</td>
            </tr>
          ))}
          <tr style={{ borderTop: "1px solid #cbd5e1" }}>
            <td style={{ padding: "5px 0", fontWeight: 700, color: "#002b49" }}>Total Fit Score</td>
            <td />
            <td />
            <td style={{ padding: "5px 6px", textAlign: "right", fontWeight: 800, color: "#0066cc" }}>
              {b.raw_total}
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ color: "#64748b", marginTop: 6, fontSize: 11 }}>Formula: {b.formula}</div>
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
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 950, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            🎯 Lead Discovery &amp; Scoring
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Live Singapore business prospecting + deterministic fit scoring + compliance-checked outreach.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
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
              border: brandId === b.brand_id ? "1.5px solid #0066cc" : "1px solid #cbd5e1",
              background: brandId === b.brand_id ? "#0066cc" : "#ffffff",
              color: brandId === b.brand_id ? "#ffffff" : "#334155",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {b.name}
          </button>
        ))}
      </div>

      {/* Tab Switcher */}
      <div style={{ display: "flex", borderBottom: "1px solid #e2e8f0", marginBottom: "1.5rem" }}>
        <button
          onClick={() => setActiveTab("pipeline")}
          style={{
            padding: "10px 20px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "pipeline" ? "3px solid #0066cc" : "none",
            color: activeTab === "pipeline" ? "#0066cc" : "#64748b",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          📊 Scored Pipeline &amp; Outreach
        </button>
        <button
          onClick={() => setActiveTab("osm_live")}
          style={{
            padding: "10px 20px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "osm_live" ? "3px solid #0066cc" : "none",
            color: activeTab === "osm_live" ? "#0066cc" : "#64748b",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          🗺️ Live Singapore OSM Discovery
        </button>
      </div>

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: "6px", border: "1px solid #fecaca", marginBottom: 16 }}>Error: {error}</div>}

      {/* TAB 1: Pipeline */}
      {activeTab === "pipeline" && (
        <>
          <div
            style={{
              border: "1px solid #e2e8f0",
              background: "#ffffff",
              borderRadius: 8,
              padding: "12px 16px",
              marginBottom: 18,
              fontSize: 13,
              color: "#334155",
              boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
            }}
          >
            <strong style={{ color: "#002b49" }}>Deterministic Scoring:</strong> Prospects are scored via explicit formula without hallucinated numbers. Outreach drafts pass through the 4-step compliance gate.
          </div>

          <button
            onClick={onGenerate}
            disabled={busy || !brandId}
            style={{
              marginBottom: 18,
              padding: "10px 20px",
              borderRadius: 6,
              background: busy ? "#94a3b8" : "#0066cc",
              color: "white",
              fontWeight: 700,
              border: "none",
              cursor: busy ? "not-allowed" : "pointer",
            }}
          >
            {busy ? "Generating Leads..." : "⚡ Generate Scored Leads + Outreach"}
          </button>

          {!leads && !error && <p style={{ color: "#64748b" }}>Loading leads…</p>}

          {leads?.map((lead) => (
            <div
              key={lead.lead_id}
              style={{
                border: "1px solid #e2e8f0",
                background: "#ffffff",
                borderRadius: 8,
                padding: "16px 18px",
                marginBottom: 14,
                boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <strong style={{ fontSize: "1.1rem", color: "#002b49" }}>{lead.company_name}</strong>
                <span style={{ fontSize: 20, fontWeight: 800, color: "#0066cc" }}>{lead.fit_score}</span>
              </div>
              <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>
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
                    color: "#334155",
                    fontSize: 13,
                    fontStyle: "italic",
                    margin: "10px 0 0",
                    borderLeft: "3px solid #0066cc",
                    paddingLeft: 10,
                    background: "#f8fafc",
                    padding: "8px 10px",
                    borderRadius: "0 4px 4px 0",
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
              border: "1px solid #bfdbfe",
              background: "#eff6ff",
              borderRadius: 8,
              padding: "12px 16px",
              marginBottom: 18,
              fontSize: 13,
              color: "#1e40af",
            }}
          >
            <strong>🌐 Live OpenStreetMap (Singapore):</strong> Real registered commercial entities queried live via Overpass API for this vertical.
          </div>

          {osmLoading ? (
            <div style={{ color: "#64748b", padding: "2rem", textAlign: "center" }}>
              Querying Singapore Overpass nodes for commercial entities...
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
              {osmResults.map((biz) => (
                <div
                  key={biz.id}
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    padding: "14px",
                    boxShadow: "0 1px 3px rgba(0, 43, 73, 0.04)",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#002b49", fontSize: "1rem", marginBottom: 4 }}>
                    {biz.name}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "#0066cc", fontWeight: 600, marginBottom: 4 }}>
                    🏢 {biz.category}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "#475569", marginBottom: 4 }}>
                    📍 {biz.address}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: 6 }}>
                    📞 {biz.phone}
                  </div>
                  {biz.website && (
                    <a
                      href={biz.website}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: "0.8rem", color: "#0066cc", wordBreak: "break-all" }}
                    >
                      🔗 {biz.website}
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
