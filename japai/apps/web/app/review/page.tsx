"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPending, PendingItem } from "@/lib/api";
import RiskBadge from "@/components/RiskBadge";
import LanguageBadge from "@/components/LanguageBadge";
import RejectionRateWidget from "@/components/RejectionRateWidget";

export default function ReviewListPage() {
  const [items, setItems] = useState<PendingItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPending()
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: "2.5rem 1.5rem 4rem", maxWidth: 950, margin: "0 auto" }}>
      <header style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "1.8rem", fontWeight: 800, color: "#002b49" }}>
            🛡️ Compliance Review Queue
          </h1>
          <p style={{ color: "#64748b", margin: 0, fontSize: "0.95rem" }}>
            Content audited by AI Compliance Engine against MAS Guidelines &amp; Insurance Code, newest first.
          </p>
        </div>
        <Link href="/" style={{ color: "#0066cc", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Home
        </Link>
      </header>

      <RejectionRateWidget />

      {error && <div style={{ color: "#b91c1c", background: "#fef2f2", padding: "10px 14px", borderRadius: 6, border: "1px solid #fecaca", margin: "14px 0" }}>Error: {error}</div>}
      {!items && !error && <p style={{ color: "#64748b" }}>Loading queue…</p>}
      {items && items.length === 0 && (
        <div style={{ background: "#ffffff", padding: "3rem 2rem", textAlign: "center", borderRadius: 8, border: "1px dashed #cbd5e1", color: "#64748b" }}>
          <div style={{ fontSize: "2rem", marginBottom: 8 }}>✅</div>
          <h3 style={{ color: "#002b49", margin: "0 0 6px", fontSize: "1.1rem" }}>Queue is all clear</h3>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>No content currently pending compliance review.</p>
        </div>
      )}

      {items && items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {items.map((item) => (
            <Link
              key={item.content_version_id}
              href={`/review/${item.content_version_id}`}
              style={{
                display: "block",
                border: "1px solid #e2e8f0",
                borderRadius: 10,
                padding: "18px 20px",
                textDecoration: "none",
                color: "inherit",
                background: "#ffffff",
                boxShadow: "0 1px 4px rgba(0, 43, 73, 0.04)",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span
                      style={{
                        background: "#f1f5f9",
                        color: "#002b49",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 700,
                        textTransform: "uppercase",
                      }}
                    >
                      {item.brand_name || "JA Assure"}
                    </span>
                    <span style={{ fontSize: 13, color: "#64748b", fontWeight: 600 }}>
                      Platform: <strong style={{ color: "#0f172a" }}>{item.platform || "social"}</strong>
                    </span>
                    {item.status && item.status !== "submitted_for_review" && (
                      <span
                        style={{
                          background: item.status === "approved" ? "#ecfdf5" : "#fef2f2",
                          color: item.status === "approved" ? "#047857" : "#b91c1c",
                          fontSize: 11,
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: 4,
                          textTransform: "uppercase",
                        }}
                      >
                        {item.status}
                      </span>
                    )}
                  </div>
                  {item.title && (
                    <h3 style={{ margin: "2px 0 0", fontSize: "1.05rem", fontWeight: 700, color: "#002b49" }}>
                      {item.title}
                    </h3>
                  )}
                </div>

                <div style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
                  <LanguageBadge language={item.language} isLocalized={item.is_localized} />
                  <RiskBadge riskLevel={item.risk_level} />
                </div>
              </div>

              {/* Compliance Engine Verdict Highlight */}
              {item.compliance_outcome && (
                <div
                  style={{
                    background: item.risk_level === "pass" ? "#f0fdf4" : item.risk_level === "block" ? "#fef2f2" : "#fffbeb",
                    border: `1px solid ${item.risk_level === "pass" ? "#bbf7d0" : item.risk_level === "block" ? "#fecaca" : "#fde68a"}`,
                    borderRadius: 6,
                    padding: "8px 12px",
                    margin: "10px 0",
                    fontSize: 12,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 6,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span>
                      {item.risk_level === "pass" ? "✅" : item.risk_level === "block" ? "🛑" : "⚠️"}
                    </span>
                    <strong style={{ color: item.risk_level === "pass" ? "#166534" : item.risk_level === "block" ? "#991b1b" : "#92400e" }}>
                      Engine Verdict: {item.compliance_outcome.replace(/_/g, " ").toUpperCase()}
                    </strong>
                    {item.compliance_notes && (
                      <span style={{ color: "#475569" }}>— {item.compliance_notes}</span>
                    )}
                  </div>
                  {item.has_suggested_revision && (
                    <span
                      style={{
                        background: "#e0f2fe",
                        color: "#0369a1",
                        padding: "2px 6px",
                        borderRadius: 4,
                        fontWeight: 700,
                        fontSize: 11,
                      }}
                    >
                      ✨ AI Revision Ready
                    </span>
                  )}
                </div>
              )}

              {/* Detected issues if any */}
              {item.detected_issues && item.detected_issues.length > 0 && (
                <div style={{ margin: "6px 0 10px", padding: "6px 10px", background: "#f8fafc", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 12 }}>
                  <span style={{ color: "#b91c1c", fontWeight: 700 }}>Flagged Terms: </span>
                  {item.detected_issues.map((iss, i) => (
                    <span key={i} style={{ marginRight: 8, color: "#334155" }}>
                      &ldquo;<strong style={{ color: "#b91c1c" }}>{iss.term}</strong>&rdquo;
                      {iss.policy_ref && <span style={{ color: "#64748b" }}> ({iss.policy_ref})</span>}
                    </span>
                  ))}
                </div>
              )}

              <p
                lang={item.language ?? "en"}
                style={{
                  margin: "8px 0 0",
                  color: "#334155",
                  lineHeight: 1.55,
                  fontSize: "0.88rem",
                  fontFamily:
                    '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
                }}
              >
                {item.body_preview}…
              </p>

              <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
                <span style={{ color: "#0066cc", fontSize: 13, fontWeight: 700 }}>
                  Open Compliance Audit &amp; Decision Panel →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
